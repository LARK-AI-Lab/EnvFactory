"""Multi-turn EnvFactory tool-agent rollout for slime.

Adapted from ToolAgent's slime rollout. The policy's own SGLang tokens are trainable;
tool observations are rendered with the chat template and appended as masked tokens.
Environments run in-process through ``src.tools.tool_manager`` (no MCP transport).

Dataset row (``--input-key prompt --label-key label --metadata-key metadata``)::

    {"prompt": [{"role": "system", ...}, {"role": "user", ...}],
     "label": "<JSON list of reference tool calls>",
     "metadata": {"envs": ["Calendar"], "initial_state": {"Calendar": {...}}, "final_state": {...}}}
"""

from __future__ import annotations

import asyncio
import copy
import functools
import json
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from slime.rollout.sglang_rollout import GenerateState
from slime.utils.http_utils import post
from slime.utils.types import Sample

from src.tools.tool_manager import get_tool_manager
from src.tools.tool_parser import get_tool_parser

logger = logging.getLogger(__name__)

# Overridable through the slime custom config (--custom-config-path).
DEFAULTS = {
    "environment_config_path": "configs/mcp_server.json",
    "tool_format": "qwen3",
    "max_interaction_turns": 10,
    "max_tool_response_length": 512,  # Characters; 0 keeps observations whole.
    "truncate_side": "middle",  # left | right | middle
    "tool_max_workers": 64,
}

_EXECUTOR: ThreadPoolExecutor | None = None


def _cfg(args, name: str) -> Any:
    value = getattr(args, name, None)
    return DEFAULTS[name] if value is None else value


async def _offload(args, fn, *fn_args):
    """Run blocking work (chat templates, tool calls) off the rollout event loop."""
    global _EXECUTOR
    if _EXECUTOR is None:
        _EXECUTOR = ThreadPoolExecutor(int(_cfg(args, "tool_max_workers")), thread_name_prefix="envfactory-tools")
    return await asyncio.get_running_loop().run_in_executor(_EXECUTOR, functools.partial(fn, *fn_args))


def _truncate(text: str, max_length: int, side: str) -> str:
    if max_length <= 0 or len(text) <= max_length:
        return text
    if side == "left":
        return "(truncated)..." + text[-max_length:]
    if side == "right":
        return text[:max_length] + "...(truncated)"
    left, right = (max_length + 1) // 2, max_length // 2
    return text[:left] + "...(truncated)..." + (text[-right:] if right else "")


def _render(tokenizer, messages: list[dict], tools: list[dict], add_generation_prompt: bool, template_kwargs: dict) -> str:
    return tokenizer.apply_chat_template(
        messages, tools=tools or None, tokenize=False, add_generation_prompt=add_generation_prompt, **template_kwargs
    )


def _render_observation(
    tokenizer, messages: list[dict], new_messages: list[dict], tools: list[dict], eos: str, template_kwargs: dict
) -> str:
    """Text the chat template places after the last assistant turn's EOS for ``new_messages``.

    The cut is located by EOS count, not by prefix equality: templates may render the
    final assistant turn differently once it is no longer last (Qwen3 drops its empty
    ``<think>`` block), but every message still closes with one EOS.
    """
    before = _render(tokenizer, messages, tools, False, template_kwargs)
    after = _render(tokenizer, messages + new_messages, tools, True, template_kwargs)
    cut = -len(eos)
    for _ in range(before.count(eos)):
        cut = after.find(eos, cut + len(eos))
        if cut < 0:
            raise ValueError(f"Rendered history lost an EOS token {eos!r} after appending observations.")
    if cut < 0:
        raise ValueError(f"Rendered history contains no EOS token {eos!r}.")
    return after[cut + len(eos):]


def call_tools(tool_manager, tool_calls: list, allowed: set[str], clients: dict, initial_state: dict) -> list[str]:
    """Execute one assistant turn's calls in order; each yields exactly one observation."""
    results = []
    for call in tool_calls:
        if call.error is not None:
            results.append(call.error)
        elif call.name not in allowed:
            results.append(f"Unknown function '{call.name}'. Available tools: {sorted(allowed)}")
        else:
            env, _, tool = call.name.partition("-")
            if env not in clients:
                clients[env] = tool_manager.create_client(env, initial_state[env])
            results.append(clients[env].call_tool(tool, call.arguments))
    return results


def _mark_failed(sample: Sample, reason: str) -> Sample:
    """Exclude an infrastructure failure from training while keeping slime's tensor fields aligned."""
    logger.warning(f"⚠️ Sample {sample.index} failed: {reason}")
    sample.status = Sample.Status.FAILED
    sample.remove_sample = True
    if sample.response_length == 0:
        # A zero-length response breaks the length bookkeeping; emit a masked placeholder.
        sample.tokens = [0, 0]
        sample.response = ""
        sample.response_length = 1
    sample.loss_mask = [0] * sample.response_length
    sample.rollout_log_probs = [0.0] * sample.response_length
    # Slime validates top-p replay on every row, including masked placeholders.
    sample.rollout_top_p_token_ids = []
    sample.rollout_top_p_token_offsets = [0] * (sample.response_length + 1)
    sample.metadata["failure_reason"] = reason
    return sample


async def generate(args, sample: Sample, sampling_params: dict, evaluation: bool = False) -> Sample:
    """Run one multi-turn tool-agent rollout and return the trainable sample."""
    assert not args.partial_rollout, "Partial rollout cannot resume a stateful tool environment."
    assert not getattr(args, "use_rollout_routing_replay", False), (
        "Rollout routing replay cannot stitch routed experts across tool turns."
    )
    if isinstance(sample.metadata, str):
        sample.metadata = json.loads(sample.metadata)
    try:
        return await _generate(args, sample, sampling_params, evaluation)
    except Exception as e:
        logger.exception(f"⚠️ Tool-agent rollout failed for sample {sample.index}: {e}")
        return _mark_failed(sample, f"{type(e).__name__}: {e}")


async def _generate(args, sample: Sample, sampling_params: dict, evaluation: bool) -> Sample:
    # Slime may retry an aborted sample; start from a clean response.
    sample.tokens = []
    sample.response = ""
    sample.response_length = 0
    sample.loss_mask = []
    sample.rollout_log_probs = None
    sample.rollout_top_p_token_ids = None
    sample.rollout_top_p_token_offsets = None
    sample.status = Sample.Status.PENDING
    sample.remove_sample = False
    sample.reward = None

    metadata = sample.metadata
    envs = metadata["envs"]
    initial_state = copy.deepcopy(metadata["initial_state"])
    missing = [env for env in envs if env not in initial_state]
    if not envs or missing:
        raise ValueError(f"Row needs nonempty metadata.envs, each with an initial_state; missing {missing}.")
    messages = copy.deepcopy(json.loads(sample.prompt) if isinstance(sample.prompt, str) else sample.prompt)

    tool_manager = get_tool_manager(_cfg(args, "environment_config_path"))
    tool_schemas = await _offload(args, tool_manager.filter_tools, envs)
    allowed = {schema["function"]["name"] for schema in tool_schemas}
    tool_parser = get_tool_parser(_cfg(args, "tool_format"))
    max_turns = int(_cfg(args, "max_interaction_turns"))
    max_tool_response_length = int(_cfg(args, "max_tool_response_length"))
    truncate_side = _cfg(args, "truncate_side")

    state = GenerateState(args)
    tokenizer = state.tokenizer
    eos = tokenizer.eos_token
    template_kwargs = getattr(args, "apply_chat_template_kwargs", None) or {}

    max_context_len = int(
        (evaluation and getattr(args, "eval_max_context_len", None))
        or args.rollout_max_context_len
        or args.context_parallel_size * args.max_tokens_per_gpu
    )
    max_response_len = int(
        (evaluation and getattr(args, "eval_max_response_len", None)) or args.rollout_max_response_len or max_context_len
    )

    # Pin the session to one engine so its growing prefix stays cached.
    sample.session_id = sample.session_id or str(uuid.uuid4())
    url = f"http://{args.sglang_router_ip}:{args.sglang_router_port}/generate"
    headers = {"X-SMG-Routing-Key": sample.session_id} if getattr(args, "router_policy", None) == "consistent_hashing" else None

    prompt_text = await _offload(args, _render, tokenizer, messages, tool_schemas, True, template_kwargs)
    sample.tokens = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
    if len(sample.tokens) >= max_context_len:
        return _mark_failed(sample, f"Prompt ({len(sample.tokens)} tokens) exceeds the context budget ({max_context_len}).")

    clients: dict[str, Any] = {}
    solution_calls: list[dict] = []
    num_failed_calls = 0
    num_turns = 0

    for turn in range(max_turns):
        if state.aborted:
            sample.status = Sample.Status.ABORTED
            return sample

        remaining_context = max_context_len - len(sample.tokens)
        remaining_response = max_response_len - sample.effective_response_length
        if remaining_context <= 0 or remaining_response <= 0:
            sample.status = Sample.Status.TRUNCATED
            break

        turn_sampling_params = {
            **sampling_params,
            "max_new_tokens": min(sampling_params.get("max_new_tokens") or max_response_len, remaining_response, remaining_context),
        }
        output = await post(
            url,
            {"input_ids": sample.tokens, "sampling_params": turn_sampling_params, "return_logprob": True},
            headers=headers,
        )
        meta_info = output["meta_info"]
        if meta_info["finish_reason"]["type"] == "abort":
            if state.aborted:
                sample.status = Sample.Status.ABORTED
                return sample
            return _mark_failed(sample, "SGLang aborted the request.")
        if "output_token_logprobs" not in meta_info:
            return _mark_failed(sample, "SGLang omitted output_token_logprobs; the response cannot be trained.")

        # Train on the engine's own token ids, never on re-tokenized text.
        gen_ids = [item[1] for item in meta_info["output_token_logprobs"]]
        gen_log_probs = [item[0] for item in meta_info["output_token_logprobs"]]
        gen_text = output["text"]
        sample.append_response_tokens(
            args, tokens=gen_ids, log_probs=gen_log_probs, trainable=True, meta_info=meta_info, text=gen_text
        )
        num_turns += 1

        if meta_info["finish_reason"]["type"] == "length":
            sample.status = Sample.Status.TRUNCATED
            break

        content = gen_text.removesuffix(eos)
        tool_calls = tool_parser.extract_tool_calls(content, tool_schemas)
        messages.append({"role": "assistant", "content": content})
        solution_calls.extend({"name": call.name, "arguments": call.arguments} for call in tool_calls if call.error is None)
        num_failed_calls += sum(call.error is not None for call in tool_calls)

        if not tool_calls:
            sample.status = Sample.Status.COMPLETED
            break
        if turn == max_turns - 1:
            # The final turn's calls are recorded for the reward but never executed.
            sample.status = Sample.Status.TRUNCATED
            break

        tool_start = time.perf_counter()
        results = await _offload(args, call_tools, tool_manager, tool_calls, allowed, clients, initial_state)
        sample.non_generation_time += time.perf_counter() - tool_start

        tool_messages = [
            {"role": "tool", "content": _truncate(result, max_tool_response_length, truncate_side)} for result in results
        ]
        text = await _offload(args, _render_observation, tokenizer, messages, tool_messages, tool_schemas, eos, template_kwargs)
        messages.extend(tool_messages)
        ids = tokenizer(text, add_special_tokens=False)["input_ids"]
        overflow = len(sample.tokens) + len(ids) - max_context_len
        if overflow > 0:
            ids = ids[: len(ids) - overflow]
            text = tokenizer.decode(ids)
        if ids:
            sample.append_response_tokens(args, tokens=ids, trainable=False, text=text)
        if overflow > 0:
            sample.status = Sample.Status.TRUNCATED
            break

    if sample.response_length == 0:
        return _mark_failed(sample, "The rollout produced no response tokens.")
    if sample.status is Sample.Status.PENDING:
        sample.status = Sample.Status.COMPLETED

    # Only environments the policy touched have a rollout state, as with the verl agent loop.
    metadata["rollout_state"] = {env: client.state() for env, client in clients.items()}
    metadata["tool_calls"] = solution_calls
    metadata["num_failed_tool_calls"] = num_failed_calls
    metadata["num_turns"] = num_turns
    return sample
