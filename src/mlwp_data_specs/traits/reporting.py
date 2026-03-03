"""Reporting primitives for trait validation."""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, Dict, List, Optional, Tuple
from unittest import mock

from loguru import logger
from rich.console import Console
from rich.table import Table

CHECK_REGISTRY: Dict[Tuple[str, str], Callable] = {}


def log_function_call(func: Callable):
    """Register and wrap check functions for consistent logging and tracing."""
    key = (func.__module__, func.__name__)
    if key not in CHECK_REGISTRY:
        CHECK_REGISTRY[key] = func

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Applying {func.__name__} with {kwargs}")
        active = CHECK_REGISTRY[key]
        report = active(*args, **kwargs)
        for result in report.results:
            result.module = func.__module__
            result.function = func.__name__
        return report

    return wrapper


@dataclass
class Result:
    section: str
    requirement: str
    status: str
    detail: str = ""
    module: Optional[str] = None
    function: Optional[str] = None

    def __post_init__(self) -> None:
        valid = {"FAIL", "WARNING", "PASS"}
        if self.status not in valid:
            raise ValueError(f"Invalid status {self.status}. Expected one of {sorted(valid)}")


@dataclass
class ValidationReport:
    ok: bool = True
    results: List[Result] = field(default_factory=list)

    def add(self, section: str, requirement: str, status: str, detail: str = "") -> None:
        self.results.append(Result(section=section, requirement=requirement, status=status, detail=detail))
        if status == "FAIL":
            self.ok = False

    def summarize(self) -> str:
        fails = sum(1 for r in self.results if r.status == "FAIL")
        warnings = sum(1 for r in self.results if r.status == "WARNING")
        passes = sum(1 for r in self.results if r.status == "PASS")
        return f"Summary: {fails} fail(s), {warnings} warning(s), {passes} pass(es)."

    def __iadd__(self, other: "ValidationReport") -> "ValidationReport":
        self.results.extend(other.results)
        self.ok = self.ok and other.ok
        return self

    def __add__(self, other: "ValidationReport") -> "ValidationReport":
        out = ValidationReport(ok=self.ok and other.ok)
        out.results = [*self.results, *other.results]
        return out

    def has_fails(self) -> bool:
        return any(result.status == "FAIL" for result in self.results)

    def has_warnings(self) -> bool:
        return any(result.status == "WARNING" for result in self.results)

    def console_print(self, *, file=None) -> None:
        console = Console(file=file)
        table = Table(title="Validation Report")
        table.add_column("Section", style="bold")
        table.add_column("Requirement", style="dim")
        table.add_column("Status", justify="center")
        table.add_column("Detail", style="italic")
        table.add_column("Check Function", style="bold")

        emojis = {"FAIL": "FAIL", "WARNING": "WARN", "PASS": "PASS"}
        for result in self.results:
            function_name = "N/A"
            if result.module and result.function:
                function_name = f"{result.module}.{result.function}".removeprefix(
                    "mlwp_data_specs.checks."
                )
            table.add_row(
                result.section,
                result.requirement,
                emojis[result.status],
                result.detail,
                function_name,
            )

        console.print(table)
        console.print(self.summarize())


@contextmanager
def skip_all_checks():
    """Temporarily replace registered checks with no-op stubs."""

    def _stubbed_check(*_args, **_kwargs):
        return ValidationReport()

    with ExitStack() as stack:
        try:
            stack.enter_context(mock.patch("xarray.open_zarr", lambda *a, **kw: None))
        except ModuleNotFoundError:
            pass

        stack.enter_context(
            mock.patch.dict(
                CHECK_REGISTRY,
                {key: _stubbed_check for key in list(CHECK_REGISTRY.keys())},
            )
        )
        yield
