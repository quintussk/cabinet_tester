from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Input, Button, Footer, Header, Static, Label, Checkbox, Switch, ListItem, ListView, RichLog, TabbedContent, TabPane
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
from test_tree import TestTree
from create_test_project import CreateProject

from pop_up import HasPrompt

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
    ("S25", "Cable & cabinet assembly list S25.xlsx"),
    ("E25", "Cable & cabinet assembly list E25.xlsx"),
    ("F25", "Cable & cabinet assembly list F25.xlsx"),
    ("E40", "Cable & cabinet assembly list E40 S7-1500 PLC.xlsx"),
    ("G40", "Cable & extruder assembly list G40.xlsx"),
    ("E50", "Cable & cabinet assembly list E50.xlsx")
]    

class Options(Container):
    selected_scheme: Reactive[str] = reactive("S25")

    def __init__(self, selected_scheme):
        super().__init__()
        self.selected_scheme = selected_scheme

    def compose(self) -> ComposeResult:
        yield Label("Electric scheme choice: ")
        yield ListView(
            *[ListItem(Label(f"{tester[0]}  -  {tester[1]}"), id=tester[0]) for tester in testers],
            classes="keuze")
        with Horizontal(id="horizontal_main"):
            yield Button("Change Scheme", id="Change_Scheme", disabled=True, variant="default")
            self.response_static = Static(f"Selected Scheme: {self.selected_scheme}", id="response")
            yield self.response_static

    def update_selected_scheme(self, new_scheme):
        self.selected_scheme = new_scheme
        self.response_static.update(f"Selected Scheme: {self.selected_scheme}")

class CableApp(App[None], HasPrompt):
    CSS_PATH = "main.tcss"
    TITLE = "Electrical cabinet tester"
    SUB_TITLE = "V1"
    selected_label = ""
    selected_scheme = "S25"
    test_time = 30  # Initial test time in seconds

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with TabbedContent(classes="tabs"):
            with TabPane("Electric scheme", id="tab_electric_scheme"):
                self.options_container = Options(selected_scheme=self.selected_scheme)
                yield self.options_container
            with TabPane("Project", id="tab_project"):          
                yield TestTree(testers=testers,selected_scheme=self.selected_scheme)

        yield rich_log_handler.console
        yield Footer()
        
    def on_load(self) -> None:
        self.bind("q", "quit", description="Quit")
        self.bind("d", "toggle_dark", description="Toggle mode")
    
    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    @on(ListView.Highlighted)
    async def on_item_focus(self, event: ListView.Highlighted) -> None:
        self.selected_label = event.item.id
        logger.debug(f"Geselecteerde schema: {self.selected_label}")
        button_test = self.query_one("#Change_Scheme")
        if self.selected_scheme != self.selected_label:
            button_test.disabled = False
            button_test.variant = "success"
        else:
            button_test.disabled = True
            button_test.variant = "default"

    @on(Button.Pressed, "#Change_Scheme")
    async def changescheme(self, event: Button.Pressed) -> None:
        self.selected_scheme = self.selected_label
        for tester in testers:
            if tester[0] == self.selected_label:
                self.selected_file = tester[1]
                logger.debug(f"Bijbehorende bestand: {self.selected_file}")
                CreateProject().create(self.selected_file)
                self.query(TestTree).remove()
                self.options_container.update_selected_scheme(self.selected_scheme)
                self.mount(TestTree(testers=testers,selected_scheme=self.selected_scheme))
        button_test = self.query_one("#Change_Scheme")
        button_test.disabled = True
        button_test.variant = "default"
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            self.push_screen(TestScreen(totest=self.selected_label))

if __name__ == "__main__":
    CableApp().run()
