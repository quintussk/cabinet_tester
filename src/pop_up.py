import asyncio
from datetime import datetime, timedelta

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from textual import events

import logging

logging.getLogger(__name__)
logger = logging.getLogger(__name__)

class Prompt(ModalScreen[bool]):
    CSS_PATH = "prompt.tcss"

    def __init__(self, title: str, prompt: str, duration: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self.title = title
        self.prompt = prompt
        self.true_false = "False"
        self.timer_label = None
        self.end_time = datetime.now() + timedelta(seconds=duration)
        self.timer_task = None
        self.result = asyncio.Future()

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(self.title, id="title")
            yield Label(self.prompt, id="question")
            yield Static("", id="timer")  # Timer label
            yield Static(self.true_false, id="response")

    async def on_mount(self) -> None:
        self.timer_label = self.query_one("#timer", Static)
        self.timer_task = self.set_interval(1, self.update_timer)
        self.response_container = self.query_one("#response", Static)
        self.updateContainer(False,False)
        self.update_timer()

    def update_timer(self) -> None:
        remaining_time = self.end_time - datetime.now()
        if remaining_time.total_seconds() <= 0:
            pass
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

    def updateContainer(self, state, state_2) -> None:
        if state:
            self.response_container.update("True")
            self.response_container.styles.background = "green"
        elif state_2:
            self.response_container.update("                Keep the probe on the terminal!                          .          Checking other connectors to this terminal")
            self.response_container.styles.background = "orange"
        else:
            self.response_container.update("False")
            self.response_container.styles.background = "red"

    def update_container_color(self, color: str) -> None:
        """Method to update the container color from outside the class."""
        container = self.query_one(Container)
        container.styles.background = color

class HasPrompt:
    async def prompt(self, title: str, prompt: str, duration: int):
        self.prompt_instance = Prompt(title=title, prompt=prompt, duration=duration)
        await self.push_screen(self.prompt_instance)

    async def push_screen(self, *args, **kwargs):
        raise NotImplementedError
    
    async def updateconatiner(self, state, state_2):
        self.prompt_instance.updateContainer(state,state_2)

    async def dismiss(self):
        await self.prompt_instance.dismiss()