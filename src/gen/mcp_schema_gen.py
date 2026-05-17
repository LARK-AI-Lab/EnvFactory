import os
os.environ['SKIP_MCP_AUTO_INIT'] = 'True' 
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from agents import Agent, Runner
from src.gen import Gen
from src.gen.env_gen import EnvGenConfig
from src.gen.prompts import SchemaGen_System_Prompt, SchemaGen_User_Prompt, SchemaDesign_System_Prompt


class SchemaGen(Gen):
    """
    Schema Generator for converting data_source files to mcp_server_schema format.
    """
    
    def __init__(self, config: Optional[EnvGenConfig] = None, logger=None):
        """
        Initialize the SchemaGen with agents.
        
        Args:
            config: Configuration object (EnvGenConfig)
            logger: Optional shared logger instance
        """
        config = config or EnvGenConfig()
        super().__init__(config, logger=logger)
        self.load_agents()
    
    def load_agents(self) -> None:
        """Load schema generator and designer agents."""
        schema_model = self.get_model(
            self.config.schema_gen_model if self.config.schema_gen_model else self.config.model_name
        )
        
        self.schema_generator = Agent(
            name="SchemaGen",
            instructions=SchemaGen_System_Prompt,
            model=schema_model,
        )
        self.schema_designer = Agent(
            name="SchemaDesign",
            instructions=SchemaDesign_System_Prompt,
            model=schema_model,    
        )
    

    def _load_data_source(self, file_path: str) -> Dict[str, Any]:
        """
        Load and parse a data_source JSON file.
        
        Args:
            file_path: Path to the data_source JSON file
            
        Returns:
            Dict containing the parsed JSON data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"Data source file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    def _extract_tools_info(self, data_source: Dict[str, Any]) -> str:
        """
        Extract tools information from data_source for better context.
        
        Args:
            data_source: Parsed data_source dictionary
            
        Returns:
            str: Formatted string containing tools information
        """
        tools_info = []
        
        # Try to get tools from remote_server_response
        if 'metadata' in data_source:
            metadata = data_source['metadata']
            
            # Check remote_server_response
            if 'remote_server_response' in metadata and 'tools' in metadata['remote_server_response']:
                tools = metadata['remote_server_response']['tools']
                for tool in tools:
                    tool_str = f"- {tool.get('name', 'unknown')}: {tool.get('description', 'No description')}"
                    tools_info.append(tool_str)
            
            # Also check server_info_crawled
            elif 'server_info_crawled' in metadata and 'tools' in metadata['server_info_crawled']:
                tools = metadata['server_info_crawled']['tools']
                for tool in tools:
                    tool_str = f"- {tool.get('name', 'unknown')}: {tool.get('description', 'No description')}"
                    tools_info.append(tool_str)
        
        if tools_info:
            return "\n".join(tools_info)
        return "No tools information found"
    
    def _validate_and_save_schema(self, schema: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate schema structure and save to file if output_path is provided.
        
        Args:
            schema: The schema dictionary to validate
            output_path: Optional path to save the validated schema
            
        Returns:
            The validated schema dictionary
            
        Raises:
            ValueError: If schema validation fails
        """
        if not isinstance(schema, dict):
            raise ValueError("Schema must be a dictionary")
        
        required_fields = ['class_name', 'description', 'tools']
        for field in required_fields:
            if field not in schema:
                raise ValueError(f"Schema missing required field: {field}")
        
        class_name = schema.get('class_name', '')
        
        if not isinstance(schema['tools'], list):
            raise ValueError("'tools' must be a list")
        
        for i, tool in enumerate(schema['tools']):
            if not isinstance(tool, dict):
                raise ValueError(f"Tool at index {i} must be a dictionary")
            
            tool_required_fields = ['name', 'description', 'input_schema', 'output_schema']
            for field in tool_required_fields:
                if field not in tool:
                    raise ValueError(f"Tool at index {i} missing required field: {field}")

        if output_path is None:
            metadata_dir = Path("envs/metadata")
            metadata_dir.mkdir(parents=True, exist_ok=True)
            output_path = metadata_dir / f"{class_name}_metadata.json"
        else:
            output_path = Path(output_path)
        
        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        
        return schema

    async def generate(
        self, 
        data_source_path: str, 
        output_path: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate mcp_server_schema from a data_source file.
        
        Args:
            data_source_path: Path to the input data_source JSON file
            output_path: Optional path to save the generated schema. If None, will use class_name + "-metadata.json" in envs/metadata/
            conversation_id: Conversation ID for logging
            
        Returns:
            Dict containing the generated mcp_server_schema
            
        Raises:
            FileNotFoundError: If data_source file doesn't exist
            ValueError: If schema generation fails or output is invalid
        """
        # Load data source
        data_source = self._load_data_source(data_source_path)
        
        # Convert data_source to JSON string for prompt
        data_source_str = json.dumps(data_source, indent=2, ensure_ascii=False)
        
        # Construct user prompt
        user_prompt = SchemaGen_User_Prompt.format(
            data_source_content=data_source_str
        )
        
        if conversation_id is None:
            conversation_id = f"schema_gen_{Path(data_source_path).stem}"
        
        try:
            output = await Runner.run(
                self.schema_generator,
                input=user_prompt,
                max_turns=self.config.max_turns
            )
            
            # Log interaction
            output_dict = await self.log(
                conversation_id=conversation_id,
                idx=0,
                agent=self.schema_generator,
                output=output
            )
            
            if 'schema' not in output_dict:
                raise ValueError("Agent output does not contain 'schema' field")
            
            schema = output_dict['schema']
            
            # Validate and save schema
            result = self._validate_and_save_schema(schema, output_path)
            
            # Dump logs
            log_name = Path(self.config.log_dump_path).name
            self.logger.dump_log(conversation_id, log_name)
            
            return result
            
        except Exception as e:
            # Dump logs even on failure
            log_name = Path(self.config.log_dump_path).name
            self.logger.dump_log(conversation_id, log_name)
            raise ValueError(f"Schema generation failed: {str(e)}") from e
    
    async def design(
        self, 
        schema_sketch: str, 
        output_path: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Design mcp_server_schema from a schema sketch (skeleton code or description).
        
        Args:
            schema_sketch: String containing skeleton code or description of an MCP server
            output_path: Optional path to save the generated schema. If None, will use class_name + "-metadata.json" in envs/metadata/
            conversation_id: Conversation ID for logging
            
        Returns:
            Dict containing the generated mcp_server_schema
            
        Raises:
            ValueError: If schema design fails or output is invalid
        """
        if conversation_id is None:
            conversation_id = f"schema_design_{hash(schema_sketch) % 100000}"
        
        try:
            output = await Runner.run(
                self.schema_designer,
                input=schema_sketch,
                max_turns=self.config.max_turns
            )

            # Log interaction
            output_dict = await self.log(
                conversation_id=conversation_id,
                idx=0,
                agent=self.schema_designer,
                output=output
            )
            
            if 'schema' not in output_dict:
                error_msg = (
                    f"Agent output does not contain 'schema' field. "
                    f"Found keys: {list(output_dict.keys())}. "
                    f"Raw output length: {len(output.final_output)} characters. "
                    f"Please check if the agent returned output in the expected format with <schema> tags."
                )
                raise ValueError(error_msg)
            
            schema = output_dict['schema']
            
            # Validate and save schema
            result = self._validate_and_save_schema(schema, output_path)
            
            # Dump logs
            log_name = Path(self.config.log_dump_path).name
            self.logger.dump_log(conversation_id, log_name)
            
            return result
            
        except Exception as e:
            # Dump logs even on failure
            log_name = Path(self.config.log_dump_path).name
            self.logger.dump_log(conversation_id, log_name)
            raise ValueError(f"Schema design failed: {str(e)}") from e
    
    def design_sync(self, schema_sketch: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Synchronous wrapper for design method.
        Compatible with Jupyter notebook environments.
        
        Args:
            schema_sketch: String containing skeleton code or description of an MCP server
            output_path: Optional path to save the generated schema. If None, will use class_name + "-metadata.json" in envs/metadata/
            
        Returns:
            Dict containing the generated mcp_server_schema
        """
        import asyncio
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # Use nest_asyncio to allow nested event loops
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError as exc:
                raise RuntimeError(
                    "nest_asyncio is required when running in an environment with an existing event loop. "
                    "Install it with: pip install nest-asyncio"
                ) from exc
            # Now we can use run_until_complete
            return loop.run_until_complete(self.design(schema_sketch, output_path))
        except RuntimeError:
            # No running loop, create a new one
            return asyncio.run(self.design(schema_sketch, output_path))
    
    def generate_sync(self, data_source_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Synchronous wrapper for generate method.
        Compatible with Jupyter notebook environments.
        
        Args:
            data_source_path: Path to the input data_source JSON file
            output_path: Optional path to save the generated schema. If None, will use class_name + "-metadata.json" in envs/metadata/
            
        Returns:
            Dict containing the generated mcp_server_schema
        """
        import asyncio
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # Use nest_asyncio to allow nested event loops
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError as exc:
                raise RuntimeError(
                    "nest_asyncio is required when running in an environment with an existing event loop. "
                    "Install it with: pip install nest-asyncio"
                ) from exc
            # Now we can use run_until_complete
            return loop.run_until_complete(self.generate(data_source_path, output_path))
        except RuntimeError:
            # No running loop, create a new one
            return asyncio.run(self.generate(data_source_path, output_path))


def main():
    """Main entry point for command-line execution."""
    parser = argparse.ArgumentParser(
        description="Generate MCP server metadata from schema sketch (skeleton code or description)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From a file containing schema sketch
  python -m src.gen.mcp_schema_gen envs/tools/Calendar.py
  
  # From a file with custom output path
  python -m src.gen.mcp_schema_gen envs/tools/Calendar.py --output envs/metadata/Calendar_metadata.json
  
  # From stdin (pipe input)
  cat envs/tools/Calendar.py | python -m src.gen.mcp_schema_gen -
  
  # Specify model
  python -m src.gen.mcp_schema_gen envs/tools/Calendar.py --model kimi-k2
        """
    )
    
    parser.add_argument(
        "schema_sketch",
        type=str,
        help="Path to file containing schema sketch (Python/TypeScript code) or '-' to read from stdin"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output path for generated metadata. If not specified, will save to envs/metadata/{class_name}_metadata.json"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model to use (e.g., kimi-k2, qwen-max, deepseek-chat). If not specified, uses default from config"
    )
    
    args = parser.parse_args()
    
    # Read schema sketch
    if args.schema_sketch == "-":
        # Read from stdin
        schema_sketch = sys.stdin.read()
    else:
        # Read from file
        sketch_path = Path(args.schema_sketch)
        if not sketch_path.exists():
            print(f"Error: Schema sketch file not found: {sketch_path}", file=sys.stderr)
            sys.exit(1)
        
        with open(sketch_path, 'r', encoding='utf-8') as f:
            schema_sketch = f.read()
    
    # Create configuration
    config_kwargs = {}
    if args.model:
        config_kwargs['model_name'] = args.model
        config_kwargs['schema_gen_model'] = args.model
    
    config = EnvGenConfig(**config_kwargs) if config_kwargs else EnvGenConfig()
    
    # Initialize SchemaGen and generate metadata
    try:
        schema_gen = SchemaGen(config=config)
        print(f"Generating metadata from schema sketch...")
        if args.schema_sketch != "-":
            print(f"Input file: {args.schema_sketch}")
        if args.output:
            print(f"Output path: {args.output}")
        print()
        
        result = schema_gen.design_sync(
            schema_sketch=schema_sketch,
            output_path=args.output
        )
        
        # Print success message
        print(f"\n{'='*60}")
        print("METADATA GENERATION SUCCESS")
        print(f"{'='*60}")
        print(f"Class Name: {result.get('class_name', 'N/A')}")
        print(f"Description: {result.get('description', 'N/A')[:100]}...")
        print(f"Tools Count: {len(result.get('tools', []))}")
        
        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            class_name = result.get('class_name', 'Unknown')
            output_path = Path("envs/metadata") / f"{class_name}_metadata.json"
        
        print(f"Saved to: {output_path}")
        print(f"{'='*60}\n")
        
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
