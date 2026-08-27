from __future__ import annotations

from collections.abc import Iterable


PERMISSION_ORDER = {"read": 1, "execute": 2, "write": 3, "admin": 4}


def permission_allows(requested: str, granted: str) -> bool:
    return PERMISSION_ORDER.get(granted, 0) >= PERMISSION_ORDER.get(requested, 0)


def unique_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result

