from tkinter import VERTICAL
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid, VerticalScroll
from textual.widgets import Input, Button, Footer, Header, Static, Label, Checkbox, Switch, ListItem, ListView, RichLog, Placeholder
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

# DIT MOET IN EEN ANDERE SCRIPT LATER
class TestScreen(Screen):
    totest = ""
    CSS_PATH = "tester.tcss"

    def __init__(self, totest: str) -> None:
            super().__init__()
            self.totest = totest

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Container(
                Placeholder("This is a custom label for p1.", id="p1"),
                Placeholder("Placeholder p2 here!", id="p2"),
                Placeholder(id="p3"),
                Placeholder(id="p4"),
                Placeholder(id="p5"),
                Placeholder(),
                Horizontal(
                    Placeholder(variant="size", id="col1"),
                    Placeholder(variant="text", id="col2"),
                    Placeholder(variant="size", id="col3"),
                    id="c1",
                ),
                id="bot",
            ),
            Container(
                Placeholder(variant="text", id="left"),
                Placeholder(variant="size", id="topright"),
                Placeholder(variant="text", id="botright"),
                id="top",
            ),
            id="content",
        )
        yield rich_log_handler.console
        yield Footer()

    def on_load(self) -> None:
        """Load the app.""" 
        self.bind("q", "quit", description="Quit")
        self.bind("d", "toggle_dark", description="Toggle mode")
    
    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()


