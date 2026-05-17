import json
import logging
import asyncio
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('log.log'), logging.StreamHandler()]
)

class StructuredLogger:
    def __init__(self, log_folder: str = "log"):
        self.log_folder = log_folder
        self.logs = {}
        self.logger = logging.getLogger(__name__)
        self.lock = asyncio.Lock()

        Path(self.log_folder).mkdir(parents=True, exist_ok=True)

    async def add_log(self, conversation_id: str, idx: int, content: dict) -> None:
        """Asynchronously add log entry with concurrency protection"""
        async with self.lock:
            if conversation_id not in self.logs:
                self.logs[conversation_id] = {}
            
            if idx not in self.logs[conversation_id]:
                self.logs[conversation_id][idx] = []
            
            self.logs[conversation_id][idx].append(content)

    def dump_log(self, conversation_id: str, log_name: str, overwrite: bool = False) -> bool:
        """
        Dump logs for a conversation to a JSON file.

        Args:
            conversation_id (str): The unique identifier of the conversation whose logs should be dumped.
            log_name (str): The filename for the output JSON file.
            overwrite (bool): If True, overwrite the existing file. If False, merge with existing data (update if dict, append if list).
        """
        if conversation_id not in self.logs:
            self.logger.debug(f"No logs found for conversation {conversation_id}.")
            return False
        
        # Prepare log data
        log_data = self.logs.pop(conversation_id)
        
        # Build output path
        output_path = Path(self.log_folder) / log_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Determine output data structure
            if not overwrite and output_path.exists():
                # Read and merge with existing
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                
                if isinstance(existing_data, dict):
                    existing_data.update(log_data)  # Merge dicts
                    output_data = existing_data
                elif isinstance(existing_data, list):
                    existing_data.append(log_data)  # Append to list
                    output_data = existing_data
                else:
                    output_data = [existing_data, log_data] # Wrap scalar/other types
            else:
                output_data = log_data
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=True, indent=2)
            
            self.logger.info(f"Dumped logs for '{conversation_id}' to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to dump logs for '{conversation_id}': {e}")
            self.logs[conversation_id] = log_data  # Restore on failure
            return False
