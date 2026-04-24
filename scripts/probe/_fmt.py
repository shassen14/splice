from __future__ import annotations

from typing import Any

W = 72


def section(title: str) -> None:
    print(f"\n{'=' * W}")
    print(f"  {title}")
    print(f"{'=' * W}")


def subsection(title: str) -> None:
    print(f"\n  --- {title} ---")


def call(label: str, fn, *args, indent: str = "  ", **kwargs) -> Any:
    try:
        result = fn(*args, **kwargs)
    except Exception as e:
        print(f"{indent}{label:<45} FAIL  {e}")
        return None

    if result is None:
        tag = "NONE"
    elif result == {} or result == [] or result == "":
        tag = "EMPTY"
    elif result is False:
        tag = "FALSE"
    else:
        tag = "OK"

    rstr = repr(result)
    if len(rstr) > 120:
        rstr = rstr[:117] + "..."
    print(f"{indent}{label:<45} {tag:<6} {rstr}")
    return result


def probe_methods(obj, candidates: list[str]) -> list[str]:
    found = [m for m in candidates if getattr(obj, m, None) is not None]
    missing = [m for m in candidates if getattr(obj, m, None) is None]
    print(f"  Present:  {found}")
    if missing:
        print(f"  Absent:   {missing}")
    return found
