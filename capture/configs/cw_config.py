"""
Configuration for capture.py
"""

# ChipWhisperer target platform (e.g. CWLITEARM, CWLITEXMEGA, CW308_STM32F3)
PLATFORM = "CWLITEARM"

# Firmware source directory (where `make` is run)
FW_DIR = "../firmware"

# Path to compiled firmware .hex file
FW_PATH = "../firmware/firmware-CWLITEARM.hex"

# Programmer type: "stm32f", "xmega", or "avr"
PROGRAMMER = "stm32f"

# Number of traces to capture in each phase (0 skips that phase).
# Profiling: firmware takes the weight from the payload (random, known).
# Attack: firmware uses its fixed ground-truth weights, only the input is sent.
NUM_PROFILING_TRACES = 20_000
NUM_ATTACK_TRACES = 5_000

# Random input range fed to the network (uniform distribution)
INPUT_LOW = -1.0
INPUT_HIGH = 1.0

# Random weight range for profiling (uniform distribution); should cover the
# fixed firmware weights in network_config.h, which lie in [-2, 2]
WEIGHT_LOW = -2.0
WEIGHT_HIGH = 2.0
TRACES_PER_WEIGHT = 500

# RNG seed for reproducibility
SEED = 148

# Directory to save captured traces
OUT_DIR = "../data/raw/"

PROFILING_PROJECT_NAME = "../data/raw/profile"
ATTACK_PROJECT_NAME = "../data/raw/attack"
