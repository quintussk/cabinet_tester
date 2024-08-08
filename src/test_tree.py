import logging
from enum import Enum
from pathlib import Path
from rich.progress import BarColumn, Progress
import asyncio
from textual.containers import Container, Horizontal
from run_test import RunTest

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Tree, Button
import json
from textual import on
from utils import read_css

logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    PASS = "✅"
    FAIL = "❌"
    MISSING = "⚪"
    
class TestTree(Container):
    _CSS_PATH = str(Path(__file__).with_suffix(".css"))
    DEFAULT_CSS = read_css(_CSS_PATH)
    selected_node = ""

    def __init__(self):
        super().__init__()
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

        with Horizontal(classes="horizon"):
            yield Button("Run_test", id="run_test", disabled=True, variant="default")


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
    async def runtesti(self, event: Button.Pressed) -> None:
        logger.debug(self.selected_node)
        logger.debug(self.app)
        tester = RunTest(app=self.app)
        await tester.run(self.selected_node, self.json_file)
        self.redraw()


    def redraw(self):       
        parent = self.parent
        self.remove()
        parent.mount(TestTree())
