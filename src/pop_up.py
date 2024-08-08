import asyncio
from datetime import datetime, timedelta

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

import logging

logging.getLogger(__name__)
logger = logging.getLogger(__name__)

class Prompt(ModalScreen[bool]):
    DEFAULT_CSS = """
    Prompt {
        align: center middle;
    }

    Prompt > Container {
        width: 50;
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

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.true_false = "True"
            self.updateContainer(True)
            self.response_container.update(self.true_false)
        elif event.button.id == "no":
            self.true_false = "False"
            self.updateContainer(False)
            self.response_container.update(self.true_false)

    async def on_dismiss(self) -> None:
        if self.timer_task:
            self.timer_task.cancel()

    def updateContainer(self, state) -> None:
        if state:
            self.response_container.styles.background = "green"
        else:
            self.response_container.styles.background = "red"

class HasPrompt:
    async def prompt(self, prompt: str, duration: int) -> bool:
        event = asyncio.Event()
        result = None

        def check_result(prompt_response: bool) -> None:
            nonlocal result
            nonlocal event
            result = prompt_response
            event.set()

        await asyncio.gather(
            self.push_screen(Prompt(prompt, duration), check_result),
            event.wait(),
        )

        if result is None:
            raise RuntimeError("Prompt was dismissed without a result")
        return result

    async def push_screen(self, *args, **kwargs):
        raise NotImplementedError

if __name__ == "__main__":
    from textual import on
    from textual.screen import Screen
    from textual.widgets import Button, Header, Static

    class MyScreen(Screen):
        def compose(self) -> ComposeResult:
            yield Header()
            yield Button("Prompt", id="prompt")
            yield Static(id="result")

        @on(Button.Pressed, "#prompt")
        async def on_prompt_pressed(self, event: Button.Pressed) -> None:
            result_widget = self.query_one("#result", Static)
            await self.app.prompt("Do you agree?", 10)  # Geeft de prompttekst en duur (in seconden)

    class MyApp(App, HasPrompt):  # MyApp now has a 'prompt' method via HasPrompt trait
        def compose(self) -> ComposeResult:
            yield MyScreen()

    app = MyApp()
    MyApp().run()
