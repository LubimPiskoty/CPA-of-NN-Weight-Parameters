"""
Configuration for capture.py
"""

# ChipWhisperer target platform (e.g. CWLITEARM, CWLITEXMEGA, CW308_STM32F3)
PLATFORM = "CWLITEARM"

# Path to compiled firmware .hex file
FW_PATH = "../firmware/firmware-CWLITEARM.hex"

# Programmer type: "stm32f", "xmega", or "avr"
PROGRAMMER = "stm32f"

# Number of traces to capture
NUM_TRACES = 20_000

# Random input range fed to the network (uniform distribution)
INPUT_LOW = -1.0
INPUT_HIGH = 1.0

# Random weight range fed to the network (uniform distribution)
WEIGHT_LOW = -1.0
WEIGHT_HIGH = 1.0
TRACES_PER_WEIGHT = 500

# RNG seed for reproducibility
SEED = 148

# Directory to save captured traces
OUT_DIR = "../data/raw/"

# Skip flashing the target (set True if already programmed)
SKIP_FLASH = False

PROJECT_NAME = "../data/raw/cw_project"
