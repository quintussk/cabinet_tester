from tkinter import VERTICAL
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Input, Button, Footer, Header, Static, Label, Checkbox, Switch, ListItem, ListView, RichLog
from textual import on, events
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.screen import Screen
import json
from pathlib import Path
from textual.reactive import Reactive
import logging
from rich.logging import RichHandler
from textual.logging import TextualHandler
import atexit

from Tester import TestScreen

class LoggingConsole(RichLog):
    file = False
    console: Widget

    def print(self, content):
        self.write(content)

logger = logging.getLogger()
rich_log_handler = RichHandler(
    console=LoggingConsole(),  # type: ignore
    rich_tracebacks=True,
)
logger.addHandler(rich_log_handler)
logger.addHandler(TextualHandler())
logger.setLevel(logging.DEBUG)
atexit.register(logger.removeHandler, rich_log_handler)

testers = [
    ("S25", "infoS25"),
    ("E25", "infoE25"),
    ("E25_Belotti", "infoS25"),
    ("F25", "infoE25"),
    ("G25", "infoS25"),
    ("E40", "infoE25"),
    ("G40", "infoE25"),
    ("E50", "infoE25")
]    


class OptionListApp(App[None]):
    CSS_PATH = "main.tcss"
    TITLE = "Electrical cabinet tester"
    SUB_TITLE = "V1"
    selected_label = ""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Vertical(
                Label("Schema Keuze:", classes="Labels"),
                ListView(
                    *[ListItem(Label(tester[0]), id=tester[0]) for tester in testers],
                    classes="keuze")
                ),
                id="start_screen",
            )
        yield Button(f"Start {self.selected_label}", variant="success", id="start", classes="button_start")
        yield rich_log_handler.console
        yield Footer()
        
    def on_load(self) -> None:
        """Load the app.""" 
        self.bind("q", "quit", description="Quit")
        self.bind("d", "toggle_dark", description="Toggle mode")
    
    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    @on(ListView.Highlighted)
    async def on_item_focus(self, event: ListView.Highlighted) -> None:
        self.selected_label = event.item.id
        logger.debug(f"Geselecteerde schema: {self.selected_label}")
        self.compose()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            # self.push_screen(AantalMensen())
            self.push_screen(TestScreen(totest = self.selected_label))

if __name__ == "__main__":
    OptionListApp().run()
