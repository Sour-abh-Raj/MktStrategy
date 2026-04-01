from __future__ import annotations

import itertools
from typing import Dict, Iterable, List


class ParameterSearch:
    def grid(self, space: Dict[str, Iterable[float]]) -> List[Dict[str, float]]:
        keys = list(space.keys())
        combos = itertools.product(*(space[k] for k in keys))
        return [dict(zip(keys, combo)) for combo in combos]
