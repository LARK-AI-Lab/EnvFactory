import ast
import importlib.util
import sys
import unittest
from pathlib import Path


TYPES_PATH = (
    Path(__file__).resolve().parents[1] / "src" / "gen" / "env_gen" / "types.py"
)
ENV_GEN_PATH = TYPES_PATH.with_name("env_gen.py")
SPEC = importlib.util.spec_from_file_location("env_gen_types_for_test", TYPES_PATH)
types = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = types
SPEC.loader.exec_module(types)


class CheckpointFinalizationTest(unittest.TestCase):
    def make_result(self, *, success, all_passed):
        final_validation = types.ValidationReport(
            total_scenarios=2,
            passed_scenarios=2 if all_passed else 1,
            failed_scenarios=0 if all_passed else 1,
            all_passed=all_passed,
            scenario_results=[],
        )
        return types.EnvGenResult(
            metadata_path="envs/metadata/Test_metadata.json",
            class_name="Test",
            state=types.EnvGenState.VALIDATE_SCENARIOS,
            final_validation=final_validation,
            success=success,
        )

    def test_successful_result_serializes_as_completed(self):
        result = self.make_result(success=True, all_passed=True)

        result.finalize_validation(total_time=12.5)
        checkpoint = types.CheckpointData.from_env_gen_result(result, schema={})

        self.assertEqual(checkpoint.metadata["state"], "completed")
        self.assertTrue(checkpoint.statistics["success"])
        self.assertEqual(checkpoint.statistics["total_time"], 12.5)

    def test_failed_validation_cannot_keep_stale_success(self):
        result = self.make_result(success=True, all_passed=False)

        result.finalize_validation(total_time=8.0)
        checkpoint = types.CheckpointData.from_env_gen_result(result, schema={})

        self.assertEqual(checkpoint.metadata["state"], "failed")
        self.assertFalse(checkpoint.statistics["success"])


class FinalCheckpointOrderingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(ENV_GEN_PATH.read_text(encoding="utf-8"))

    def assert_finalized_before_final_save(self, function_name):
        function = next(
            node
            for node in ast.walk(self.tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == function_name
        )
        finalize_lines = [
            node.lineno
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "finalize_validation"
        ]
        checkpoint_lines = [
            node.lineno
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "save_checkpoint"
        ]

        self.assertTrue(finalize_lines)
        self.assertLess(max(finalize_lines), max(checkpoint_lines))

    def test_generation_finalizes_before_final_checkpoint(self):
        self.assert_finalized_before_final_save("generate_mcp_env")

    def test_resume_finalizes_before_final_checkpoint(self):
        self.assert_finalized_before_final_save("_resume_from_validation_internal")


if __name__ == "__main__":
    unittest.main()
