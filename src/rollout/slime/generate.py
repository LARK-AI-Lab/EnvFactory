"""Multi-turn EnvFactory tool-agent rollout for slime.

Adapted from ToolAgent's slime rollout. The policy's own SGLang tokens are trainable;
tool observations are rendered with the chat template and appended as masked tokens.
Environments run in-process through ``src.tools.tool_manager`` (no MCP transport).
Rollout knobs come from ``configs/slime/envfactory.yaml`` (``--custom-config-path``).
BFCL v3 eval rows (``metadata.benchmark``) run on ``src.eval.bfcl_v3.bfcl.BfclEnv`` instead,
with scripted follow-up user turns.

Dataset row (``--input-key prompt --label-key label``)::

    {"prompt": [{"role": "system", ...}, {"role": "user", ...}],
     "label": "<JSON list of reference tool calls>",
     "metadata": {"envs": ["Calendar"], "initial_state": {"Calendar": {...}}, "final_state": {...}}}
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any

from slime.rollout.sglang_rollout import GenerateState
from slime.utils.http_utils import post
from slime.utils.types import Sample

from src.eval.bfcl_v3.bfcl import BENCHMARK, BfclEnv
from src.tools.tool_manager import get_tool_manager
from src.tools.tool_parser import extract_tool_calls

logger = logging.getLogger(__name__)


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


class EnvFactoryEnv:
    """The row's EnvFactory environments: a single user turn, evaluated under the training budgets."""

    per_call_budget = False  # The response budget spans the trajectory, as in verl.

    def __init__(self, args, tool_manager, metadata: dict):
        envs, self.initial_state = metadata["envs"], metadata["initial_state"]
        missing = [env for env in envs if env not in self.initial_state]
        if not envs or missing:
            raise ValueError(f"Row needs nonempty metadata.envs, each with an initial_state; missing {missing}.")
        self.args = args
        self.tool_manager = tool_manager
        self.tool_schemas = tool_manager.filter_tools(envs)
        self.allowed = {schema["function"]["name"] for schema in self.tool_schemas}
        self.max_steps = args.max_interaction_turns
        self.max_context_len = args.rollout_max_context_len
        self.max_response_len = args.rollout_max_response_len
        self.clients: dict[str, Any] = {}

    def call_tools(self, tool_calls: list) -> list[str]:
        """Execute one assistant turn's calls in order; each yields exactly one observation."""
        results = []
        for call in tool_calls:
            if call.name not in self.allowed:
                result = f"Unknown function '{call.name}'. Available tools: {sorted(self.allowed)}"
            else:
                env, _, tool = call.name.partition("-")
                if env not in self.clients:
                    self.clients[env] = self.tool_manager.create_client(env, self.initial_state[env])
                result = self.clients[env].call_tool(tool, call.arguments)
            results.append(_truncate(result, self.args.max_tool_response_length, self.args.truncate_side))
        return results

    def next_user_turn(self) -> list[dict] | None:
        return None

    def result(self) -> dict:
        # Only environments the policy touched have a rollout state, as with the verl agent loop.
        return {"rollout_state": {env: client.state() for env, client in self.clients.items()}}


def _make_env(args, tool_manager, metadata: dict):
    if metadata.get("benchmark") == BENCHMARK:
        return BfclEnv(args, metadata)
    return EnvFactoryEnv(args, tool_manager, metadata)


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
    return sample


async def generate(args, sample: Sample, sampling_params: dict, evaluation: bool = False) -> Sample:
    """Run one multi-turn tool-agent rollout and return the trainable sample."""
    assert not args.partial_rollout, "Partial rollout cannot resume a stateful tool environment."
    # Outside the try: a missing custom config must stop training, not fail every sample.
    tool_manager = get_tool_manager(args.environment_config_path)
    try:
        return await _generate(args, tool_manager, sample, sampling_params, evaluation)
    except Exception as e:
        logger.exception(f"⚠️ Tool-agent rollout failed for sample {sample.index}: {e}")
        return _mark_failed(sample, f"{type(e).__name__}: {e}")


async def _generate(args, tool_manager, sample: Sample, sampling_params: dict, evaluation: bool) -> Sample:
    # Slime hands every rollout its own deep copy of the row, so metadata may be used in place.
    metadata = sample.metadata
    env = await asyncio.to_thread(_make_env, args, tool_manager, metadata)
    messages = list(sample.prompt)

    state = GenerateState(args)
    tokenizer = state.tokenizer
    eos = tokenizer.eos_token
    template_kwargs = args.apply_chat_template_kwargs or {}
    max_context_len, max_response_len = env.max_context_len, env.max_response_len
    max_prompt_len = min(args.rollout_max_prompt_len or max_context_len, max_context_len - 1)

    # Pin the session to one engine so its growing prefix stays cached.
    sample.session_id = sample.session_id or str(uuid.uuid4())
    url = f"http://{args.sglang_router_ip}:{args.sglang_router_port}/generate"
    routed = getattr(args, "router_policy", None) == "consistent_hashing"  # Router args exist only with the router.
    headers = {"X-SMG-Routing-Key": sample.session_id} if routed else None

    prompt_text = await asyncio.to_thread(_render, tokenizer, messages, env.tool_schemas, True, template_kwargs)
    sample.tokens = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
    if len(sample.tokens) > max_prompt_len:
        return _mark_failed(sample, f"Prompt ({len(sample.tokens)} tokens) exceeds {max_prompt_len} tokens.")

    solution_calls: list[dict] = []
    num_failed_calls = 0
    num_turns = 0
    steps = 0  # Assistant responses since the current user turn began.

    while True:
        if state.aborted:
            sample.status = Sample.Status.ABORTED
            return sample

        remaining_context = max_context_len - len(sample.tokens)
        remaining_response = max_response_len - (0 if env.per_call_budget else sample.effective_response_length)
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
        steps += 1

        content = gen_text.removesuffix(eos)
        tool_calls = extract_tool_calls(content)
        messages.append({"role": "assistant", "content": content})
        # Calls of a truncated or step-capped turn count for the reward but are never executed.
        solution_calls.extend({"name": call.name, "arguments": call.arguments} for call in tool_calls if call.error is None)
        num_failed_calls += sum(call.error is not None for call in tool_calls)

        if meta_info["finish_reason"]["type"] == "length" or (tool_calls and steps == env.max_steps):
            sample.status = Sample.Status.TRUNCATED
            break
        if tool_calls:
            tool_start = time.perf_counter()
            executed = iter(await asyncio.to_thread(env.call_tools, [call for call in tool_calls if call.error is None]))
            sample.non_generation_time += time.perf_counter() - tool_start
            new_messages = [{"role": "tool", "content": call.error or next(executed)} for call in tool_calls]
        else:
            new_messages = env.next_user_turn()
            if new_messages is None:
                sample.status = Sample.Status.COMPLETED
                break
            steps = 0

        text = await asyncio.to_thread(_render_observation, tokenizer, messages, new_messages, env.tool_schemas, eos, template_kwargs)
        messages.extend(new_messages)
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

    metadata.update(env.result())
    metadata["tool_calls"] = solution_calls
    metadata["num_failed_tool_calls"] = num_failed_calls
    metadata["num_turns"] = num_turns
    return sample
