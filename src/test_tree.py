import logging
from enum import Enum
from pathlib import Path
from rich.progress import BarColumn, Progress
import asyncio
from textual.containers import Container, Horizontal
from run_test import RunTest

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Tree, Button, Static
import json
from textual import on
from utils import read_css
from create_test_project import CreateProject  # Zorg ervoor dat je deze import toevoegt

logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    PASS = "✅"
    FAIL = "❌"
    MISSING = "⚪"
    
class TestTree(Container):
    # CSS_PATH = "test_tree.tcss"
    DEFAULT_CSS = ''
    selected_node = ""
    test_time = 30  # Initial test time in seconds

    def __init__(self, testers, selected_scheme):
        super().__init__()
        self.testers = testers
        self.selected_scheme = selected_scheme
        self.json_file = Path(__file__).parent.parent / "test_results/test_results.json"
        self.load_json_data()

    def load_json_data(self):
        with open(self.json_file, "r") as file:
            self.test_data = json.load(file)
            self.cabinet_name = self.test_data.get("cabinet_name", "Unknown Cabinet")
            self.test_results = self.test_data.get("test_results", {})

    def compose(self) -> ComposeResult:
        tree: Tree[dict] = Tree(self.cabinet_name)
        tree.root.expand()

        for test_name, results in self.test_results.items():
            if not results:
                # Als er geen resultaten zijn, markeer als MISSING
                parent_status = TestStatus.MISSING.value
            else:
                # Controleer of alle tests in dit hoofdstuk geslaagd zijn
                all_passed = all(result['passed'] for result in results)
                parent_status = TestStatus.PASS.value if all_passed else TestStatus.FAIL.value

            # Voeg de parent node toe met de juiste status
            parent_node = tree.root.add(f"{parent_status} {test_name}", data=test_name)
            
            for result in results:
                status = TestStatus.PASS.value if result['passed'] else TestStatus.FAIL.value
                leaf_node = parent_node.add_leaf(f"{status} Terminal {result['terminal']}", data=result)
                
                # Als de test niet is geslaagd, voeg dan een extra leaf toe met het juiste antwoord
                if not result['passed']:
                    leaf_node.expand()
                    leaf_node.add_leaf(f"{result['answer']}", data=result['answer'])

        yield tree

        yield Horizontal(
            Horizontal(
                Button("Run_test", id="run_test", disabled=True, variant="default"),
                Button("Clear project", id="clear_project", variant="warning"),
                id="left-buttons"
            ),
            Horizontal(
                Button("+ 5s", id="plus"),
                Button("- 5s", id="minus"),
                Static(f"Test time: {self.test_time}s", id="test_time"),
                id="right-buttons"
            ),
            id="horizontal_tree"
        )

    @on(Tree.NodeHighlighted)
    async def on_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        logger.debug(event.node)
        self.selected_node = event.node.data
        button_test = self.query_one("#run_test")
        if event.node.parent is not None:
            button_test.disabled = False
            button_test.variant = "success"
        else:
            button_test.disabled = True
            button_test.variant = "default"

    @on(Button.Pressed, "#run_test")
    async def runtest(self, event: Button.Pressed) -> None:
        logger.debug(self.selected_node)
        logger.debug(self.app)
        tester = RunTest(app=self.app)
        await tester.run(self.selected_node, self.json_file,test_time=self.test_time)
        self.redraw()

    @on(Button.Pressed, "#clear_project")
    async def clear_project(self, event: Button.Pressed) -> None:
        if not self.selected_scheme:
            logger.error("No scheme selected")
            return

        # Create a new project based on the selected scheme
        for tester in self.testers:
            if tester[0] == self.selected_scheme:
                selected_file = tester[1]
                logger.debug(f"Bijbehorende bestand: {selected_file}")
                CreateProject().create(selected_file)
                self.redraw()
                break

    @on(Button.Pressed, "#plus")
    async def increase_test_time(self, event: Button.Pressed) -> None:
        self.test_time += 5
        self.update_test_time_display()

    @on(Button.Pressed, "#minus")
    async def decrease_test_time(self, event: Button.Pressed) -> None:
        self.test_time = max(0, self.test_time - 5)  # Prevent negative time
        self.update_test_time_display()

    def update_test_time_display(self):
        test_time_display = self.query_one("#test_time", Static)
        test_time_display.update(f"Test time: {self.test_time}s")

    def redraw(self):       
        parent = self.parent
        self.remove()
        parent.mount(TestTree(testers=self.testers,selected_scheme=self.selected_scheme))