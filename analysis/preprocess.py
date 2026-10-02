"""Clip the raw ChipWhisperer projects to the analysed window and save them to data/processed/.

Only the trace segments referenced by the project file (<name>.cwp) are used, exactly what
cw.open_project returns; older capture runs left in <name>_data/traces/ are ignored.

    python analysis/preprocess.py

Output: data/processed/<name>.npz with
    traces  float32 (N, WINDOW[1] - WINDOW[0])   trace samples inside WINDOW
    textin  float64 (N, k)                       textin of every trace ((input, weight) or (input,))
    window  int     (2,)                         the sample range the traces were clipped to
"""
import os
import numpy as np
import chipwhisperer as cw

WINDOW = (0, 1000)          # only the start of the capture contains the network computation
PROJECTS = ("profile", "attack")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw")
OUT_DIR = os.path.join(ROOT, "data", "processed")


def process(name):
    proj = cw.open_project(os.path.join(RAW_DIR, name))
    traces, textins = [], []
    for seg in proj.segments:
        n = seg.numTraces()
        seg.loadAllTraces()                                         # memory-mapped: only the window is read
        traces.append(np.array(seg.traces[:n, WINDOW[0]:WINDOW[1]], dtype=np.float32))
        textins.append(np.array([np.atleast_1d(t) for t in seg.textins[:n]], dtype=np.float64))
        seg.unloadAllTraces()
        print(f"  {seg.config.attr('prefix')}: {n} traces")
    traces, textins = np.concatenate(traces), np.concatenate(textins)

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{name}.npz")
    np.savez(path, traces=traces, textin=textins, window=np.array(WINDOW))
    print(f"{name}: {traces.shape[0]} traces x {traces.shape[1]} samples -> {path} "
          f"({os.path.getsize(path) / 2**20:.0f} MiB)")


if __name__ == "__main__":
    for name in PROJECTS:
        process(name)
