from __future__ import annotations

import numpy as np
from tqdm import tqdm

from src.graph.prompts import Get_User_Provided_Prompt
from src.manager.llm_client_manager import LLMClient
from src.utils.utils import to_JSON

class Parameter:
    def __init__(self, name: str, description: str, data_type: str):
        self.name = name
        self.description = description
        self.data_type = data_type
        self._embedding = None
        self._name_embedding = None
        self._description_embedding = None
        self._user_provided = None

    @property
    def embedding(self):
        """Legacy property for backward compatibility."""
        if self._embedding is None:
            self._embedding = LLMClient.encode(str(self), disable_progress_bar=True)
        return self._embedding

    @property
    def name_embedding(self):
        """Embedding for name and data_type: '{name} ({data_type})'."""
        if self._name_embedding is None:
            name_text = f"{self.name} ({self.data_type})"
            self._name_embedding = LLMClient.encode(name_text, disable_progress_bar=True)
        return self._name_embedding

    @property
    def description_embedding(self):
        """Embedding for description."""
        if self._description_embedding is None:
            self._description_embedding = LLMClient.encode(self.description, disable_progress_bar=True)
        return self._description_embedding

    @property
    def user_provided(self):
        return self._user_provided

    def set_user_provided(self, value: bool):
        """Set the user_provided value directly (used for batch processing)."""
        self._user_provided = value

    def similarity(self, other: Parameter) -> float:
        """
        Compute weighted similarity between two parameters.
        Formula: 0.6 * name_similarity + 0.4 * description_similarity
        """
        # Compute name (dtype) similarity
        name_sim = LLMClient.similarity(self.name_embedding, other.name_embedding).item()
        
        # Compute description similarity
        desc_sim = LLMClient.similarity(self.description_embedding, other.description_embedding).item()
        
        # Weighted combination: 0.6 for name, 0.4 for description
        return 0.6 * name_sim + 0.4 * desc_sim

    def __str__(self):
        return f"{self.name} ({self.data_type}): {self.description}"

    def __repr__(self):
        return f"Parameter({self.name})"

    def __hash__(self):
        return hash(self.name)

class Tool:
    def __init__(self, tool: dict):
        self.server = tool.get('server', '')
        self.name = tool.get("name", "")
        self.description = tool.get("description", "")
        self.input_schema = self._parse_schema(tool.get("input_schema", None))
        self.output_schema = self._parse_schema(tool.get("output_schema", None))

    def _parse_schema(self, schema: dict) -> dict:
        """Parse and embed the given input/output schema."""
        parsed_schema = {
            "parameters": [],
            "text": "",
            "required": [],
        }

        # Handle None or empty schema
        if schema is None:
            return parsed_schema

        # Get required fields
        parsed_schema["required"] = schema.get("required", [])

        # Handle missing properties field
        if "properties" not in schema or schema["properties"] is None:
            return parsed_schema

        # Parse properties
        for param_name, param_info in schema["properties"].items():
            param_type = param_info.get("type", "unknown")
            
            # Handle array types: parse nested object properties
            if param_type == "array" and "items" in param_info:
                items_schema = param_info["items"]
                # Check if items is an object with properties
                if isinstance(items_schema, dict) and items_schema.get("type") == "object" and "properties" in items_schema:
                    # Parse nested properties within the array items
                    for nested_name, nested_info in items_schema["properties"].items():
                        nested_param_name = f"{param_name}.{nested_name}"
                        nested_param = Parameter(
                            name=nested_param_name,
                            description=nested_info.get("description", ""),
                            data_type=nested_info.get("type", "unknown"),
                        )
                        parsed_schema["text"] += f"{str(nested_param)}\n"
                        parsed_schema["parameters"].append(nested_param)
                else:
                    # Array but items is not an object with properties, create parameter for the array itself
                    param = Parameter(
                        name=param_name,
                        description=param_info.get("description", ""),
                        data_type=param_type,
                    )
                    parsed_schema["text"] += f"{str(param)}\n"
                    parsed_schema["parameters"].append(param)
            elif param_type == "object" and "properties" in param_info and param_info["properties"]:
                # Handle object types: parse nested properties
                for nested_name, nested_info in param_info["properties"].items():
                    nested_param_name = f"{param_name}.{nested_name}"
                    nested_param_type = nested_info.get("type", "unknown")
                    
                    # Only extract second level properties, no deeper nesting
                    nested_param = Parameter(
                        name=nested_param_name,
                        description=nested_info.get("description", ""),
                        data_type=nested_param_type,
                    )
                    parsed_schema["text"] += f"{str(nested_param)}\n"
                    parsed_schema["parameters"].append(nested_param)
            else:
                # Non-array, non-object type, create parameter as usual
                param = Parameter(
                    name=param_name,
                    description=param_info.get("description", ""),
                    data_type=param_type,
                )
                parsed_schema["text"] += f"{str(param)}\n"
                parsed_schema["parameters"].append(param)

        return parsed_schema

    def __repr__(self):
        return f"Tool({self.name})"

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, Tool):
            return False
        return self.name == other.name

    def __str__(self):
        result = f"Tool name: {self.name}\n"
        result += f"Tool description: {self.description}\n"

        input_text = self.input_schema['text'].strip()
        if input_text:
            result += f"Input parameters (Required: {self.input_schema['required']}):\n"
            result += f"{input_text}\n"
        else:
            result += "Input parameters: None\n"

        output_text = self.output_schema['text'].strip()
        if output_text:
            result += f"Output fields:\n{output_text}\n"
        else:
            result += "Output fields: None\n"
        
        return result.rstrip()

    
def batch_embedding(parameters: list[Parameter], batch_size: int = 64) -> None:
    """
    Batch-compute embeddings for a list of Parameter.
    Computes both name_embedding and description_embedding for weighted similarity calculation.
    """
    # Filter parameters that need embeddings
    params_needing_name = [p for p in parameters if p._name_embedding is None]
    params_needing_desc = [p for p in parameters if p._description_embedding is None]
    
    # Batch compute name embeddings: "{name} ({data_type})"
    if params_needing_name:
        name_texts = [f"{p.name} ({p.data_type})" for p in params_needing_name]
        name_embeddings = []
        for i in range(0, len(name_texts), batch_size):
            batch = name_texts[i:i + batch_size]
            batch_embeddings = LLMClient.encode(batch, disable_progress_bar=True)
            name_embeddings.extend(batch_embeddings)
        
        for param, emb in zip(params_needing_name, name_embeddings):
            param._name_embedding = emb
    
    # Batch compute description embeddings
    if params_needing_desc:
        # Separate parameters with empty and non-empty descriptions
        params_with_desc = []
        params_empty_desc = []
        desc_texts = []
        
        for p in params_needing_desc:
            desc = p.description if p.description else ""
            if desc.strip():
                # Has description, will compute embedding
                params_with_desc.append(p)
                desc_texts.append(desc)
            else:
                # Empty description, will set to zero vector
                params_empty_desc.append(p)
        
        # Note: Parameters with empty descriptions will get zero vectors
        # This is intentional - empty descriptions should not contribute to similarity
        
        # Compute embeddings only for parameters with descriptions
        desc_embeddings = []
        if desc_texts:
            for i in range(0, len(desc_texts), batch_size):
                batch = desc_texts[i:i + batch_size]
                batch_embeddings = LLMClient.encode(batch, disable_progress_bar=True)
                desc_embeddings.extend(batch_embeddings)
        
        # Determine embedding dimension
        if desc_embeddings:
            # Use dimension from computed embeddings
            emb_dim = len(desc_embeddings[0])
        elif params_empty_desc:
            # All descriptions are empty, need to get dimension from a dummy call
            dummy_emb = LLMClient.encode(["dummy"], disable_progress_bar=True)[0]
            emb_dim = len(dummy_emb)
        else:
            # No empty descriptions, skip assignment
            emb_dim = None
        
        # Assign embeddings: non-empty descriptions get computed embeddings, empty ones get zero vectors
        if emb_dim is not None:
            desc_emb_idx = 0
            for p in params_needing_desc:
                if p in params_empty_desc:
                    # Set to zero vector
                    p._description_embedding = np.zeros(emb_dim)
                else:
                    # Use computed embedding
                    p._description_embedding = desc_embeddings[desc_emb_idx]
                    desc_emb_idx += 1
    
    # Also compute legacy embedding for backward compatibility
    params_needing_legacy = [p for p in parameters if p._embedding is None]
    if params_needing_legacy:
        legacy_texts = [str(p) for p in params_needing_legacy]
        legacy_embeddings = []
        for i in range(0, len(legacy_texts), batch_size):
            batch = legacy_texts[i:i + batch_size]
            batch_embeddings = LLMClient.encode(batch, disable_progress_bar=True)
            legacy_embeddings.extend(batch_embeddings)
        
        for param, emb in zip(params_needing_legacy, legacy_embeddings):
            param._embedding = emb


def batch_get_user_provided(parameters: list[Parameter], param_to_tool_map: dict[Parameter, Tool] = None, batch_size: int = 32, max_retry: int = 3) -> None:
    """
    Batch-inference and check user-provided for a list of Parameter.
    
    Args:
        parameters: List of Parameter objects to check
        param_to_tool_map: Optional mapping from Parameter to Tool. If provided, tool descriptions will be included in the prompt.
        batch_size: Batch size for LLM inference
        max_retry: Maximum retry attempts for each batch
    """
    params = [p for p in parameters if p._user_provided is None]

    for i in tqdm(range(0, len(params), batch_size), desc="Getting user_provided using LLM..."):
        batch = params[i:i + batch_size]
        
        # Build parameter text with tool association if available
        text_lines = []
        for idx, param in enumerate(batch):
            param_line = f"{idx}: {param.name} ({param.data_type}): {param.description}"
            if param_to_tool_map and param in param_to_tool_map:
                tool = param_to_tool_map[param]
                param_line += f" [Tool: {tool.name}]"
            text_lines.append(param_line)
        text = "\n".join(text_lines)
        
        # Get tool context for this batch
        batch_tool_context = ""
        if param_to_tool_map:
            batch_tools = set()
            for param in batch:
                if param in param_to_tool_map:
                    batch_tools.add(param_to_tool_map[param])
            
            if batch_tools:
                batch_tool_context = "### Tool Context\n"
                batch_tool_context += "The following tools are relevant to the parameters below. Use the tool descriptions to better understand the context and purpose of each parameter:\n\n"
                for tool in batch_tools:
                    batch_tool_context += f"**Tool: {tool.name}**\n"
                    batch_tool_context += f"Description: {tool.description}\n"
                    batch_tool_context += f"Server: {tool.server}\n\n"
        
        prompt = Get_User_Provided_Prompt.format(tool_context=batch_tool_context, text=text)
        
        batch_success = False
        for attempt in range(max_retry):
            try:
                output = LLMClient.inference(prompts=prompt, disable_progress_bar=True)[0]
                
                # Check if API call failed (returned None)
                if output is None:
                    # Treat API failure as retryable error
                    if attempt < max_retry - 1:
                        # Retry the API call
                        continue
                    else:
                        # All retries exhausted, skip this batch and continue with next
                        print(f"Warning: API call failed for batch starting at index {i} after {max_retry} attempts. Skipping this batch.")
                        break
                
                output_json = to_JSON(output)
                
                # Validate that output_json is a dict
                if not isinstance(output_json, dict):
                    raise ValueError(f"Expected dict from to_JSON, got {type(output_json)}: {output_json}")

                # Validate output
                assert len(output_json) == len(batch), "Output dict length should match the number of inputs"
                for idx, value in output_json.items():
                    assert int(idx) >= 0 and int(idx) < len(batch), f"Invalid range for {idx}"
                    assert isinstance(value, bool), f"Invalid type for {value}"

                # Assign value
                for idx, value in output_json.items():
                    batch[int(idx)]._user_provided = value
                batch_success = True
                break
            except (RuntimeError, ValueError) as e:
                # Check if it's an authentication error (non-retryable)
                error_str = str(e).lower()
                if "authentication" in error_str or "401" in error_str or "api key" in error_str or "invalid" in error_str:
                    raise RuntimeError(f"Authentication failed. Please check your API credentials. Original error: {e}") from e
                # For other RuntimeError/ValueError, check if it's a retryable API failure
                if "api call failed" in error_str.lower() or "returned none" in error_str.lower():
                    # This is a retryable API failure
                    if attempt < max_retry - 1:
                        continue
                    else:
                        print(f"Warning: API call failed for batch starting at index {i} after {max_retry} attempts. Skipping this batch.")
                        break
                # For other non-retryable RuntimeError/ValueError, don't retry
                raise
            except (AssertionError, KeyError, TypeError) as e:
                # Retryable errors (parsing errors, validation errors that might be fixed by retry)
                if attempt < max_retry - 1:
                    # Add error message to prompt for retry
                    error_msg = f"\n\n# Attempt {attempt + 1} failed. Error: {e}. Please retry."
                    prompt += error_msg
                else:
                    # Last attempt failed, skip this batch and continue with next
                    print(f"Warning: Failed to get user_provided for batch starting at index {i} after {max_retry} attempts. Last error: {e}. Skipping this batch.")
                    break
            except Exception as e:
                # Other unexpected errors
                error_str = str(e).lower()
                if "authentication" in error_str or "401" in error_str or "api key" in error_str:
                    raise RuntimeError(f"Authentication failed. Please check your API credentials. Original error: {e}") from e
                if attempt < max_retry - 1:
                    error_msg = f"\n\n# Attempt {attempt + 1} failed. Error: {e}. Please retry."
                    prompt += error_msg
                else:
                    # Last attempt failed, skip this batch and continue with next
                    print(f"Warning: Unexpected error for batch starting at index {i} after {max_retry} attempts. Last error: {e}. Skipping this batch.")
                    break
        
        # If batch failed after all retries, parameters in this batch will remain with _user_provided = None
        if not batch_success:
            print(f"Note: Batch starting at index {i} was not processed. Parameters in this batch still have _user_provided = None.")