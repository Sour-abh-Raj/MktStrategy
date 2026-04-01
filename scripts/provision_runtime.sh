#!/usr/bin/env bash
set -euo pipefail

python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install freqtrade pandas numpy ta scikit-learn optuna pytest

freqtrade --version
