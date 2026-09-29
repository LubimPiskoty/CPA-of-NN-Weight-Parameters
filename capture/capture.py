#!/usr/bin/env python3
"""
Power trace capture script for the neural network target.
Settings are read from cw_config.py (edit that file, not this one, to change
platform/firmware/trace-count/etc.).

Follows the capture pattern from the reference implementation
(XIAOLUHOU/Shuffling-Against-SCA): a single fixed-size capture window per
trace (no multi-segment stitching), stored using ChipWhisperer's built-in
Project/Trace format.

Usage:
    python capture.py
"""

import os
import struct
import sys
import time
import numpy as np
import chipwhisperer as cw
from configs import cw_config as cfg
from tqdm import trange
import math

PROGRAMMER_MAP = {
    "stm32f": cw.programmers.STM32FProgrammer,
    "xmega": cw.programmers.XMEGAProgrammer,
    "avr": cw.programmers.AVRProgrammer,
}

MAX_SAMPLES = 24400  # CW-Lite hardware buffer limit
DECIMATE = 1  # increase to stretch the capture window further in time
N_WARMUP = 50  # dummy captures to let the target/scope settle before real capture


def make_payload(input_value: float, weight_value: float) -> bytearray:
    """Pack a float into a 16-byte SimpleSerial payload."""
    payload = bytearray(16)
    payload[0:4] = struct.pack("<f", input_value)
    payload[4:8] = struct.pack("<f", weight_value)
    return payload


def scope_setup(scope, samples: int = MAX_SAMPLES, decimate: int = DECIMATE):
    scope.arm()
    scope.adc.fifo_fill_mode = "normal"
    scope.adc.samples = samples
    scope.adc.decimate = decimate


def capture_trace(scope, target, cmd_data: bytearray, timeout_ms: int = 5000):
    """Single fixed-window capture using plain SimpleSerial (v1)."""
    target.flush()
    scope.arm()
    target.simpleserial_write("p", cmd_data)

    ret = scope.capture()
    if ret:
        print("WARNING: scope capture timed out", file=sys.stderr)

    trace = scope.get_last_trace()
    response = target.simpleserial_read("r", 16, timeout=timeout_ms)
    return trace, response


def main():
    print(f"Connecting to scope and target (platform={cfg.PLATFORM})...")
    scope = cw.scope()
    scope.default_setup()

    target = cw.target(scope, cw.targets.SimpleSerial)

    scope_setup(scope, samples=MAX_SAMPLES, decimate=DECIMATE)

    if not cfg.SKIP_FLASH:
        if not os.path.exists(cfg.FW_PATH):
            print(
                f"Invalid firmware path: {os.path.abspath(cfg.FW_PATH)}.\nMaybe you forgot to build the firmware"
            )
            exit(-1)
        print(f"Flashing firmware: {cfg.FW_PATH}")
        cw.program_target(scope, PROGRAMMER_MAP[cfg.PROGRAMMER], cfg.FW_PATH)
        time.sleep(0.2)
    else:
        print("Skipping flash (SKIP_FLASH=True in cw_config.py)")

    rng = np.random.default_rng(seed=cfg.SEED)
    input_vals = [
        float(rng.uniform(cfg.INPUT_LOW, cfg.INPUT_HIGH)) for _ in range(cfg.NUM_TRACES)
    ]

    weight_vals = []
    for _ in range(math.ceil(cfg.NUM_TRACES / cfg.TRACES_PER_WEIGHT)):
        w = float(rng.uniform(cfg.WEIGHT_LOW, cfg.WEIGHT_HIGH))
        weight_vals.extend([w] * cfg.TRACES_PER_WEIGHT)
    weight_vals = weight_vals[: cfg.NUM_TRACES]
    proj = cw.create_project(cfg.PROJECT_NAME, overwrite=True)

    print(f"Warming up ({N_WARMUP} dummy captures)...")
    dummy_payload = make_payload(-0.67, 0.67)
    for _ in range(N_WARMUP):
        capture_trace(scope, target, dummy_payload)
    print("Warm up done.")

    # proj.config["Ground Truth"] = {}
    # proj.config["Ground Truth"]["Weight[0][0]"] = w

    print(f"Capturing {cfg.NUM_TRACES:,} traces...")
    start = time.time()
    try:
        for i in trange(cfg.NUM_TRACES, mininterval=10):
            cmd_data = make_payload(input_vals[i], weight_vals[i])
            trace_wave, _ = capture_trace(scope, target, cmd_data)

            trace = cw.Trace(
                wave=trace_wave,
                textin=(input_vals[i], weight_vals[i]),
                textout=None,
                key=None,
            )
            proj.traces.append(trace)

    except KeyboardInterrupt:
        print("\nInterrupted — saving what was captured so far.")
    finally:
        elapsed = time.time() - start
        print(f"  completed in {elapsed:.1f}s")
        scope.dis()
        target.dis()

    proj.save()
    print(f"\nSaved {len(proj.traces)} traces to project: {cfg.PROJECT_NAME}")


if __name__ == "__main__":
    main()
