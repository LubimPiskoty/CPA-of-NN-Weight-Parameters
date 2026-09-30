#!/usr/bin/env python3
"""
Power trace capture script for the neural network target.
Settings are read from cw_config.py (edit that file, not this one, to change
platform/firmware/trace-count/etc.).

Follows the capture pattern from the reference implementation
(XIAOLUHOU/Shuffling-Against-SCA): a single fixed-size capture window per
trace (no multi-segment stitching), stored using ChipWhisperer's built-in
Project/Trace format.

Captures a profiling set (random known weights sent in the payload) and
then an attack set (fixed weights compiled into the firmware) into two
separate projects, rebuilding and reflashing the firmware between them.

Usage:
    python capture.py
"""

import os
import struct
import subprocess
import sys
import time
import numpy as np
import chipwhisperer as cw
from configs import cw_config as cfg
from tqdm import trange

PROGRAMMER_MAP = {
    "stm32f": cw.programmers.STM32FProgrammer,
    "xmega": cw.programmers.XMEGAProgrammer,
    "avr": cw.programmers.AVRProgrammer,
}

MAX_SAMPLES = 24400  # CW-Lite hardware buffer limit
DECIMATE = 1  # increase to stretch the capture window further in time
N_WARMUP = 50  # dummy captures to let the target/scope settle before real capture


def build_target(is_attack_mode: bool, fw_dir: str = cfg.FW_DIR):
    """Rebuild the firmware in fw_dir for cfg.PLATFORM in profiling or attack mode."""
    make_args = [
        f"PLATFORM={cfg.PLATFORM}",
        "CRYPTO_TARGET=NONE",
        f"IS_ATTACK_MODE={int(is_attack_mode)}",
    ]
    # Clean first: make does not track the IS_ATTACK_MODE define, so stale
    # objects from the other mode would otherwise be reused.
    subprocess.run(["make", "clean", *make_args], cwd=fw_dir, check=True)
    subprocess.run(["make", *make_args], cwd=fw_dir, check=True)


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


def flash_target(scope, is_attack_mode: bool):
    """Build the firmware for the given mode and program it onto the target."""
    mode = "attack" if is_attack_mode else "profiling"
    print(f"Building firmware ({mode} mode)...")
    build_target(is_attack_mode=is_attack_mode)
    if not os.path.exists(cfg.FW_PATH):
        print(
            f"Invalid firmware path: {os.path.abspath(cfg.FW_PATH)}.\nMaybe you forgot to build the firmware"
        )
        exit(-1)
    print(f"Flashing firmware: {cfg.FW_PATH}")
    cw.program_target(scope, PROGRAMMER_MAP[cfg.PROGRAMMER], cfg.FW_PATH)
    time.sleep(0.2)


def warm_up(scope, target):
    print(f"Warming up ({N_WARMUP} dummy captures)...")
    dummy_payload = make_payload(-0.67, 0.67)
    for _ in range(N_WARMUP):
        capture_trace(scope, target, dummy_payload)
    print("Warm up done.")


def capture_phase(
    scope, target, project_name: str, input_vals, weight_vals, store_weights: bool
):
    """
    Capture one trace per input into a new project.

    Every payload carries (input, weight). With store_weights (profiling) the
    firmware uses that weight and each trace stores textin=(input, weight).
    Without it (attack) the firmware ignores the payload weight and uses its
    fixed one; the weight is a random dummy so the payload data looks the same
    as in profiling, and only textin=(input,) is stored.
    """
    proj = cw.create_project(project_name, overwrite=True)
    num_traces = len(input_vals)

    print(f"Capturing {num_traces:,} traces into {project_name}...")
    start = time.time()
    try:
        for i in trange(num_traces, mininterval=10):
            cmd_data = make_payload(input_vals[i], weight_vals[i])
            if store_weights:
                textin = (input_vals[i], weight_vals[i])
            else:
                textin = (input_vals[i],)
            trace_wave, _ = capture_trace(scope, target, cmd_data)

            proj.traces.append(
                cw.Trace(wave=trace_wave, textin=textin, textout=None, key=None)
            )
    finally:
        # Also runs on KeyboardInterrupt, which then propagates and stops the run.
        elapsed = time.time() - start
        print(f"  completed in {elapsed:.1f}s")
        proj.save()
        print(f"Saved {len(proj.traces)} traces to project: {project_name}")


def main():
    rng = np.random.default_rng(seed=cfg.SEED)

    # Profiling: a random known weight for every trace
    prof_inputs = [
        float(rng.uniform(cfg.INPUT_LOW, cfg.INPUT_HIGH))
        for _ in range(cfg.NUM_PROFILING_TRACES)
    ]
    prof_weights = [
        float(rng.uniform(cfg.WEIGHT_LOW, cfg.WEIGHT_HIGH))
        for _ in range(cfg.NUM_PROFILING_TRACES)
    ]

    # Attack: only inputs, the weight is the fixed one compiled into the firmware.
    # The payload still carries dummy weights (ignored by the firmware).
    attack_inputs = [
        float(rng.uniform(cfg.INPUT_LOW, cfg.INPUT_HIGH))
        for _ in range(cfg.NUM_ATTACK_TRACES)
    ]
    attack_dummy_weights = [
        float(rng.uniform(cfg.WEIGHT_LOW, cfg.WEIGHT_HIGH))
        for _ in range(cfg.NUM_ATTACK_TRACES)
    ]

    print(f"Connecting to scope and target (platform={cfg.PLATFORM})...")
    scope = cw.scope()
    scope.default_setup()

    target = cw.target(scope, cw.targets.SimpleSerial)

    scope_setup(scope, samples=MAX_SAMPLES, decimate=DECIMATE)

    try:
        if cfg.NUM_PROFILING_TRACES > 0:
            print("\n=== Profiling phase ===")
            flash_target(scope, is_attack_mode=False)
            warm_up(scope, target)
            capture_phase(
                scope,
                target,
                cfg.PROFILING_PROJECT_NAME,
                prof_inputs,
                prof_weights,
                store_weights=True,
            )

        if cfg.NUM_ATTACK_TRACES > 0:
            print("\n=== Attack phase ===")
            flash_target(scope, is_attack_mode=True)
            warm_up(scope, target)
            capture_phase(
                scope,
                target,
                cfg.ATTACK_PROJECT_NAME,
                attack_inputs,
                attack_dummy_weights,
                store_weights=False,
            )

    except KeyboardInterrupt:
        print("\nInterrupted — stopping capture.")
    finally:
        scope.dis()
        target.dis()


if __name__ == "__main__":
    main()
