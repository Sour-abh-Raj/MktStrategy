from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import List


@dataclass
class HyperoptResult:
    command: List[str]
    return_code: int
    stdout: str
    stderr: str


class HyperoptRunner:
    def build_command(
        self,
        strategy: str,
        config_path: str,
        timerange: str,
        epochs: int = 50,
        spaces: str = "buy sell roi stoploss trailing",
    ) -> List[str]:
        return [
            "freqtrade",
            "hyperopt",
            "--strategy",
            strategy,
            "--config",
            config_path,
            "--timerange",
            timerange,
            "--epochs",
            str(epochs),
            "--spaces",
            spaces,
        ]

    def run(self, strategy: str, config_path: str, timerange: str, epochs: int = 50) -> HyperoptResult:
        cmd = self.build_command(strategy, config_path, timerange, epochs)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return HyperoptResult(command=cmd, return_code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
