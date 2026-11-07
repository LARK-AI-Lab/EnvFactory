"""EnvFactory trajectory reward: tool-call trace plus final environment state."""

from __future__ import annotations

import math


def _values_match(solution, reference) -> bool:
    """Exact equality, with numeric tolerance so 1 matches 1.0."""
    if solution == reference:
        return True
    if isinstance(solution, (int, float)) and isinstance(reference, (int, float)):
        return math.isclose(solution, reference, rel_tol=1e-6)
    return False


def _call_matches(solution: dict, reference: dict) -> bool:
    """Same tool, and every unmasked reference argument present with an equal value."""
    if solution.get("name") != reference.get("name"):
        return False
    solution_args = solution.get("arguments") or {}
    masked = set(reference.get("masked_arguments") or [])
    for key, value in (reference.get("arguments") or {}).items():
        if key in masked:
            continue
        if key not in solution_args or not _values_match(solution_args[key], value):
            return False
    return True


def trace_score(solution: list[dict], reference: list[dict]) -> float:
    """1.0 when every reference call is matched by a distinct solution call, in any order."""
    if not solution:
        return 0.0
    if not reference:
        return 1.0
    matched = set()
    for ref_call in reference:
        index = next(
            (i for i, call in enumerate(solution) if i not in matched and _call_matches(call, ref_call)),
            None,
        )
        if index is None:
            return 0.0
        matched.add(index)
    return 1.0


def state_score(solution: dict, reference: dict, servers: set[str]) -> float:
    """Fraction of the reference-touched environments whose final state matches exactly."""
    reference = {server: state for server, state in reference.items() if server in servers}
    if not reference:
        return 0.0
    return sum(solution.get(server) == state for server, state in reference.items()) / len(reference)


def length_penalty(solution: list[dict], reference: list[dict]) -> float:
    """0.05 per surplus call, capped at 0.5."""
    if not solution or not reference:
        return 0.0
    return min(max(len(solution) - len(reference), 0) * 0.05, 0.5)


def format_penalty(num_failed_calls: int) -> float:
    """0.05 per unparseable call, capped at 0.5."""
    return min(num_failed_calls * 0.05, 0.5)


def compute_score(
    solution_calls: list[dict],
    num_failed_calls: int,
    solution_state: dict,
    reference_calls: list[dict],
    reference_state: dict,
    tau: float,
) -> dict:
    """``max(0, tau * trace + (1 - tau) * state - penalties)`` with its components."""
    servers = {call["name"].split("-", 1)[0] for call in reference_calls}
    trace = trace_score(solution_calls, reference_calls)
    state = state_score(solution_state, reference_state, servers)
    penalty = length_penalty(solution_calls, reference_calls) + format_penalty(num_failed_calls)
    return {
        "score": max(0.0, tau * trace + (1 - tau) * state - penalty),
        "trace_score": trace,
        "state_score": state,
        "penalty": penalty,
    }
