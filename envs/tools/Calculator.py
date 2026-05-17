
import math
from pydantic import BaseModel
from typing import Dict, List, Any
from mcp.server.fastmcp import FastMCP


class CalculatorScenario(BaseModel):
    """Main scenario model for calculator state."""
    history: List[Dict[str, Any]] = []

Scenario_Schema = [CalculatorScenario]


class CalculatorAPI:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []

    def load_scenario(self, scenario: dict) -> None:
        model = CalculatorScenario(**scenario)
        for entry in model.history:
            expression = entry.get("expression")
            if not isinstance(expression, str) or not expression:
                raise ValueError("Expression must be a non-empty string")
        self.history = model.history

    def save_scenario(self) -> dict:
        return {"history": self.history}

    def calculate(self, expression: str) -> dict:
        safe_globals = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
        safe_globals["__builtins__"] = {}
        result = eval(expression, safe_globals)  # noqa: S307
        entry = {"expression": expression, "result": result}
        self.history.append(entry)
        return entry


mcp = FastMCP(name="Calculator")
api = CalculatorAPI()


@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the calculator API."""
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        api.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e


@mcp.tool()
def save_scenario() -> dict:
    """Save current calculator state as scenario dictionary."""
    try:
        return api.save_scenario()
    except Exception as e:
        raise e


@mcp.tool()
def calculate(expression: str) -> dict:
    """
    Evaluate a mathematical expression and return the result.

    Args:
        expression (str): The mathematical expression to evaluate, e.g. "2 + 3 * 4", "sqrt(16)", or "sin(pi / 4)".
    """
    try:
        if not expression or not isinstance(expression, str):
            raise ValueError("Expression must be a non-empty string")
        return api.calculate(expression)
    except Exception as e:
        return {"expression": expression, "error": str(e)}


if __name__ == "__main__":
    mcp.run()
