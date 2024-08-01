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
        yield Label(f"Schema Keuze: {self.totest}", classes="Labels")
        yield rich_log_handler.console
        yield Footer()

    def on_load(self) -> None:
        """Load the app.""" 
        self.bind("q", "quit", description="Quit")
        self.bind("d", "toggle_dark", description="Toggle mode")
    
    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

