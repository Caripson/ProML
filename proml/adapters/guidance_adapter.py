"""Guidance-compatible constrained decoding adapter."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..constraints import GenerationAdapter

try:  # pragma: no cover - optional dependency
    import guidance  # type: ignore
except ImportError:  # pragma: no cover
    guidance = None  # type: ignore


class GuidanceGenerationAdapter(GenerationAdapter):
    """Adapter that prepares constraint kwargs for the Guidance `gen` operator.

    The adapter does not execute the model itself; it simply collects the
    constraint metadata so that a Guidance program can call::

        guidance.gen(name=variable_name, **adapter.gen_kwargs())

    When the `guidance` package is not installed, initialisation raises
    `RuntimeError`, ensuring callers know decoder-time enforcement is
    unavailable.
    """

    def __init__(self, variable_name: str = "output") -> None:
        if guidance is None:
            raise RuntimeError(
                "The 'guidance' package is required for GuidanceGenerationAdapter. "
                "Install guidance or use the stub/regex validation fallback."
            )
        self.variable_name = variable_name
        self._constraints: Dict[str, Any] = {}

    # --- GenerationAdapter protocol -------------------------------------------------

    def supports_regex(self) -> bool:
        return True

    def apply_regex(self, pattern: str) -> None:
        self._constraints["regex"] = pattern

    def supports_json_schema(self) -> bool:
        return True

    def apply_json_schema(self, schema: Dict[str, Any]) -> None:
        self._constraints["schema"] = schema

    def supports_grammar(self) -> bool:
        # Guidance can consume EBNF grammars via llguidance integration when provided.
        return True

    def apply_grammar(self, grammar: Dict[str, Any]) -> None:
        self._constraints["grammar"] = grammar

    # --- Convenience helpers -------------------------------------------------------

    def gen_kwargs(self) -> Dict[str, Any]:
        """Return keyword arguments for `guidance.gen` aligned with collected constraints."""
        return dict(self._constraints)

    def gen_call(self, *, stream: bool = False, **kwargs: Any) -> Any:
        """Create a partially-applied `guidance.gen` call with constraints attached.

        Example usage inside a Guidance program::

            adapter = GuidanceGenerationAdapter()
            with guidance.program(llm=...) as program:
                program += adapter.gen_call()

        Additional keyword arguments are forwarded to `guidance.gen`.
        """

        if guidance is None:  # pragma: no cover - guarded above
            raise RuntimeError("guidance is not available")

        gen_kwargs = self.gen_kwargs()
        gen_kwargs.update(kwargs)
        return guidance.gen(name=self.variable_name, stream=stream, **gen_kwargs)

    def variable(self) -> str:
        """Expose the configured variable name for template authors."""
        return self.variable_name


__all__ = ["GuidanceGenerationAdapter"]
