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

import board
import busio
import adafruit_mcp230xx.mcp23017 as MCP
from digitalio import Direction, Pull
import time

logging.getLogger(__name__)
logger = logging.getLogger(__name__)

class RunTest(BaseTest):
    async def run(self, test, test_data_path):
        i2c = busio.I2C(board.SCL, board.SDA)
        mcps = {
            27: MCP.MCP23017(i2c, address=0x27),
            26: MCP.MCP23017(i2c, address=0x26),
            25: MCP.MCP23017(i2c, address=0x25),
            24: MCP.MCP23017(i2c, address=0x24),
            23: MCP.MCP23017(i2c, address=0x23),
            22: MCP.MCP23017(i2c, address=0x22),
            21: MCP.MCP23017(i2c, address=0x21),
        }
        
        input_pin = mcps[26].get_pin(0)
        input_pin.direction = Direction.INPUT
        
        self.title = test
        logger.debug(f"De te testen test is {test}")
        
        # Open the JSON file with test data
        with open(test_data_path, 'r') as file:
            test_data = json.load(file)
        
        # Open JSON files for component answers and IO configurations
        json_data_file_path = Path(__file__).parent.parent / "test_results/testing_components_answers.json"
        json_io_path = Path(__file__).parent / "IOLIST.json"
        with open(json_data_file_path, 'r') as file:
            data = json.load(file)
        with open(json_io_path, 'r') as file:
            data_io = json.load(file)
        
        if test in data:
            connector = data[test]  # Terminals connected to the test
            connected_io = data_io.get(test, [])  # I/O configuration for the connector
            logger.debug(f"Connected IO: {connected_io}")
            
            # Loop through each terminal for the specified connector
            for terminal in connector:

                from_terminal = terminal.get('from_terminal')
                to_part = terminal.get('to_part')
                to_mark = terminal.get('to_mark')
                to_terminal = terminal.get('to_terminal')
                
                # Match from_terminal to Conector_pin in connected_io to get mcp_adress and mcp_pin
                # Normalize `from_terminal` to ensure it's an integer regardless of format
                if isinstance(from_terminal, str) and from_terminal.startswith("pin "):
                    from_terminal = int(from_terminal.split(" ")[1])
                elif isinstance(from_terminal, str) and from_terminal.isdigit():
                    from_terminal = int(from_terminal)
                elif isinstance(from_terminal, int):
                    # Already an integer, no conversion needed
                    pass

                # Now perform the matching
                matching_io = next((io for io in connected_io if io.get("Conector_pin") == from_terminal), None)

                if matching_io:
                    mcp_adress = int(matching_io['mcp_adress'])
                    mcp_pin = int(matching_io['mcp_pin'])  # Convert pin to integer (hex support)
                
                    # Ensure from_terminal is a string for consistency in test_data
                    if isinstance(from_terminal, int):
                        from_terminal = str(from_terminal)
                    
                    # Skip if already passed
                    already_passed = any(
                        result['terminal'] == from_terminal and result['passed'] 
                        for result in test_data.get("test_results", {}).get(test, [])
                    )
                    if already_passed:
                        logger.debug(f"Terminal {from_terminal} already passed, skipping...")
                        continue

                    # Skip if to_mark or to_part is NaN
                    if (isinstance(to_mark, float) and math.isnan(to_mark)) or (isinstance(to_part, float) and math.isnan(to_part)):
                        continue

                    # Create a prompt instance
                    prompt_instance = Prompt(f"Test: mark: {to_mark} ({to_part}), terminal: {to_terminal} ", 30)
                    await self.app.push_screen(prompt_instance)

                    # Simulate a test with a delay
                    start_time = asyncio.get_event_loop().time()

                    while True:
                        current_time = asyncio.get_event_loop().time()
                        elapsed_time = current_time - start_time

                        output_pin = mcps[mcp_adress].get_pin(mcp_pin)
                        output_pin.direction = Direction.OUTPUT
                        output_pin.value = True

                        if input_pin.value:
                            output_pin.value = False
                            output_pin.direction = Direction.INPUT
                            prompt_instance.updateContainer(True)
                            self.add_result(from_terminal, True, to_mark, to_terminal)
                            break
                        
                        if elapsed_time >= 30:
                            output_pin.value = False
                            self.add_result(from_terminal, False, to_mark, to_terminal)
                            break

                        await asyncio.sleep(0.5)

                    await asyncio.sleep(2)
                    await prompt_instance.dismiss()

                    logger.debug(f"From terminal: {from_terminal}, To part: {to_part}, To mark: {to_mark}, To terminal: {to_terminal}")
            
            # Save updated results after processing all terminals
            self.save_results_to_json(test_data_path)
        else:
            logger.debug(f"Test '{test}' not found in the JSON.")

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
