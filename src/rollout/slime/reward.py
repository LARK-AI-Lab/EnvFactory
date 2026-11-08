"""Slime reward hooks for the EnvFactory tool-agent rollout and its BFCL v3 evaluation."""

from __future__ import annotations

import asyncio
import json
import logging
import statistics

from slime.rollout.filter_hub.dynamic_sampling_filters import check_reward_nonzero_std
from slime.utils.types import Sample

from src.eval.bfcl_v3.bfcl import BENCHMARK, grade as grade_bfcl
from src.rewards.tool_reward import compute_score

logger = logging.getLogger(__name__)

ZERO_REWARD = {"score": 0.0, "trace_score": 0.0, "state_score": 0.0, "penalty": 0.0}

# Rewards of every group the dynamic filter saw this rollout, kept or dropped; drained by log_rollout_metrics.
# Kept groups alone mix easy and hard prompts differently every rollout, so only these track the policy.
_candidate_rewards: list[dict] = []


def filter_reward_spread(args, samples: list[Sample], **kwargs):
    """slime's nonzero-reward-std group filter (``--dynamic-sampling-filter-path``), recording every group's rewards."""
    _candidate_rewards.extend(sample.reward for sample in samples)
    return check_reward_nonzero_std(args, samples, **kwargs)


async def reward(args, sample: Sample, **kwargs) -> dict:
    """Score a rollout (``--reward-key score``): EnvFactory trace + state reward, or BFCL task success."""
    if sample.status is Sample.Status.FAILED:
        return dict(ZERO_REWARD)
    tau = float(args.reward_tau)  # From --custom-config-path; a missing key must fail loudly.
    metadata = sample.metadata
    try:
        if metadata.get("benchmark") == BENCHMARK:
            return {"score": await asyncio.to_thread(grade_bfcl, metadata, sample.label)}
        return compute_score(
            solution_calls=metadata["tool_calls"],
            num_failed_calls=metadata["num_failed_tool_calls"],
            solution_state=metadata["rollout_state"],
            reference_calls=json.loads(sample.label),
            reference_state=metadata["final_state"],
            tau=tau,
        )
    except Exception as e:
        logger.warning(f"⚠️ Reward failed for sample {sample.index}: {type(e).__name__}: {e}")
        sample.remove_sample = True
        return dict(ZERO_REWARD)


def log_rollout_metrics(rollout_id, args, samples, rollout_extra_metrics, rollout_time) -> bool:
    """Log reward components and tool-use counters; returns False so slime's default logging still runs."""
    from slime.observability import logging_utils
    from slime.observability.metric_utils import compute_rollout_step

    valid = [sample for sample in samples if not sample.remove_sample]
    metrics = {"rollout/removed_fraction": 1 - len(valid) / len(samples) if samples else 0.0}
    if valid:
        for key in ZERO_REWARD:
            metrics[f"rollout/{key}"] = statistics.fmean(float(sample.reward[key]) for sample in valid)
        metrics["rollout/num_turns"] = statistics.fmean(sample.metadata["num_turns"] for sample in valid)
        metrics["rollout/num_tool_calls"] = statistics.fmean(len(sample.metadata["tool_calls"]) for sample in valid)
        metrics["rollout/num_failed_tool_calls"] = statistics.fmean(
            sample.metadata["num_failed_tool_calls"] for sample in valid
        )
    if _candidate_rewards:
        # The all-group score is slime's rollout/raw_reward_before_filters.
        for key in ("trace_score", "state_score", "penalty"):
            metrics[f"rollout/all_groups/{key}"] = statistics.fmean(float(r[key]) for r in _candidate_rewards)
        _candidate_rewards.clear()
    metrics["rollout/step"] = compute_rollout_step(args, rollout_id)
    # src/app/slime_training_viewer.py reads this record from training.log.
    logger.info("reward components %s: %s", rollout_id, metrics)
    logging_utils.log(args, metrics, step_key="rollout/step")
    return False
