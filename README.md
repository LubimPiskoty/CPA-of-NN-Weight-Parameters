# Correlation Power Analysis of Neural Network Weight Parameters

Bachelor's thesis repository — FIIT STU Bratislava.
Supervisor: Xiaolu Hou

Studies leakage on Neural networks running on ChipWhisperer using template
capture and Jupyter/Python for analysis.

## Repository structure

| Folder      | Contents                                                                                |
| ----------- | --------------------------------------------------------------------------------------- |
| `firmware/` | On-chip C programs flashed to the target                                                |
| `capture/`  | Python scripts driving ChipWhisperer to record traces                                   |
| `data/`     | Captured traces — `raw/` (untouched) and `processed/` (aligned/filtered)                |
| `analysis/` | Jupyter notebooks: preprocessing, CPA attacks, result generation                        |
| `results/`  | Exported figures/tables used directly in the thesis                                     |
| `thesis/`   | FIIT-BP-template LaTeX source ([template](https://github.com/dodancs/FIIT-BP-template)) |

## Setup

### Hardware / capture environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install chipwhisperer numpy scipy matplotlib jupyter
```

### Building the thesis PDF

```bash
cd thesis
latexmk -pdf main.tex
```

## Reproducing results

1. Flash firmware from `firmware/main.c` onto the target.
2. Run the matching script in `capture/` to record traces into `data/raw/`.
3. Run `analysis/01_preprocessing.ipynb` to produce `data/processed/`.
4. Run `analysis/02_cpa_attack.ipynb` onward to reproduce figures into `results/`.
