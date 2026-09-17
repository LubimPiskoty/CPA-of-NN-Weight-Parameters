"""
Configuration for capture.py
"""

# ChipWhisperer target platform (e.g. CWLITEARM, CWLITEXMEGA, CW308_STM32F3)
PLATFORM = "CWLITEARM"

# Path to compiled firmware .hex file
FW_PATH = "../firmware/cpa-firmware-CWLITEARM.hex"

# Programmer type: "stm32f", "xmega", or "avr"
PROGRAMMER = "stm32f"

# Number of traces to capture
NUM_TRACES = 10_000

# Random input range fed to the network (uniform distribution)
INPUT_LOW = -2.0
INPUT_HIGH = 2.0

# RNG seed for reproducibility
SEED = 42

# Directory to save captured traces
OUT_DIR = "../data/raw/"

# Skip flashing the target (set True if already programmed)
SKIP_FLASH = False

PROJECT_NAME = "../data/raw/CPA_NN"
