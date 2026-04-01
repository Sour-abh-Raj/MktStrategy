from __future__ import annotations

from typing import List


class StrategyReplacementEngine:
    def replace_weak(self, active: List[str], underperformers: List[str], candidates: List[str]) -> List[str]:
        updated = [s for s in active if s not in underperformers]
        for c in candidates:
            if c not in updated:
                updated.append(c)
            if len(updated) >= len(active):
                break
        return updated
