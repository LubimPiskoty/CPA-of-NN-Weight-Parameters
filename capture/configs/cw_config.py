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
# Profiling: firmware generates all weights from a seed sent by 'k' (random,
# the attacked weight is read back so it is known).
# Attack: firmware uses its fixed ground-truth weights, only the input is sent.
NUM_PROFILING_TRACES = 50_000
NUM_ATTACK_TRACES = 5_000

# Random input range fed to the network (uniform distribution)
INPUT_LOW = -1.0
INPUT_HIGH = 1.0

# Number of consecutive traces captured with one seed, i.e. with the same
# weights. A new seed (new random weights) is sent only between batches.
# The weight range is RANDOM_WEIGHT_MAX in firmware/main.c ([-2, 2]).
BATCH_SIZE = 100

# RNG seed for reproducibility
SEED = 148

# Directory to save captured traces
OUT_DIR = "../data/raw/"

PROFILING_PROJECT_NAME = "../data/raw/profile"
ATTACK_PROJECT_NAME = "../data/raw/attack"
