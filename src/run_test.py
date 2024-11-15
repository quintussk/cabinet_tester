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
    async def run(self, test, test_data_path, test_time):
        i2c = busio.I2C(board.SCL, board.SDA)
        mcps = {
            
            26: MCP.MCP23017(i2c, address=0x26),
            25: MCP.MCP23017(i2c, address=0x25),
            24: MCP.MCP23017(i2c, address=0x24),
            23: MCP.MCP23017(i2c, address=0x23),
            22: MCP.MCP23017(i2c, address=0x22),
            21: MCP.MCP23017(i2c, address=0x21),
            27: MCP.MCP23017(i2c, address=0x27),
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
                    await self.app.prompt(title=f"Testing; {test} connector" ,prompt=f"Mark: {to_mark} ({to_part}); terminal: {to_terminal} ", duration=test_time)
                    # prompt_instance = Prompt(title=f"Testing; {test} connector" ,prompt=f"Mark: {to_mark} ({to_part}); terminal: {to_terminal} ", duration=test_time)
                    # await self.app.push_screen(prompt_instance)

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
                            await self.app.updateconatiner(True,False)
                            self.add_result(from_terminal, True, to_mark, to_terminal)
                            break
                        
                        if elapsed_time >= test_time:
                            output_pin.value = False
                            output_pin.direction = Direction.INPUT
                            await self.app.updateconatiner(False,True)
                            mcp_address, pin_number = await self.test_different_components(tested_mark=to_mark, tested_terminal=to_terminal, mcps=mcps, input_pin=input_pin)
                            logger.debug(f"Returned mcp_address: {mcp_address}, pin_number: {pin_number}")
                            if mcp_address is not None:
                                gevonden_details = self.zoek_connector(data_io, mcp_address, pin_number)
                                logger.debug(f"Verbonden component: {gevonden_details}")
                                self.add_result_different_terminal(from_terminal, False, gevonden_details)
                            else:
                                self.add_result(from_terminal, False, to_mark, to_terminal)
                            
                            break

                        await asyncio.sleep(0.5)

                    await asyncio.sleep(2)
                    await self.app.dismiss()

                    logger.debug(f"From terminal: {from_terminal}, To part: {to_part}, To mark: {to_mark}, To terminal: {to_terminal}")
            
            # Save updated results after processing all terminals
            self.save_results_to_json(test_data_path)
        else:
            logger.debug(f"Test '{test}' not found in the JSON.")

    def zoek_connector(self,data_io, mcp_address, mcp_pin):
        """
        Zoek de connector details op basis van MCP-adres en pin-nummer.

        Parameters:
            data_io (dict): De JSON data met IO informatie.
            mcp_address (int): Het MCP-adres.
            mcp_pin (int): Het pin-nummer op de MCP.

        Returns:
            dict: Gevonden details met 'Connector' en 'Conector_pin', of None als niets wordt gevonden.
        """
        for connector, pins in data_io.items():
            for pin in pins:
                if int(pin['mcp_adress']) == mcp_address and int(pin['mcp_pin']) == mcp_pin:
                    return {"Connector": connector, "Conector_pin": pin['Conector_pin']}
        return None



    async def test_different_components(self, tested_mark, tested_terminal, mcps, input_pin):
        logger.debug(f"Starten met het testen van andere componenten voor mark: {tested_mark}, terminal: {tested_terminal}"), 

        # Loop door alle MCP modules
        logger.debug("Looping door alle MCP modules")
        logger.debug(f"mcps: {mcps}")
        logger.debug(f"mcp: {mcps.items()}")
        for mcp_address, mcp in mcps.items():
            logger.debug(f"Controleren MCP module op adres {mcp_address}")
            for pin_number in range(16):  # MCP23017 heeft 16 pinnen
                if mcp_address == 26 and pin_number == 0:
                    continue
                test_pin = mcp.get_pin(pin_number)
                test_pin.direction = Direction.OUTPUT
                
                # Zet de pin hoog
                test_pin.value = True
                await asyncio.sleep(0.1)  # Kleine vertraging om het signaal te stabiliseren
                
                # Controleer de input
                if input_pin.value:
                    logger.debug(f"Verbonden component gevonden op MCP {mcp_address}, pin {pin_number}")
                    
                    # Zet pin weer laag
                    test_pin.value = False
                    test_pin.direction = Direction.INPUT
                    
                    # Return de gevonden verbinding en stop de test
                    return mcp_address, pin_number

                # Zet pin weer laag
                test_pin.value = False
                test_pin.direction = Direction.INPUT

        logger.debug("Geen andere verbonden componenten gevonden")
        return None, None

# Rest van je script blijft hetzelfde

# Hieronder je Prompt en MyScreen classes (die blijven ongewijzigd)