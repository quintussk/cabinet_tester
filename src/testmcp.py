from digitalio import Direction
import board
import busio

import adafruit_mcp230xx.mcp23017 as MCP

# Set up the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create an MCP23017 object at address 0x27
mcps = {
    27: MCP.MCP23017(i2c, address=0x27),
    26: MCP.MCP23017(i2c, address=0x26),
    25: MCP.MCP23017(i2c, address=0x25),
    24: MCP.MCP23017(i2c, address=0x24),
    23: MCP.MCP23017(i2c, address=0x23),
    22: MCP.MCP23017(i2c, address=0x22),
    21: MCP.MCP23017(i2c, address=0x21),
}

# Configure the MCP23017 outputs as outputs
for i in range(16):
    mcps[27].get_pin(i).direction = Direction.OUTPUT

outputpin = mcps[27].get_pin(0)

outputpin.value = True

