"""Shared data types for environment generation and validation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List


@dataclass
class ScenarioResult:
    """Single scenario validation result."""
    scenario_id: str
    passed: bool
    errors: list = field(default_factory=list)
    tool_traces: dict = field(default_factory=dict)
    complexity_level: str = "medium"
    execution_time: float = 0.0


@dataclass
class ValidationReport:
    """Validation report for all scenarios."""
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    scenario_results: list = field(default_factory=list)
    all_passed: bool = False

    def get_failed_scenarios(self) -> list:
        """Get list of failed scenario results."""
        return [r for r in self.scenario_results if not r.passed]

    def get_passed_scenarios(self) -> list:
        """Get list of passed scenario results."""
        return [r for r in self.scenario_results if r.passed]


@dataclass
class RevisionHistory:
    """Single revision history record."""
    revision_number: int
    failed_scenario_ids: list
    aggregated_errors: dict
    revised_code: str
    validation_report: Optional[ValidationReport] = None


class EnvGenState(Enum):
    """Environment generation workflow state enumeration."""
    IDLE = "idle"
    SCHEMA_DESIGN = "schema_design"
    TOOL_GEN = "tool_gen"
    SCENARIO_GEN = "scenario_gen"
    VALIDATE_SCENARIOS = "validate_scenarios"
    REVISE = "revise"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EnvGenResult:
    """Complete result of environment generation."""
    metadata_path: str
    class_name: str
    state: EnvGenState

    # Generation results
    schema: Optional[dict] = None
    tool_code: Optional[str] = None
    initial_tool_code: Optional[str] = None  # Code before validation/revision
    scenarios: Optional[list] = None

    # Validation results
    initial_validation: Optional[ValidationReport] = None
    final_validation: Optional[ValidationReport] = None

    # Revision history
    revision_history: list = field(default_factory=list)
    total_revisions: int = 0

    # Paths
    saved_paths: dict = field(default_factory=dict)

    # Success flag
    success: bool = False
    error_message: Optional[str] = None

    # Time statistics
    total_time: float = 0.0


@dataclass
class CheckpointData:
    """Unified checkpoint data structure for saving and resuming generation."""

    # Metadata
    metadata: dict
    schema: dict

    # Code history
    tool_code_history: List[dict] = field(default_factory=list)

    # Test scenarios
    scenarios: List[dict] = field(default_factory=list)

    # Validation results
    validation_results: dict = field(default_factory=dict)

    # Revision history
    revision_history: List[dict] = field(default_factory=list)

    # Statistics
    statistics: dict = field(default_factory=dict)

    # Saved paths
    saved_paths: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'metadata': self.metadata,
            'schema': self.schema,
            'tool_code_history': self.tool_code_history,
            'scenarios': self.scenarios,
            'validation_results': self.validation_results,
            'revision_history': self.revision_history,
            'statistics': self.statistics,
            'saved_paths': self.saved_paths
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CheckpointData':
        """Create CheckpointData from dictionary."""
        return cls(
            metadata=data.get('metadata', {}),
            schema=data.get('schema', {}),
            tool_code_history=data.get('tool_code_history', []),
            scenarios=data.get('scenarios', []),
            validation_results=data.get('validation_results', {}),
            revision_history=data.get('revision_history', []),
            statistics=data.get('statistics', {}),
            saved_paths=data.get('saved_paths', {})
        )

    @classmethod
    def from_env_gen_result(cls, result: 'EnvGenResult', schema: dict, checkpoint_version: str = "1.0") -> 'CheckpointData':
        """Create CheckpointData from EnvGenResult."""
        from datetime import datetime

        # Build metadata
        metadata = {
            'class_name': result.class_name,
            'metadata_path': result.metadata_path,
            'checkpoint_version': checkpoint_version,
            'last_updated': datetime.now().isoformat(),
            'state': result.state.value
        }

        # Build tool code history
        tool_code_history = []

        # Get initial code (before any revisions)
        # Try to get initial_code from EnvGenResult if available (from validation result)
        # Otherwise, use tool_code as fallback
        # Note: We need to store initial_code in EnvGenResult when loading from validation results
        initial_code = getattr(result, 'initial_tool_code', None) or result.tool_code

        if initial_code:
            tool_code_history.append({
                'version': 0,
                'code': initial_code,
                'timestamp': datetime.now().isoformat(),
                'revision_number': None
            })

        # Add revision code history
        # Only add revisions where code actually changed
        for rev in result.revision_history:
            # Check if this revision's code is different from the latest in history
            latest_code = tool_code_history[-1]['code'] if tool_code_history else None
            if latest_code is None or rev.revised_code != latest_code:
                tool_code_history.append({
                    'version': len(tool_code_history),
                    'code': rev.revised_code,
                    'timestamp': datetime.now().isoformat(),
                    'revision_number': rev.revision_number
                })
            else:
                # Code didn't change (e.g., scenario problem), update the revision_number reference
                # but don't add a new version entry
                if tool_code_history:
                    # Update the latest entry's revision_number to point to this revision
                    # This maintains the link between revision_history and tool_code_history
                    tool_code_history[-1]['revision_number'] = rev.revision_number

        # Build validation results
        validation_results = {}
        if result.initial_validation:
            validation_results['initial'] = cls._validation_report_to_dict(result.initial_validation)
        if result.final_validation:
            validation_results['final'] = cls._validation_report_to_dict(result.final_validation)

        # Build revision history
        revision_history = []
        for rev in result.revision_history:
            rev_dict = {
                'revision_number': rev.revision_number,
                'failed_scenario_ids': rev.failed_scenario_ids,
                'aggregated_errors': rev.aggregated_errors,
                'revised_code_version': rev.revision_number,  # Points to tool_code_history
            }
            if rev.validation_report:
                rev_dict['validation_report'] = cls._validation_report_to_dict(rev.validation_report)
            revision_history.append(rev_dict)

        # Build statistics
        statistics = {
            'total_revisions': result.total_revisions,
            'total_time': result.total_time,
            'success': result.success,
            'error_message': result.error_message
        }

        return cls(
            metadata=metadata,
            schema=schema,
            tool_code_history=tool_code_history,
            scenarios=result.scenarios or [],
            validation_results=validation_results,
            revision_history=revision_history,
            statistics=statistics,
            saved_paths=result.saved_paths
        )

    @staticmethod
    def _validation_report_to_dict(report: ValidationReport) -> dict:
        """Convert ValidationReport to dictionary."""
        return {
            'total_scenarios': report.total_scenarios,
            'passed_scenarios': report.passed_scenarios,
            'failed_scenarios': report.failed_scenarios,
            'all_passed': report.all_passed,
            'scenario_results': [
                {
                    'scenario_id': sr.scenario_id,
                    'passed': sr.passed,
                    'errors': sr.errors,
                    'tool_traces': sr.tool_traces,
                    'complexity_level': sr.complexity_level,
                    'execution_time': sr.execution_time
                }
                for sr in report.scenario_results
            ]
        }

    def to_env_gen_result(self) -> 'EnvGenResult':
        """Convert CheckpointData back to EnvGenResult for resuming."""
        # Get the latest tool code
        latest_code = None
        if self.tool_code_history:
            latest_code = self.tool_code_history[-1]['code']

        # Reconstruct ValidationReport objects
        initial_validation = None
        if 'initial' in self.validation_results:
            initial_validation = self._dict_to_validation_report(self.validation_results['initial'])

        final_validation = None
        if 'final' in self.validation_results:
            final_validation = self._dict_to_validation_report(self.validation_results['final'])

        # Reconstruct RevisionHistory objects
        revision_history = []
        for rev_dict in self.revision_history:
            validation_report = None
            if 'validation_report' in rev_dict:
                validation_report = self._dict_to_validation_report(rev_dict['validation_report'])

            # Get the revised code from tool_code_history
            revised_code_version = rev_dict.get('revised_code_version', rev_dict['revision_number'])
            revised_code = ''
            if revised_code_version < len(self.tool_code_history):
                revised_code = self.tool_code_history[revised_code_version]['code']

            revision_history.append(RevisionHistory(
                revision_number=rev_dict['revision_number'],
                failed_scenario_ids=rev_dict['failed_scenario_ids'],
                aggregated_errors=rev_dict['aggregated_errors'],
                revised_code=revised_code,
                validation_report=validation_report
            ))

        # Get state from metadata
        state = EnvGenState(self.metadata.get('state', 'idle'))

        return EnvGenResult(
            metadata_path=self.metadata['metadata_path'],
            class_name=self.metadata['class_name'],
            state=state,
            schema=self.schema,
            tool_code=latest_code,
            scenarios=self.scenarios,
            initial_validation=initial_validation,
            final_validation=final_validation,
            revision_history=revision_history,
            total_revisions=self.statistics.get('total_revisions', 0),
            saved_paths=self.saved_paths,
            success=self.statistics.get('success', False),
            error_message=self.statistics.get('error_message'),
            total_time=self.statistics.get('total_time', 0.0)
        )

    @staticmethod
    def _dict_to_validation_report(data: dict) -> ValidationReport:
        """Convert dictionary to ValidationReport."""
        scenario_results = [
            ScenarioResult(
                scenario_id=sr['scenario_id'],
                passed=sr['passed'],
                errors=sr.get('errors', []),
                tool_traces=sr.get('tool_traces', {}),
                complexity_level=sr.get('complexity_level', 'medium'),
                execution_time=sr.get('execution_time', 0.0)
            )
            for sr in data.get('scenario_results', [])
        ]

        return ValidationReport(
            total_scenarios=data['total_scenarios'],
            passed_scenarios=data['passed_scenarios'],
            failed_scenarios=data['failed_scenarios'],
            scenario_results=scenario_results,
            all_passed=data.get('all_passed', False)
        )
