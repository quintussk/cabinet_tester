from pathlib import Path
from pydantic import BaseModel, Field
from typing import ClassVar, List
from textual.app import App
import json

def read_css(path: str) -> str:
    with Path(path).open() as f:
        return f.read()

class SubTest(BaseModel):
    title: str = ""
    terminal: str = ""
    passes: bool = False
    answer: str = ""

class BaseTest(BaseModel, arbitrary_types_allowed=True):
    title: str = ""
    description: str = ""
    passes: bool = False
    results: List[SubTest] = []
    app: App | None = Field(
        None,
        exclude=True,
    )
    
    def add_result(self, terminal, passes: bool, to_mark, to_terminal):
        """Voegt een testresultaat toe aan de resultatenlijst."""
        subtest = SubTest(
            title=f"Test for terminal {terminal}",
            terminal=terminal,
            passes=passes,
            answer=f"Should go to mark: {to_mark} and terminal {to_terminal}"
        )
        self.results.append(subtest)

    def add_result_different_terminal(self, terminal, passes: bool, gevonden_details):
        """Voegt een testresultaat toe aan de resultatenlijst."""
        conector = gevonden_details["Connector"]
        conector_pin = gevonden_details["Conector_pin"]
        subtest = SubTest(
            title=f"Test for terminal {terminal}",
            terminal=terminal,
            passes=passes,
            answer=f"Different kabel connected to this terminal, kabel from connector {conector} with pin {conector_pin} is connected" 
        )
        self.results.append(subtest)

    def save_results_to_json(self, json_file_path: Path):
        """Slaat de resultaten op in een JSON-bestand en werkt bestaande terminals bij."""
        if not json_file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")

        with open(json_file_path, 'r') as file:
            data = json.load(file)

        if self.title not in data["test_results"]:
            data["test_results"][self.title] = []

        existing_terminals = {result['terminal']: result for result in data["test_results"][self.title]}

        for result in self.results:
            if result.terminal in existing_terminals:
                # Update het bestaande resultaat
                existing_terminals[result.terminal]['passed'] = result.passes
                existing_terminals[result.terminal]['answer'] = result.answer
            else:
                # Voeg een nieuw resultaat toe
                data["test_results"][self.title].append({
                    "terminal": result.terminal,
                    "passed": result.passes,
                    "answer": result.answer
                })

        with open(json_file_path, 'w') as file:
            json.dump(data, file, indent=4)

    async def prompt(self, title: str,  prompt: str, duration: int):
        await self.app.prompt(title=title, prompt=prompt, duration=duration)
