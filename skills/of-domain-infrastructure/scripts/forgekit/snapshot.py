from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps

from .safeio import MAX_RECORDS, checkpoint, read_scope, require, safe_path

_ACTIVE = ContextVar("forge_case_snapshot", default=None)


def active_case(case):
    current = _ACTIVE.get()
    if current is not None and current[0] == safe_path(case):
        checkpoint()
        return current
    return None


def inventory(root):
    result = {}
    for name in ("raw", "analysis", "reports"):
        folder = safe_path(root / name)
        require(folder.is_dir(), "INVALID_CASE_DIRECTORY")
        names = []
        for item in folder.iterdir():
            checkpoint()
            require(len(names) < MAX_RECORDS, "TOO_MANY_CASE_FILES")
            safe_path(item)
            names.append(item.name)
        result[name] = tuple(sorted(names))
    return result


@contextmanager
def verified_case(case):
    from .casefiles import load_case, verify
    current = active_case(case)
    if current is not None:
        yield current
        return
    root = safe_path(case)
    require(not (root / ".forge.lock").exists(), "CASE_BUSY")
    before = inventory(root)
    with read_scope(root):
        verify(root)
        state = load_case(root)
        token = _ACTIVE.set(state)
        try:
            yield state
            checkpoint()
            require(not (root / ".forge.lock").exists() and inventory(root) == before,
                    "CASE_CHANGED_DURING_READ")
        finally:
            _ACTIVE.reset(token)


def read_operation(function):
    @wraps(function)
    def invoke(case, *args, **kwargs):
        with verified_case(case):
            return function(case, *args, **kwargs)
    return invoke
