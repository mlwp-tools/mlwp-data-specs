"""Reporting primitives for trait validation."""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, Dict, Iterator, List, Optional, TextIO, Tuple
from unittest import mock

from loguru import logger
from rich.console import Console
from rich.table import Table

CHECK_REGISTRY: Dict[Tuple[str, str], Callable[..., "ValidationReport"]] = {}


def log_function_call(
    func: Callable[..., "ValidationReport"],
) -> Callable[..., "ValidationReport"]:
    """Register and wrap check functions for consistent logging and tracing.

    Parameters
    ----------
    func : Callable[..., ValidationReport]
        Check function that returns a validation report.

    Returns
    -------
    Callable[..., ValidationReport]
        Wrapped function that logs invocation details and annotates report rows
        with the source function path.
    """

    key = (func.__module__, func.__name__)
    if key not in CHECK_REGISTRY:
        CHECK_REGISTRY[key] = func

    @wraps(func)
    def wrapper(*args: object, **kwargs: object) -> ValidationReport:
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
    """Single requirement evaluation result."""

    section: str
    requirement: str
    status: str
    detail: str = ""
    module: Optional[str] = None
    function: Optional[str] = None

    def __post_init__(self) -> None:
        valid = {"FAIL", "WARNING", "PASS"}
        if self.status not in valid:
            raise ValueError(
                f"Invalid status {self.status}. Expected one of {sorted(valid)}"
            )


@dataclass
class ValidationReport:
    """Container for validation results across one or more checks."""

    ok: bool = True
    results: List[Result] = field(default_factory=list)

    def add(
        self, section: str, requirement: str, status: str, detail: str = ""
    ) -> None:
        """Append a new result entry to the report.

        Parameters
        ----------
        section : str
            Logical section name, e.g. ``"Time Coordinate"``.
        requirement : str
            Human-readable requirement label.
        status : str
            Validation status, one of ``"PASS"``, ``"WARNING"``, ``"FAIL"``.
        detail : str, optional
            Additional context for the result row.
        """
        self.results.append(
            Result(
                section=section, requirement=requirement, status=status, detail=detail
            )
        )
        if status == "FAIL":
            self.ok = False

    def summarize(self) -> str:
        """Create a one-line summary of report counts.

        Returns
        -------
        str
            Summary containing fail/warning/pass counts.
        """
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
        """Check if any result has ``FAIL`` status.

        Returns
        -------
        bool
            ``True`` when at least one failing result exists.
        """
        return any(result.status == "FAIL" for result in self.results)

    def has_warnings(self) -> bool:
        """Check if any result has ``WARNING`` status.

        Returns
        -------
        bool
            ``True`` when at least one warning result exists.
        """
        return any(result.status == "WARNING" for result in self.results)

    def console_print(self, *, file: TextIO | None = None) -> None:
        """Render the report as a rich table.

        Parameters
        ----------
        file : TextIO | None, optional
            Output stream. Defaults to stdout.
        """
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
def skip_all_checks() -> Iterator[None]:
    """Temporarily replace registered checks with no-op stubs.

    Yields
    ------
    Iterator[None]
        Context where registered checks return empty reports.
    """

    def _stubbed_check(*_args: object, **_kwargs: object) -> ValidationReport:
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
