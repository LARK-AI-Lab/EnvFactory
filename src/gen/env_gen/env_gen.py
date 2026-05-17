import asyncio
import argparse
import sys
import json
import time
import glob
from pathlib import Path
from typing import List, Optional
import os
os.environ['SKIP_MCP_AUTO_INIT'] = 'True'
os.environ['OPENAI_AGENTS_DISABLE_TRACING'] = 'true'
from dotenv import load_dotenv
load_dotenv()
from src.gen import Gen
from src.gen.env_gen import EnvGenConfig
from src.gen.mcp_schema_gen import SchemaGen
from src.gen.env_gen.mcp_tool_gen import MCPToolGen, ScenarioGen
from src.gen.env_gen.validate_revise import ValidateReviseGen
from src.gen.env_gen.types import (
    EnvGenState,
    EnvGenResult,
    CheckpointData
)
from src.manager.mcp_client_manager import MCPClientManager
from src.utils.utils import load_metadata, update_mcp_server_config


def normalize_path(path) -> str:
    """
    Normalize path to use forward slashes (/) instead of backslashes (\\).

    Args:
        path: Path object or string

    Returns:
        String with forward slashes
    """
    if isinstance(path, Path):
        return path.as_posix()
    return str(path).replace('\\', '/')


class EnvGen(Gen):
    """
    Main environment generator orchestrating the complete workflow.
    """

    def __init__(self, config: Optional[EnvGenConfig] = None):
        """
        Initialize EnvGen.

        Args:
            config: Configuration object
        """
        if config is None:
            config = EnvGenConfig()
        # Validate that config is EnvGenConfig
        if not isinstance(config, EnvGenConfig):
            raise TypeError(f"EnvGen requires EnvGenConfig, got {type(config).__name__}")

        super().__init__(config)
        self.config: EnvGenConfig = config  # Type hint for IDE
        self.load_agents()

        # Initialize sub-generators with shared logger instance
        # This ensures all logs are collected in the same logger instance
        self.schema_gen = SchemaGen(config=self.config, logger=self.logger)
        self.tool_gen = MCPToolGen(config=self.config, logger=self.logger)
        self.scenario_gen = ScenarioGen(config=self.config, logger=self.logger)
        # client_manager will be created per metadata file

    def load_agents(self) -> None:
        """No agents needed at this level - sub-generators handle their own."""
        pass

    async def generate_mcp_env(
        self,
        metadata_path: str,
        conversation_id: Optional[str] = None
    ) -> EnvGenResult:
        """
        Generate complete MCP environment for a single metadata file.

        Workflow:
        1. Load metadata
        2. Generate tool code
        3. Generate test scenarios
        4. Register tool server
        5. Execute validation-revision loop
        6. Save final results

        Args:
            metadata_path: Path to metadata JSON file
            conversation_id: Conversation ID for logging

        Returns:
            EnvGenResult with complete generation information
        """
        start_time = time.time()
        metadata_path_obj = Path(metadata_path)

        if conversation_id is None:
            conversation_id = f"env_gen_{metadata_path_obj.stem}"

        print(f"\n{'='*60}")
        print(f"Starting environment generation: {metadata_path}")
        print(f"{'='*60}")

        result = EnvGenResult(
            metadata_path=str(metadata_path),
            class_name="",
            state=EnvGenState.IDLE
        )

        # Initialize turn_idx counter for unified logging
        turn_idx = 0

        try:
            # Step 1: Load metadata
            print(f"\n[Step 1/5] Loading metadata...")
            result.state = EnvGenState.SCHEMA_DESIGN
            metadata_info = load_metadata(metadata_path)
            result.class_name = metadata_info['class_name']
            result.schema = metadata_info

            print(f"  Class: {metadata_info['class_name']}")
            print(f"  Tools: {len(metadata_info['tools'])}")

            # Step 2: Generate tool code
            print(f"\n[Step 2/5] Generating tool implementation...")
            result.state = EnvGenState.TOOL_GEN
            tool_result, turn_idx = await self.tool_gen.gen(
                mcp_server_name=metadata_info['class_name'],
                mcp_server_description=metadata_info['description'],
                tools=metadata_info['tools'],
                conversation_id=conversation_id,
                start_turn_idx=turn_idx
            )
            result.tool_code = tool_result['tool_code']

            # Save tool code
            tool_path = self.tool_gen.save_tools(
                mcp_server_name=metadata_info['class_name'],
                tool_code=result.tool_code
            )
            result.saved_paths['tool_path'] = normalize_path(tool_path)

            print(f"  Tool saved to: {normalize_path(tool_path)}")

            # Save checkpoint after tool generation
            if self.config.save_intermediate:
                checkpoint_path = self.save_checkpoint(result, metadata_info)
                if checkpoint_path:
                    print(f"  Checkpoint saved to: {checkpoint_path}")

            # Step 3: Generate test scenarios
            print(f"\n[Step 3/5] Generating test scenarios...")
            result.state = EnvGenState.SCENARIO_GEN
            scenarios, turn_idx = await self.scenario_gen.generate_scenarios(
                mcp_server_name=metadata_info['class_name'],
                tool_code=result.tool_code,
                n_scenarios=self.config.n_scenarios,
                conversation_id=conversation_id,
                start_turn_idx=turn_idx
            )
            result.scenarios = scenarios

            print(f"  Generated {len(scenarios)} scenarios:")
            for s in scenarios:
                print(f"    - {s['scenario_id']} ({s['complexity_level']})")

            # Save checkpoint after scenario generation
            if self.config.save_intermediate:
                checkpoint_path = self.save_checkpoint(result, metadata_info)
                if checkpoint_path:
                    print(f"  Checkpoint saved to: {checkpoint_path}")

            # Step 4: Register tool server
            print(f"\n[Step 4/5] Registering tool server...")
            update_mcp_server_config(
                config_path="configs/mcp_server.json",
                mcp_server_name=metadata_info['class_name'],
                tool_path=normalize_path(tool_path),
                is_stateless=False
            )

            client_manager = MCPClientManager()
            try:
                client_manager.register_MCP_server(
                    server_name=metadata_info['class_name'],
                    tool_path=normalize_path(tool_path),
                    is_stateless=False
                )
                print(f"  Tool server registered successfully")
            except Exception as e:
                print(f"  Warning: Failed to register tool server: {e}")
                # Continue anyway

            # Step 5: Validation-Revision Loop
            print(f"\n[Step 5/5] Starting validation-revision loop...")
            result.state = EnvGenState.VALIDATE_SCENARIOS

            validator = ValidateReviseGen(
                client_manager=client_manager,
                config=self.config,
                logger=self.logger
            )

            # Create checkpoint callback to save intermediate results
            def checkpoint_callback(current_code, initial_code, initial_validation,
                                   current_validation, revision_history, total_revisions):
                """Save checkpoint after each revision."""
                if not self.config.save_intermediate:
                    return
                # Update result with current state
                result.tool_code = current_code
                result.initial_tool_code = initial_code
                result.initial_validation = initial_validation
                result.final_validation = current_validation
                result.revision_history = revision_history
                result.total_revisions = total_revisions
                # Save checkpoint
                checkpoint_path = self.save_checkpoint(result, metadata_info)
                if checkpoint_path:
                    print(f"[ValidateRevise] Checkpoint saved: {checkpoint_path}")

            validation_result_dict, turn_idx = await validator.validate_revise_loop(
                mcp_server_name=metadata_info['class_name'],
                mcp_server_description=metadata_info['description'],
                tool_code=result.tool_code,
                tools_metadata=metadata_info['tools'],
                scenarios=scenarios,
                conversation_id=conversation_id,
                start_turn_idx=turn_idx,
                checkpoint_callback=checkpoint_callback if self.config.save_intermediate else None
            )

            # Extract validation result from tuple
            validation_result = validation_result_dict

            # Update result with validation info
            result.initial_validation = validation_result['initial_validation']
            result.final_validation = validation_result['final_validation']
            result.revision_history = validation_result['revision_history']
            result.total_revisions = validation_result['total_revisions']
            result.tool_code = validation_result['final_code']
            result.success = validation_result['success']

            # Save final tool code
            if result.total_revisions > 0:
                tool_path = self.tool_gen.save_tools(
                    mcp_server_name=metadata_info['class_name'],
                    tool_code=result.tool_code
                )
                result.saved_paths['tool_path'] = normalize_path(tool_path)
                print(f"\n  Final tool code saved to: {normalize_path(tool_path)}")

            # Save final checkpoint if configured
            if self.config.save_intermediate:
                checkpoint_path = self.save_checkpoint(result, metadata_info)
                if checkpoint_path:
                    print(f"  Final checkpoint saved to: {checkpoint_path}")

            # Print summary
            print(f"\n{'='*60}")
            if result.success and result.final_validation:
                result.state = EnvGenState.COMPLETED
                print(f"✓ Environment generation COMPLETED")
                print(f"  All {result.final_validation.total_scenarios} scenarios passed")
            else:
                result.state = EnvGenState.FAILED
                print(f"⚠ Environment generation INCOMPLETE")
                if result.final_validation:
                    print(f"  Passed: {result.final_validation.passed_scenarios}/{result.final_validation.total_scenarios}")
                    print(f"  Failed: {result.final_validation.failed_scenarios}/{result.final_validation.total_scenarios}")
                else:
                    print(f"  Validation not completed")
                    if result.error_message:
                        print(f"  Error: {result.error_message}")

            if result.total_revisions > 0:
                print(f"  Revisions: {result.total_revisions}")

        except Exception as e:
            result.state = EnvGenState.FAILED
            result.success = False
            result.error_message = str(e)
            print(f"\n✗ Environment generation FAILED: {e}")
            import traceback
            traceback.print_exc()

        finally:
            result.total_time = time.time() - start_time
            print(f"  Total time: {result.total_time:.2f}s")
            print(f"{'='*60}\n")
            # Dump logs for this conversation at the end
            log_name = Path(self.config.log_dump_path).name
            dumped = self.logger.dump_log(conversation_id, log_name)
            if dumped:
                print(f"  Logs saved to: {self.config.log_dump_path}")
            else:
                print(f"  Warning: No logs found for conversation '{conversation_id}'")

        return result

    def save_checkpoint(self, result: EnvGenResult, schema: dict) -> Optional[Path]:
        """
        Save unified checkpoint file.

        Args:
            result: Current EnvGenResult
            schema: Complete metadata/schema information

        Returns:
            Path to saved checkpoint file or None
        """
        try:
            intermediate_dir = Path(self.config.intermediate_dir)
            intermediate_dir.mkdir(parents=True, exist_ok=True)

            # Create checkpoint data
            checkpoint = CheckpointData.from_env_gen_result(result, schema)

            # Save checkpoint
            checkpoint_path = intermediate_dir / f"{result.class_name}_checkpoint.json"
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint.to_dict(), f, indent=2, ensure_ascii=False)

            return checkpoint_path

        except Exception as e:
            print(f"Warning: Failed to save checkpoint: {e}")
            import traceback
            traceback.print_exc()
            return None

    def load_checkpoint(self, checkpoint_path: str) -> Optional[CheckpointData]:
        """
        Load checkpoint from file.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            CheckpointData object or None if failed
        """
        try:
            checkpoint_file = Path(checkpoint_path)
            if not checkpoint_file.exists():
                print(f"Checkpoint file not found: {checkpoint_path}")
                return None

            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            checkpoint = CheckpointData.from_dict(data)
            print(f"Loaded checkpoint: {checkpoint.metadata['class_name']}")
            print(f"  State: {checkpoint.metadata['state']}")
            print(f"  Last updated: {checkpoint.metadata['last_updated']}")

            return checkpoint

        except Exception as e:
            print(f"Failed to load checkpoint: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _save_intermediate(self, result: EnvGenResult, stage: str) -> Optional[Path]:
        """
        Legacy method for backward compatibility.
        Now calls save_checkpoint internally.

        Args:
            result: Current EnvGenResult
            stage: Stage name (ignored, kept for compatibility)

        Returns:
            Path to saved file or None
        """
        # Use the new unified checkpoint system
        return self.save_checkpoint(result, result.schema or {})

    async def resume_from_checkpoint(
        self,
        checkpoint_path: str,
        conversation_id: Optional[str] = None
    ) -> EnvGenResult:
        """
        Resume generation from a checkpoint file.

        Args:
            checkpoint_path: Path to checkpoint file
            conversation_id: Conversation ID for logging

        Returns:
            EnvGenResult with complete generation information
        """
        print(f"\n{'='*60}")
        print(f"Resuming from checkpoint: {checkpoint_path}")
        print(f"{'='*60}")

        # Load checkpoint
        checkpoint = self.load_checkpoint(checkpoint_path)
        if checkpoint is None:
            raise ValueError(f"Failed to load checkpoint from {checkpoint_path}")

        # Convert checkpoint to EnvGenResult
        result = checkpoint.to_env_gen_result()

        if conversation_id is None:
            conversation_id = f"env_gen_resume_{result.class_name}"

        # Determine which stage to resume from
        state = EnvGenState(checkpoint.metadata['state'])

        print(f"Checkpoint state: {state.value}")
        print(f"Class: {result.class_name}")

        if state == EnvGenState.TOOL_GEN or state == EnvGenState.SCENARIO_GEN:
            # Resume from scenario generation
            return await self._resume_from_scenario_gen(checkpoint, conversation_id)

        elif state == EnvGenState.VALIDATE_SCENARIOS or state == EnvGenState.REVISE:
            # Resume from validation
            return await self._resume_from_validation(checkpoint, conversation_id)

        elif state == EnvGenState.COMPLETED:
            print("Checkpoint already completed. Returning existing result.")
            return result

        elif state == EnvGenState.FAILED:
            print("Checkpoint is in failed state. Attempting to retry from validation...")
            return await self._resume_from_validation(checkpoint, conversation_id)

        else:
            # Default: start from scenario generation if we have tool code
            if checkpoint.tool_code_history:
                return await self._resume_from_scenario_gen(checkpoint, conversation_id)
            else:
                raise ValueError(f"Cannot resume from state: {state.value}")

    async def _resume_from_scenario_gen(
        self,
        checkpoint: CheckpointData,
        conversation_id: str
    ) -> EnvGenResult:
        """
        Resume from scenario generation stage.

        Args:
            checkpoint: CheckpointData object
            conversation_id: Conversation ID for logging

        Returns:
            EnvGenResult after completion
        """
        start_time = time.time()
        result = checkpoint.to_env_gen_result()
        turn_idx = 0

        try:
            # Get the latest tool code
            if not checkpoint.tool_code_history:
                raise ValueError("No tool code found in checkpoint")

            latest_code = checkpoint.tool_code_history[-1]['code']
            result.tool_code = latest_code
            result.state = EnvGenState.SCENARIO_GEN

            # Check if scenarios already exist
            if not checkpoint.scenarios:
                print(f"\n[Resuming] Generating test scenarios...")
                scenarios, turn_idx = await self.scenario_gen.generate_scenarios(
                    mcp_server_name=result.class_name,
                    tool_code=latest_code,
                    n_scenarios=self.config.n_scenarios,
                    conversation_id=conversation_id,
                    start_turn_idx=turn_idx
                )
                result.scenarios = scenarios
                print(f"  Generated {len(scenarios)} scenarios")

                # Save checkpoint after scenario generation
                if self.config.save_intermediate:
                    self.save_checkpoint(result, checkpoint.schema)
            else:
                print(f"  Using existing {len(checkpoint.scenarios)} scenarios from checkpoint")
                result.scenarios = checkpoint.scenarios

            # Continue to validation
            return await self._resume_from_validation_internal(
                result,
                checkpoint,
                conversation_id,
                turn_idx,
                start_time
            )

        except Exception as e:
            result.state = EnvGenState.FAILED
            result.success = False
            result.error_message = str(e)
            result.total_time = time.time() - start_time
            print(f"\n✗ Resume failed: {e}")
            import traceback
            traceback.print_exc()
            return result

    async def _resume_from_validation(
        self,
        checkpoint: CheckpointData,
        conversation_id: str
    ) -> EnvGenResult:
        """
        Resume from validation stage.

        Args:
            checkpoint: CheckpointData object
            conversation_id: Conversation ID for logging

        Returns:
            EnvGenResult after completion
        """
        start_time = time.time()
        result = checkpoint.to_env_gen_result()
        turn_idx = 0

        try:
            # Validate we have necessary data
            if not checkpoint.tool_code_history:
                raise ValueError("No tool code found in checkpoint")
            if not checkpoint.scenarios:
                raise ValueError("No scenarios found in checkpoint")

            return await self._resume_from_validation_internal(
                result,
                checkpoint,
                conversation_id,
                turn_idx,
                start_time
            )

        except Exception as e:
            result.state = EnvGenState.FAILED
            result.success = False
            result.error_message = str(e)
            result.total_time = time.time() - start_time
            print(f"\n✗ Resume failed: {e}")
            import traceback
            traceback.print_exc()
            return result

    async def _resume_from_validation_internal(
        self,
        result: EnvGenResult,
        checkpoint: CheckpointData,
        conversation_id: str,
        turn_idx: int,
        start_time: float
    ) -> EnvGenResult:
        """
        Internal method to handle validation and revision from checkpoint.

        Args:
            result: EnvGenResult object
            checkpoint: CheckpointData object
            conversation_id: Conversation ID
            turn_idx: Current turn index
            start_time: Start time for timing

        Returns:
            EnvGenResult after completion
        """
        try:
            result.state = EnvGenState.VALIDATE_SCENARIOS

            # Get tool path
            tool_path_str = result.saved_paths.get('tool_path')
            if not tool_path_str:
                # Need to save the tool first
                tool_path = self.tool_gen.save_tools(
                    mcp_server_name=result.class_name,
                    tool_code=result.tool_code
                )
                tool_path_str = normalize_path(tool_path)
                result.saved_paths['tool_path'] = tool_path_str
            else:
                # tool_path_str is already normalized (from saved_paths)
                tool_path = Path(tool_path_str)

            print(f"\n[Resuming] Registering tool server...")
            update_mcp_server_config(
                config_path="configs/mcp_server.json",
                mcp_server_name=result.class_name,
                tool_path=tool_path_str,
                is_stateless=False
            )

            client_manager = MCPClientManager()
            try:
                client_manager.register_MCP_server(
                    server_name=result.class_name,
                    tool_path=tool_path_str,
                    is_stateless=False
                )
                print(f"  Tool server registered successfully")
            except Exception as e:
                print(f"  Warning: Failed to register tool server: {e}")

            print(f"\n[Resuming] Starting validation-revision loop...")
            validator = ValidateReviseGen(
                client_manager=client_manager,
                config=self.config,
                logger=self.logger
            )

            # Create checkpoint callback to save intermediate results
            def checkpoint_callback(current_code, initial_code, initial_validation,
                                   current_validation, revision_history, total_revisions):
                """Save checkpoint after each revision."""
                if not self.config.save_intermediate:
                    return
                # Update result with current state
                result.tool_code = current_code
                result.initial_tool_code = initial_code
                result.initial_validation = initial_validation
                result.final_validation = current_validation
                result.revision_history = revision_history
                result.total_revisions = total_revisions
                # Save checkpoint
                checkpoint_path = self.save_checkpoint(result, checkpoint.schema)
                if checkpoint_path:
                    print(f"[ValidateRevise] Checkpoint saved: {checkpoint_path}")

            validation_result_dict, turn_idx = await validator.validate_revise_loop(
                mcp_server_name=result.class_name,
                mcp_server_description=checkpoint.schema.get('description', ''),
                tool_code=result.tool_code,
                tools_metadata=checkpoint.schema.get('tools', []),
                scenarios=result.scenarios,
                conversation_id=conversation_id,
                start_turn_idx=turn_idx,
                checkpoint_callback=checkpoint_callback if self.config.save_intermediate else None
            )

            # Update result with validation info
            result.initial_validation = validation_result_dict['initial_validation']
            result.final_validation = validation_result_dict['final_validation']
            result.revision_history = validation_result_dict['revision_history']
            result.total_revisions = validation_result_dict['total_revisions']
            result.tool_code = validation_result_dict['final_code']
            result.initial_tool_code = validation_result_dict.get('initial_code', result.tool_code)
            result.success = validation_result_dict['success']

            # Save final tool code
            if result.total_revisions > 0:
                tool_path = self.tool_gen.save_tools(
                    mcp_server_name=result.class_name,
                    tool_code=result.tool_code
                )
                result.saved_paths['tool_path'] = normalize_path(tool_path)
                print(f"\n  Final tool code saved to: {normalize_path(tool_path)}")

            # Save final checkpoint
            if self.config.save_intermediate:
                checkpoint_path = self.save_checkpoint(result, checkpoint.schema)
                print(f"  Final checkpoint saved to: {checkpoint_path}")

            # Print summary
            print(f"\n{'='*60}")
            if result.success and result.final_validation:
                result.state = EnvGenState.COMPLETED
                print(f"✓ Resume COMPLETED")
                print(f"  All {result.final_validation.total_scenarios} scenarios passed")
            else:
                result.state = EnvGenState.FAILED
                print(f"⚠ Resume INCOMPLETE")
                if result.final_validation:
                    print(f"  Passed: {result.final_validation.passed_scenarios}/{result.final_validation.total_scenarios}")
                    print(f"  Failed: {result.final_validation.failed_scenarios}/{result.final_validation.total_scenarios}")

            if result.total_revisions > 0:
                print(f"  Revisions: {result.total_revisions}")

            result.total_time = time.time() - start_time
            print(f"  Total time: {result.total_time:.2f}s")
            print(f"{'='*60}\n")

            # Dump logs
            log_name = Path(self.config.log_dump_path).name
            dumped = self.logger.dump_log(conversation_id, log_name)
            if dumped:
                print(f"  Logs saved to: {self.config.log_dump_path}")

            return result

        except Exception as e:
            result.state = EnvGenState.FAILED
            result.success = False
            result.error_message = str(e)
            result.total_time = time.time() - start_time
            print(f"\n✗ Validation/revision failed: {e}")
            import traceback
            traceback.print_exc()
            return result

    async def generate_multiple_parallel(
        self,
        metadata_paths: List[str]
    ) -> List[EnvGenResult]:
        """
        Generate MCP environments for multiple metadata files in parallel.

        Args:
            metadata_paths: List of metadata file paths

        Returns:
            List of EnvGenResult objects
        """
        print(f"\n{'='*60}")
        print(f"Parallel Environment Generation")
        print(f"{'='*60}")
        print(f"Processing {len(metadata_paths)} metadata files")
        print(f"Max concurrent: {self.config.max_concurrent_files}")
        print(f"{'='*60}\n")

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.config.max_concurrent_files)

        async def generate_with_semaphore(metadata_path: str, index: int) -> EnvGenResult:
            async with semaphore:
                print(f"\n[{index+1}/{len(metadata_paths)}] Starting: {Path(metadata_path).name}")
                conversation_id = f"parallel_env_gen_{index}_{Path(metadata_path).stem}"
                return await self.generate_mcp_env(
                    metadata_path=metadata_path,
                    conversation_id=conversation_id
                )

        # Generate all in parallel
        results = await asyncio.gather(
            *[generate_with_semaphore(path, i) for i, path in enumerate(metadata_paths)],
            return_exceptions=True
        )

        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"\n✗ Exception in parallel task {i+1}: {result}")
                # Create a failed result
                failed_result = EnvGenResult(
                    metadata_path=metadata_paths[i],
                    class_name=Path(metadata_paths[i]).stem,
                    state=EnvGenState.FAILED,
                    success=False,
                    error_message=str(result)
                )
                final_results.append(failed_result)
            else:
                final_results.append(result)

        return final_results


async def main():
    """Main entry point for command-line execution."""
    # Get default config to use its values for argument defaults
    from src.gen.env_gen import EnvGenConfig
    default_config = EnvGenConfig()

    parser = argparse.ArgumentParser(
        description="Generate MCP environments with validation and revision",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from metadata
  python -m src.gen.env_gen envs/metadata/GoogleMaps-metadata.json
  python -m src.gen.env_gen envs/metadata/GoogleMaps-metadata.json --n-scenarios 10
  python -m src.gen.env_gen envs/metadata/*.json --max-concurrent-files 5
  python -m src.gen.env_gen envs/metadata/Calendar_metadata.json --max-revisions 5

  # Resume from checkpoint
  python -m src.gen.env_gen --resume envs/intermediate/Calendar_checkpoint.json
        """
    )

    parser.add_argument(
        "metadata_paths",
        type=str,
        nargs='*',  # Changed from '+' to '*' to make it optional when using --resume
        help="Path(s) to metadata file(s). Can specify multiple files for parallel processing. Not required when using --resume."
    )

    parser.add_argument(
        "--n-scenarios",
        type=int,
        default=default_config.n_scenarios,
        help=f"Number of test scenarios to generate (default: {default_config.n_scenarios})"
    )

    parser.add_argument(
        "--max-revisions",
        type=int,
        default=default_config.max_revisions,
        help=f"Maximum number of validation-revision loops (default: {default_config.max_revisions})"
    )

    parser.add_argument(
        "--max-concurrent-files",
        type=int,
        default=default_config.max_concurrent_files,
        help=f"Maximum number of metadata files to process in parallel (default: {default_config.max_concurrent_files})"
    )

    parser.add_argument(
        "--max-concurrent-scenarios",
        type=int,
        default=default_config.max_concurrent_scenarios,
        help=f"Maximum number of scenarios to validate in parallel (default: {default_config.max_concurrent_scenarios})"
    )

    parser.add_argument(
        "--model",
        type=str,
        default=default_config.model_name,
        help=f"Model to use (default: {default_config.model_name})"
    )

    parser.add_argument(
        "--no-intermediate",
        action="store_true",
        help="Don't save intermediate results"
    )

    parser.add_argument(
        "--resume",
        type=str,
        help="Resume from checkpoint file (e.g., envs/intermediate/Calendar_checkpoint.json)"
    )

    args = parser.parse_args()

    # Create configuration first (needed for all modes)
    config = EnvGenConfig(
        model_name=args.model,
        n_scenarios=args.n_scenarios,
        max_revisions=args.max_revisions,
        max_concurrent_files=args.max_concurrent_files,
        max_concurrent_scenarios=args.max_concurrent_scenarios,
        save_intermediate=not args.no_intermediate
    )

    env_gen = EnvGen(config=config)

    # Handle resume mode
    if args.resume:
        checkpoint_path = Path(args.resume)
        if not checkpoint_path.exists():
            print(f"Error: Checkpoint file does not exist: {checkpoint_path}", file=sys.stderr)
            sys.exit(1)

        try:
            result = await env_gen.resume_from_checkpoint(
                checkpoint_path=str(checkpoint_path)
            )

            # Print final summary
            print(f"\n{'='*60}")
            print("FINAL SUMMARY (RESUMED)")
            print(f"{'='*60}")
            print(f"Class: {result.class_name}")
            print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
            if result.success and result.final_validation:
                print(f"Scenarios: {result.final_validation.total_scenarios} all passed")
            elif result.final_validation:
                print(f"Scenarios: {result.final_validation.passed_scenarios}/{result.final_validation.total_scenarios} passed")
            else:
                print(f"Scenarios: Validation not completed")
                if result.error_message:
                    print(f"Error: {result.error_message}")
            print(f"Revisions: {result.total_revisions}")
            print(f"Tool Path: {result.saved_paths.get('tool_path', 'N/A')}")
            print(f"Total Time: {result.total_time:.2f}s")
            print(f"{'='*60}")

            if not result.success:
                sys.exit(1)
            sys.exit(0)

        except Exception as e:
            print(f"\nError resuming from checkpoint: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)

    # Normal generation mode
    # Check if metadata files are provided and exist
    if not args.metadata_paths:
        print("Error: metadata_paths is required for normal generation mode", file=sys.stderr)
        print("Use --resume to resume from checkpoint", file=sys.stderr)
        sys.exit(1)

    # Expand glob patterns (needed for Windows where shell doesn't expand wildcards)
    expanded_paths = []
    for pattern in args.metadata_paths:
        # Check if pattern contains wildcards
        if '*' in pattern or '?' in pattern:
            # Use glob to expand the pattern
            matches = glob.glob(pattern)
            if not matches:
                print(f"Warning: No files match pattern: {pattern}", file=sys.stderr)
            expanded_paths.extend(matches)
        else:
            # No wildcards, use as-is
            expanded_paths.append(pattern)

    if not expanded_paths:
        print("Error: No metadata files found", file=sys.stderr)
        sys.exit(1)

    metadata_paths = [Path(p) for p in expanded_paths]
    missing_files = [p for p in metadata_paths if not p.exists()]
    if missing_files:
        print("Error: Metadata file(s) do not exist:", file=sys.stderr)
        for p in missing_files:
            print(f"  - {p}", file=sys.stderr)
        sys.exit(1)

    # Execute generation
    try:
        if len(metadata_paths) == 1:
            # Single file processing
            result = await env_gen.generate_mcp_env(
                metadata_path=str(metadata_paths[0])
            )

            # Print final summary
            print(f"\n{'='*60}")
            print("FINAL SUMMARY")
            print(f"{'='*60}")
            print(f"Class: {result.class_name}")
            print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
            if result.success and result.final_validation:
                print(f"Scenarios: {result.final_validation.total_scenarios} all passed")
            elif result.final_validation:
                print(f"Scenarios: {result.final_validation.passed_scenarios}/{result.final_validation.total_scenarios} passed")
            else:
                print(f"Scenarios: Validation not completed")
                if result.error_message:
                    print(f"Error: {result.error_message}")
            print(f"Revisions: {result.total_revisions}")
            print(f"Tool Path: {result.saved_paths.get('tool_path', 'N/A')}")
            print(f"Total Time: {result.total_time:.2f}s")
            print(f"{'='*60}")

            if not result.success:
                sys.exit(1)

        else:
            # Parallel processing
            results = await env_gen.generate_multiple_parallel(
                metadata_paths=[str(p) for p in metadata_paths]
            )

            # Print final summary
            print(f"\n{'='*60}")
            print("PARALLEL GENERATION SUMMARY")
            print(f"{'='*60}")

            success_count = sum(1 for r in results if r.success)
            failure_count = len(results) - success_count
            total_time = sum(r.total_time for r in results)

            for result in results:
                status = "✓" if result.success else "✗"
                print(f"{status} {result.class_name}: {result.state.value}")
                if result.success and result.final_validation:
                    print(f"    Scenarios: {result.final_validation.total_scenarios} passed")
                else:
                    if result.final_validation:
                        print(f"    Scenarios: {result.final_validation.passed_scenarios}/{result.final_validation.total_scenarios} passed")
                    else:
                        print(f"    Scenarios: Validation not completed")
                    if result.error_message:
                        print(f"    Error: {result.error_message}")
                if result.total_revisions > 0:
                    print(f"    Revisions: {result.total_revisions}")

            print(f"\n{'='*60}")
            print(f"Total: {len(results)} files")
            print(f"Success: {success_count}")
            print(f"Failed: {failure_count}")
            print(f"Total Time: {total_time:.2f}s")
            print(f"{'='*60}")

            if failure_count > 0:
                sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
