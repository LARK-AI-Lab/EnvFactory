import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Callable
from uuid import uuid4
from pathlib import Path

from agents import Agent, Runner

from src.gen import Gen, GenConfig
from src.gen.env_gen.types import ScenarioResult, ValidationReport, RevisionHistory

from src.utils.logger import StructuredLogger
from src.gen.env_gen.prompts import (
    ScenarioValidator_System_Prompt,
    ScenarioValidator_User_Prompt,
    MCPToolReviser_System_Prompt,
    MCPToolReviser_Enhanced_User_Prompt
)
from src.gen.env_gen.mcp_tool_gen import extract_mcp_tools
from src.utils.agent_tools import execute_mcp_tool
from src.manager.mcp_client_manager import MCPClientManager


class ValidateReviseGen(Gen):
    """
    Unified validation and revision generator.

    Handles:
    - Parallel scenario validation
    - Error aggregation from multiple scenarios
    - Tool code revision based on aggregated errors
    """

    def __init__(
        self,
        client_manager: MCPClientManager,
        config: Optional[GenConfig] = None,
        logger: Optional[StructuredLogger] = None
    ):
        """
        Initialize validator.

        Args:
            client_manager: MCPClientManager instance
            config: Configuration object
            logger: Optional shared logger instance
        """
        super().__init__(config, logger=logger)
        self.client_manager = client_manager
        self.load_agents()

    def load_agents(self) -> None:
        """Load scenario validator and tool reviser agents."""
        from src.gen.env_gen import EnvGenConfig

        # Use tool_gen_model if specified for reviser, otherwise default
        if isinstance(self.config, EnvGenConfig) and self.config.tool_gen_model:
            reviser_model = self.get_model(self.config.tool_gen_model)
        else:
            reviser_model = self.model

        self.scenario_validator = Agent(
            name="ScenarioValidator",
            instructions=ScenarioValidator_System_Prompt,
            model=self.model,
            tools=[execute_mcp_tool]
        )

        self.tool_reviser = Agent(
            name="MCPToolReviser",
            instructions=MCPToolReviser_System_Prompt,
            model=reviser_model
        )

    async def validate_scenario(
        self,
        mcp_server_name: str,
        tool_code: str,
        tools_metadata: List[Dict],
        scenario: Dict[str, Any],
        conversation_id: str,
        turn_idx: int,
        request_id: str
    ) -> Tuple[ScenarioResult, int]:
        """
        Validate a single scenario.

        Args:
            mcp_server_name: Name of the MCP server
            tool_code: Full implementation code
            tools_metadata: List of tool metadata
            scenario: Single scenario dictionary
            conversation_id: Conversation ID for logging
            turn_idx: Current turn index
            request_id: Request ID for this validation

        Returns:
            Tuple of (ScenarioResult, next_turn_idx)
        """
        scenario_id = scenario['scenario_id']
        scenario_data = scenario['scenario_data']
        complexity_level = scenario.get('complexity_level', 'medium')
        expected_behavior = scenario.get('expected_behavior', 'pass')

        # Extract only Section 3 (MCP Tools) from tool_code
        tool_section = extract_mcp_tools(tool_code)

        user_prompt = ScenarioValidator_User_Prompt.format(
            mcp_server_name=mcp_server_name,
            scenario_id=scenario_id,
            complexity_level=complexity_level,
            expected_behavior=expected_behavior,
            scenario_data=json.dumps(scenario_data, indent=2, ensure_ascii=False),
            tool_code=tool_section,
            request_id=request_id
        )

        try:
            output = await Runner.run(
                self.scenario_validator,
                input=user_prompt,
                max_turns=self.config.max_turns
            )

            output_json = await self.log(
                conversation_id=conversation_id,
                idx=turn_idx,
                agent=self.scenario_validator,
                output=output
            )
            turn_idx += 1

            # Parse validation result
            if 'validation_result' in output_json:
                validation_data = output_json['validation_result']
            else:
                validation_data = output_json

            # Check if scenario passed
            passed = validation_data.get('passed', False)

            # Collect errors
            errors = []
            for error in validation_data.get('errors', []):
                errors.append({
                    'type': error.get('error_type', 'Unknown'),
                    'location': error.get('error_location', 'Unknown'),
                    'details': error.get('error_details', 'No details'),
                    'expected_vs_actual': error.get('expected_vs_actual', ''),
                    'root_cause': error.get('root_cause', ''),
                    'expected_error': error.get('expected_error', False)
                })

            # Collect tool traces
            tool_traces = {
                'load_scenario': validation_data.get('load_scenario_result', {}),
                'tool_execution': validation_data.get('tool_execution_results', []),
                'save_scenario': validation_data.get('save_scenario_result', {})
            }

            result = ScenarioResult(
                scenario_id=scenario_id,
                passed=passed,
                errors=errors,
                tool_traces=tool_traces,
                complexity_level=complexity_level,
                execution_time=0.0  # Could add timing here
            )

            return result, turn_idx

        except Exception as e:
            # Return failed result on exception
            error_result = ScenarioResult(
                scenario_id=scenario_id,
                passed=False,
                errors=[{
                    'type': 'Validation Error',
                    'location': 'validate_scenario',
                    'details': str(e),
                    'expected_vs_actual': '',
                    'root_cause': str(e)
                }],
                tool_traces={},
                complexity_level=complexity_level
            )
            return error_result, turn_idx

    async def validate_revise_loop(
        self,
        mcp_server_name: str,
        mcp_server_description: str,
        tool_code: str,
        tools_metadata: List[Dict],
        scenarios: List[Dict[str, Any]],
        conversation_id: str,
        start_turn_idx: int = 0,
        checkpoint_callback: Optional[Callable] = None
    ) -> Tuple[Dict[str, Any], int]:
        """
        Execute validation-revision loop until all scenarios pass or max revisions reached.

        Args:
            mcp_server_name: Name of the MCP server
            mcp_server_description: Description of the MCP server
            tool_code: Current implementation code
            tools_metadata: List of tool metadata
            scenarios: List of test scenarios
            conversation_id: Conversation ID for logging
            start_turn_idx: Starting turn index
            checkpoint_callback: Optional callback to save checkpoints after each revision

        Returns:
            Tuple of (validation_result_dict, next_turn_idx)
            validation_result_dict contains:
                - initial_validation: ValidationReport from first validation
                - final_validation: ValidationReport from last validation
                - revision_history: List of RevisionHistory
                - total_revisions: Total number of revisions performed
                - final_code: Final tool code after all revisions
                - success: Whether all scenarios passed
        """
        from src.gen.env_gen import EnvGenConfig

        turn_idx = start_turn_idx
        current_code = tool_code
        initial_code = tool_code
        revision_history: List[RevisionHistory] = []

        # Get max revisions from config
        if isinstance(self.config, EnvGenConfig):
            max_revisions = self.config.max_revisions
            max_concurrent = self.config.max_concurrent_scenarios
            quick_validate = self.config.quick_validate
        else:
            max_revisions = 3
            max_concurrent = 3
            quick_validate = False

        # Initial validation
        print(f"\n  [ValidateRevise] Initial validation of {len(scenarios)} scenarios...")
        initial_validation, turn_idx = await self._validate_all_scenarios(
            mcp_server_name=mcp_server_name,
            tool_code=current_code,
            tools_metadata=tools_metadata,
            scenarios=scenarios,
            conversation_id=conversation_id,
            turn_idx=turn_idx,
            max_concurrent=max_concurrent
        )

        print(f"    Initial: {initial_validation.passed_scenarios}/{initial_validation.total_scenarios} passed")

        # If all passed, no revision needed
        if initial_validation.all_passed:
            print(f"  [ValidateRevise] All scenarios passed! No revision needed.")
            return {
                'initial_validation': initial_validation,
                'final_validation': initial_validation,
                'revision_history': [],
                'total_revisions': 0,
                'final_code': current_code,
                'initial_code': initial_code,
                'success': True
            }, turn_idx

        current_validation = initial_validation

        # Revision loop
        for revision_num in range(1, max_revisions + 1):
            print(f"\n  [ValidateRevise] Revision {revision_num}/{max_revisions}")

            # Aggregate errors from failed scenarios
            failed_scenarios = current_validation.get_failed_scenarios()
            aggregated_errors = self._aggregate_errors(
                failed_scenarios,
                quick_mode=quick_validate
            )

            # Revise code
            revised_code, turn_idx = await self._revise_code(
                mcp_server_name=mcp_server_name,
                mcp_server_description=mcp_server_description,
                current_code=current_code,
                initial_code=initial_code,
                initial_validation=initial_validation,
                current_validation=current_validation,
                aggregated_errors=aggregated_errors,
                revision_num=revision_num,
                conversation_id=conversation_id,
                turn_idx=turn_idx
            )

            # Validate revised code
            print(f"  [ValidateRevise] Validating revised code...")
            new_validation, turn_idx = await self._validate_all_scenarios(
                mcp_server_name=mcp_server_name,
                tool_code=revised_code,
                tools_metadata=tools_metadata,
                scenarios=scenarios,
                conversation_id=conversation_id,
                turn_idx=turn_idx,
                max_concurrent=max_concurrent
            )

            print(f"    After revision {revision_num}: {new_validation.passed_scenarios}/{new_validation.total_scenarios} passed")

            # Record revision history
            revision_record = RevisionHistory(
                revision_number=revision_num,
                failed_scenario_ids=[r.scenario_id for r in failed_scenarios],
                aggregated_errors=aggregated_errors,
                revised_code=revised_code,
                validation_report=new_validation
            )
            revision_history.append(revision_record)

            # Update current state
            current_code = revised_code
            current_validation = new_validation

            # Call checkpoint callback if provided
            if checkpoint_callback:
                checkpoint_callback(
                    current_code=current_code,
                    initial_code=initial_code,
                    initial_validation=initial_validation,
                    current_validation=current_validation,
                    revision_history=revision_history,
                    total_revisions=revision_num
                )

            # Check if all scenarios passed
            if new_validation.all_passed:
                print(f"  [ValidateRevise] All scenarios passed after {revision_num} revision(s)!")
                return {
                    'initial_validation': initial_validation,
                    'final_validation': new_validation,
                    'revision_history': revision_history,
                    'total_revisions': revision_num,
                    'final_code': current_code,
                    'initial_code': initial_code,
                    'success': True
                }, turn_idx

            # Check if no improvement
            if new_validation.passed_scenarios <= current_validation.passed_scenarios and revision_num > 1:
                print(f"  [ValidateRevise] No improvement after revision {revision_num}, stopping.")
                break

        # Max revisions reached or no improvement
        print(f"  [ValidateRevise] Revisions stopped. Final: {current_validation.passed_scenarios}/{current_validation.total_scenarios} passed")

        return {
            'initial_validation': initial_validation,
            'final_validation': current_validation,
            'revision_history': revision_history,
            'total_revisions': len(revision_history),
            'final_code': current_code,
            'initial_code': initial_code,
            'success': current_validation.all_passed
        }, turn_idx

    async def _validate_all_scenarios(
        self,
        mcp_server_name: str,
        tool_code: str,
        tools_metadata: List[Dict],
        scenarios: List[Dict[str, Any]],
        conversation_id: str,
        turn_idx: int,
        max_concurrent: int = 3
    ) -> Tuple[ValidationReport, int]:
        """
        Validate all scenarios with concurrency control.

        Args:
            mcp_server_name: Name of the MCP server
            tool_code: Implementation code to validate
            tools_metadata: List of tool metadata
            scenarios: List of test scenarios
            conversation_id: Conversation ID for logging
            turn_idx: Current turn index
            max_concurrent: Maximum concurrent validations

        Returns:
            Tuple of (ValidationReport, next_turn_idx)
        """
        results: List[ScenarioResult] = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def validate_with_semaphore(scenario: Dict[str, Any]) -> ScenarioResult:
            async with semaphore:
                request_id = uuid4().hex[:8]
                result, _ = await self.validate_scenario(
                    mcp_server_name=mcp_server_name,
                    tool_code=tool_code,
                    tools_metadata=tools_metadata,
                    scenario=scenario,
                    conversation_id=conversation_id,
                    turn_idx=turn_idx,
                    request_id=request_id
                )
                return result

        # Run all validations in parallel with semaphore
        validation_tasks = [validate_with_semaphore(s) for s in scenarios]
        scenario_results = await asyncio.gather(*validation_tasks)
        results = list(scenario_results)

        # Build validation report
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        report = ValidationReport(
            total_scenarios=total,
            passed_scenarios=passed,
            failed_scenarios=failed,
            scenario_results=results,
            all_passed=(failed == 0)
        )

        return report, turn_idx + len(scenarios)

    def _aggregate_errors(
        self,
        failed_scenarios: List[ScenarioResult],
        quick_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Aggregate errors from all failed scenarios into a structured format.

        Args:
            failed_scenarios: List of failed scenario results
            quick_mode: If True, skip detailed categorization

        Returns:
            Structured error aggregation
        """
        if quick_mode:
            # Quick mode: just return basic info
            return {
                'total_failed': len(failed_scenarios),
                'scenario_ids': [r.scenario_id for r in failed_scenarios],
                'quick_mode': True
            }

        # Full error aggregation
        error_categories = {
            'critical': [],  # load_scenario failures
            'high': [],      # Multiple tool failures
            'medium': [],    # Single tool failure
            'low': []        # Minor issues
        }

        error_patterns = {}

        for scenario in failed_scenarios:
            for error in scenario.errors:
                # Categorize by severity
                if error['type'] in ['Load Scenario Error', 'Schema Validation Error']:
                    category = 'critical'
                elif 'multiple' in error['details'].lower():
                    category = 'high'
                elif 'single' in error['details'].lower():
                    category = 'medium'
                else:
                    category = 'low'

                error_info = {
                    'scenario_id': scenario.scenario_id,
                    'type': error['type'],
                    'location': error['location'],
                    'details': error['details'],
                    'root_cause': error.get('root_cause', ''),
                    'expected_error': error.get('expected_error', False)
                }
                error_categories[category].append(error_info)

                # Track error patterns
                pattern_key = f"{error['type']}:{error['location']}"
                if pattern_key not in error_patterns:
                    error_patterns[pattern_key] = {
                        'type': error['type'],
                        'location': error['location'],
                        'count': 0,
                        'scenario_ids': []
                    }
                error_patterns[pattern_key]['count'] += 1
                error_patterns[pattern_key]['scenario_ids'].append(scenario.scenario_id)

        return {
            'total_failed': len(failed_scenarios),
            'scenario_ids': [r.scenario_id for r in failed_scenarios],
            'error_categories': error_categories,
            'error_patterns': list(error_patterns.values()),
            'severity_summary': {
                'critical': len(error_categories['critical']),
                'high': len(error_categories['high']),
                'medium': len(error_categories['medium']),
                'low': len(error_categories['low'])
            }
        }

    async def _revise_code(
        self,
        mcp_server_name: str,
        mcp_server_description: str,
        current_code: str,
        initial_code: str,
        initial_validation: ValidationReport,
        current_validation: ValidationReport,
        aggregated_errors: Dict[str, Any],
        revision_num: int,
        conversation_id: str,
        turn_idx: int
    ) -> Tuple[str, int]:
        """
        Revise tool code based on validation errors.

        Args:
            mcp_server_name: Name of the MCP server
            mcp_server_description: Description of the MCP server
            current_code: Current implementation code
            initial_code: Original code before any revisions
            initial_validation: Validation report from first validation
            current_validation: Current validation report
            aggregated_errors: Structured error aggregation
            revision_num: Current revision number
            conversation_id: Conversation ID for logging
            turn_idx: Current turn index

        Returns:
            Tuple of (revised_code, next_turn_idx)
        """
        # Build user prompt
        user_prompt = MCPToolReviser_Enhanced_User_Prompt.format(
            mcp_server_name=mcp_server_name,
            mcp_server_description=mcp_server_description,
            tool_code=current_code,
            total_scenarios=current_validation.total_scenarios,
            failed_scenarios=current_validation.failed_scenarios,
            passed_scenarios=current_validation.passed_scenarios,
            aggregated_errors=json.dumps(aggregated_errors, indent=2, ensure_ascii=False)
        )

        output = await Runner.run(
            self.tool_reviser,
            input=user_prompt,
            max_turns=self.config.max_turns
        )

        output_json = await self.log(
            conversation_id=conversation_id,
            idx=turn_idx,
            agent=self.tool_reviser,
            output=output
        )
        turn_idx += 1

        # Check for scenario problem flag
        is_scenario_problem = False
        if 'revision_analysis' in output_json:
            is_scenario_problem = output_json['revision_analysis'].get('is_scenario_problem', False)
            if is_scenario_problem:
                print(f"    ⚠ Detected scenario problem, not code problem. Code unchanged.")
                problematic_ids = output_json['revision_analysis'].get('problematic_scenario_ids', [])
                if problematic_ids:
                    print(f"       Problematic scenarios: {', '.join(problematic_ids)}")

        # Extract revised code
        if 'tool_code' in output_json:
            revised_code = output_json['tool_code']
        else:
            # Try to parse from final_output directly
            revised_code = self._extract_code_from_output(output.final_output)

        if not revised_code:
            print(f"    ⚠ No code returned, keeping current code")
            revised_code = current_code

        return revised_code, turn_idx

    def _extract_code_from_output(self, final_output: str) -> Optional[str]:
        """
        Extract code from agent output when JSON parsing fails.

        Args:
            final_output: Raw agent output

        Returns:
            Extracted code or None
        """
        # Look for code between <tool_code> tags
        import re
        match = re.search(r'<tool_code>(.*?)</tool_code>', final_output, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Look for python code blocks
        match = re.search(r'```python(.*?)```', final_output, re.DOTALL)
        if match:
            return match.group(1).strip()

        return None
