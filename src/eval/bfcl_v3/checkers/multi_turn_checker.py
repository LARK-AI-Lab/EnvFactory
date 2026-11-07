"""BFCL multi-turn checker with isolated per-grading registries."""

from __future__ import annotations

from src.eval.bfcl_v3.checkers.multi_turn_utils import (
    execute_multi_turn_func_call,
    is_empty_execute_response,
)


def multi_turn_checker(
    multi_turn_model_result_list_decoded: list[list[list[str]]],
    multi_turn_ground_truth_list: list[list[str]],
    test_entry: dict,
    test_category: str,
    model_name: str,
) -> dict:
    initial_config = test_entry["initial_config"]
    involved_classes = test_entry["involved_classes"]
    test_entry_id = test_entry["id"]
    assert test_category == test_entry_id.rsplit("_", 1)[0], (
        f"test_category {test_category!r} does not match the category derived from entry id {test_entry_id!r}"
    )
    execution_results = []
    all_turn_model_execution_results = []
    model_registry = {}
    ground_truth_registry = {}

    for turn_index, single_turn_ground_truth_list in enumerate(multi_turn_ground_truth_list):
        single_turn_model_response_list = multi_turn_model_result_list_decoded[turn_index]
        single_turn_model_execution_results = []
        single_turn_model_execution_results_uncombined = []
        model_instances = {}

        for single_step_model_response in single_turn_model_response_list:
            single_step_model_execution_results, model_instances = execute_multi_turn_func_call(
                func_call_list=single_step_model_response,
                initial_config=initial_config,
                involved_classes=involved_classes,
                registry=model_registry,
                long_context=("long_context" in test_category or "composite" in test_category),
            )
            single_turn_model_execution_results.extend(single_step_model_execution_results)
            single_turn_model_execution_results_uncombined.append(single_step_model_execution_results)

        single_turn_ground_truth_execution_results, ground_truth_instances = execute_multi_turn_func_call(
            func_call_list=single_turn_ground_truth_list,
            initial_config=initial_config,
            involved_classes=involved_classes,
            registry=ground_truth_registry,
            long_context=("long_context" in test_category or "composite" in test_category),
        )

        all_turn_model_execution_results.extend(single_turn_model_execution_results)
        execution_results.append({
            "model": single_turn_model_execution_results_uncombined,
            "ground_truth": single_turn_ground_truth_execution_results,
        })

        if single_turn_ground_truth_list and (not single_turn_model_response_list or is_empty_execute_response(single_turn_model_response_list)):
            return {
                "valid": False,
                "error_message": f"Model response list is empty for turn {turn_index}",
                "error_type": "multi_turn:empty_turn_model_response",
                "details": {"execution_result": execution_results},
            }

        if not single_turn_ground_truth_list:
            continue

        assert len(model_instances) == len(ground_truth_instances), \
            f"Model instances and ground truth instances do not match in length for turn {turn_index}."
        assert set(model_instances.keys()) == set(ground_truth_instances.keys())

        state_check_result = state_checker(model_instances, ground_truth_instances)
        if not state_check_result["valid"]:
            state_check_result["execution_result"] = execution_results
            return state_check_result

        response_check_result = response_checker(all_turn_model_execution_results, single_turn_ground_truth_execution_results, turn_index)
        if not response_check_result["valid"]:
            return response_check_result

    return {"valid": True}


def state_checker(model_instances: dict, ground_truth_instances: dict):
    for class_name, ground_truth_instance in ground_truth_instances.items():
        valid, differences = _compare_instances(model_instances[class_name], ground_truth_instance)
        if not valid:
            return {
                "valid": False,
                "error_message": f"Model instance for {class_name} does not match the state with ground truth instance.",
                "error_type": "multi_turn:instance_state_mismatch",
                "details": {
                    "differences": differences,
                    "model_instance_state": {k: v for k, v in vars(model_instances[class_name]).items() if not k.startswith("_")},
                    "ground_truth_instance_state": {k: v for k, v in vars(ground_truth_instance).items() if not k.startswith("_")},
                },
            }
    return {"valid": True}


def response_checker(model_response_list: list, ground_truth_response_list: list, turn_index: int):
    is_subsequence, missing_items = _is_subsequence_unordered(ground_truth_response_list, model_response_list)
    if not is_subsequence:
        return {
            "valid": False,
            "error_message": f"Model response execution results so far does not contain all the ground truth response execution results for turn {turn_index}.",
            "error_type": "multi_turn:execution_response_mismatch",
            "details": {
                "missing_items": missing_items,
                "model_response (including all previous turns)": model_response_list,
                "ground_truth_response (only the current turn)": ground_truth_response_list,
            },
        }
    return {"valid": True}


def _compare_instances(model_object, ground_truth_object):
    assert type(model_object) == type(ground_truth_object), "Objects are not of the same type."
    differences = {}
    for attr_name in vars(ground_truth_object):
        if attr_name.startswith("_"):
            continue
        model_attr = getattr(model_object, attr_name)
        ground_truth_attr = getattr(ground_truth_object, attr_name)
        if model_attr != ground_truth_attr:
            differences[attr_name] = {"model": model_attr, "ground_truth": ground_truth_attr}
    return not differences, differences


def _is_subsequence_unordered(list1, list2) -> tuple[bool, list]:
    list2_copy = list2[:]
    missing = []
    for item in list1:
        try:
            list2_copy.remove(item)
        except ValueError:
            missing.append(item)
    return not missing, missing
