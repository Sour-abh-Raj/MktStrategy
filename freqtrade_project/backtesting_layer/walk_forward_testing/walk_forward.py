from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class WalkForwardSlice:
    train_start: int
    train_end: int
    test_start: int
    test_end: int


class WalkForwardTester:
    def generate_slices(self, data_length: int, train_window: int, test_window: int, step: int) -> List[WalkForwardSlice]:
        slices: List[WalkForwardSlice] = []
        cursor = 0
        while cursor + train_window + test_window <= data_length:
            slices.append(
                WalkForwardSlice(
                    train_start=cursor,
                    train_end=cursor + train_window,
                    test_start=cursor + train_window,
                    test_end=cursor + train_window + test_window,
                )
            )
            cursor += step
        return slices
