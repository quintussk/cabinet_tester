import json
from pathlib import Path
import logging
import asyncio
from datetime import datetime, timedelta
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Label, Static
from textual import events
import math

from utils import BaseTest, SubTest

logging.getLogger(__name__)
logger = logging.getLogger(__name__)

class RunTest(BaseTest):
    async def run(self, test, test_data_path):
        self.title = test
        logger.debug(f"De te testen test is {test}")
        
        # Openen van de JSON file met test data
        with open(test_data_path, 'r') as file:
            test_data = json.load(file)
        
        # Openen van JSON file met component antwoorden
        json_file_path = Path(__file__).parent.parent / "test_results/testing_components_answers.json"
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        
        if test in data:
            terminals = data[test]
            # Terminals een voor een doorlopen
            for terminal in terminals:
                Test = False

                    
                from_terminal = terminal.get('from_terminal')
                to_part = terminal.get('to_part')
                to_mark = terminal.get('to_mark')
                to_terminal = terminal.get('to_terminal')
                
                if isinstance(from_terminal, int):
                    from_terminal = str(from_terminal)
                # Controleer of de terminal al geslaagd is in de test_data
                already_passed = any(
                    result['terminal'] == from_terminal and result['passed'] 
                    for result in test_data.get("test_results", {}).get(test, [])
                )
                
                if already_passed:
                    logger.debug(f"Terminal {from_terminal} al geslaagd, overslaan...")
                    continue

                if (isinstance(to_mark, float) and math.isnan(to_mark)) or (isinstance(to_part, float) and math.isnan(to_part)):
                    continue

                # Maak een prompt en bewaar de instantie
                prompt_instance = Prompt(f"Test: mark: {to_mark}({to_part}), terminal: {to_terminal}", 10)
                await self.app.push_screen(prompt_instance)

                # Simulatie van een test met een delay
                start_time = asyncio.get_event_loop().time()

                while True:
                    current_time = asyncio.get_event_loop().time()
                    elapsed_time = current_time - start_time
                    
                    if elapsed_time >= 2:
                        Test = True

                    if Test:
                        prompt_instance.updateContainer(True)
                        self.add_result(from_terminal, True, to_mark, to_terminal)
                        break
                    
                    await asyncio.sleep(0.5)

                await asyncio.sleep(2)
                await prompt_instance.dismiss()

                logger.debug(f"From terminal: {from_terminal}, To part: {to_part}, To mark: {to_mark}, To terminal: {to_terminal}")
            
            # Sla de bijgewerkte resultaten op na het doorlopen van alle terminals
            self.save_results_to_json(test_data_path)
        else:
            logger.debug(f"Test '{test}' niet gevonden in de JSON.")

# Rest van je script blijft hetzelfde

# Hieronder je Prompt en MyScreen classes (die blijven ongewijzigd)

class Prompt(ModalScreen[bool]):
    DEFAULT_CSS = """
    Prompt {
        align: center middle;
    }

    Prompt > Container {
        width: 70;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }

    Prompt > Container > Label {
        width: 100%;
        content-align-horizontal: center;
        margin-top: 1;
    }

    Prompt > Container > Static#timer {
        content-align-horizontal: center;
        margin-top: 1;
        color: red;
    }

    Prompt > Container > Static#response {
        width: 100%;
        height: 3;
        content-align-horizontal: center;
        content-align-vertical: middle;
        margin-top: 1;
    }
    """

    def __init__(self, prompt: str, duration: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self.prompt = prompt
        self.true_false = "False"
        self.timer_label = None
        self.end_time = datetime.now() + timedelta(seconds=duration)
        self.timer_task = None
        self.result = asyncio.Future()

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(self.prompt, id="question")
            yield Static("", id="timer")  # Timer label
            yield Static(self.true_false, id="response")

    async def on_mount(self) -> None:
        self.timer_label = self.query_one("#timer", Static)
        self.timer_task = self.set_interval(1, self.update_timer)
        self.response_container = self.query_one("#response", Static)
        self.updateContainer(False)
        self.update_timer()

    def update_timer(self) -> None:
        remaining_time = self.end_time - datetime.now()
        if remaining_time.total_seconds() <= 0:
            self.dismiss(False)
        else:
            self.timer_label.update(f"Time left: {int(remaining_time.total_seconds())}s")

    async def on_key(self, event: events.Key) -> None:
        if event.key == "y":
            self.updateContainer(True)
            self.dismiss(True)
        elif event.key == "n":
            self.updateContainer(False)
            self.dismiss(False)

    async def on_dismiss(self, result: bool = False) -> None:
        if self.timer_task:
            self.timer_task.cancel()
        if not self.result.done():
            self.result.set_result(result)

    def updateContainer(self, state) -> None:
        if state:
            self.response_container.update("True")
            self.response_container.styles.background = "green"
        else:
            self.response_container.update("False")
            self.response_container.styles.background = "red"

    def update_container_color(self, color: str) -> None:
        """Method to update the container color from outside the class."""
        container = self.query_one(Container)
        container.styles.background = color

class HasPrompt:
    async def prompt(self, prompt: str, duration: int) -> bool:
        prompt_instance = Prompt(prompt, duration)
        await self.push_screen(prompt_instance)
        return await prompt_instance.result

    async def push_screen(self, *args, **kwargs):
        raise NotImplementedError

if __name__ == "__main__":
    from textual import on
    from textual.screen import Screen
    from textual.widgets import Button, Header, Static

    class MyScreen(Screen):
        def compose(self) -> ComposeResult:
            yield Header()
            yield Button("Run Test", id="run_test")
            yield Static(id="result")

        async def on_key(self, event: events.Key) -> None:
            prompt_screen = self.app.screen_stack[-1]
            if isinstance(prompt_screen, Prompt):
                await prompt_screen.on_key(event)

        @on(Button.Pressed, "#run_test")
        async def on_run_test_pressed(self, event: Button.Pressed) -> None:
            self.json_file = Path(__file__).parent.parent / "test_results/test_results.json"
            tester = RunTest(app=self.app)
            await tester.run("10CON1", self.json_file)

    class MyApp(App, HasPrompt):  # MyApp now has a 'prompt' method via HasPrompt trait
        def compose(self) -> ComposeResult:
            yield MyScreen()

    app = MyApp()
    app.run()
