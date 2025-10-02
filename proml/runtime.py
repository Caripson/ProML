"""Runtime primitives for executing ProML prompts."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from .constraints import ConstraintEngine
from .parser import CacheConfig, EngineProfile, MetaBlock, PromlDocument
from .policy import PolicyEvaluator


@dataclass
class CacheEntry:
    value: Any
    expires_at: Optional[float]

    def is_expired(self) -> bool:
        return self.expires_at is not None and time.time() > self.expires_at


class CacheBackend(Protocol):
    def get(self, key: str) -> Optional[CacheEntry]: ...

    def set(self, key: str, entry: CacheEntry) -> None: ...

    def delete(self, key: str) -> None: ...


class InMemoryCache(CacheBackend):
    def __init__(self) -> None:
        self._store: Dict[str, CacheEntry] = {}

    def get(self, key: str) -> Optional[CacheEntry]:
        return self._store.get(key)

    def set(self, key: str, entry: CacheEntry) -> None:
        self._store[key] = entry

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


class PromptCache:
    """Cache manager that honours `CacheConfig` policies."""

    def __init__(self, backend: CacheBackend | None = None) -> None:
        self._backend = backend or InMemoryCache()

    def fetch(self, key: str) -> Optional[Any]:
        entry = self._backend.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            self._backend.delete(key)
            return None
        return entry.value

    def store(self, key: str, value: Any, cache: CacheConfig | None) -> None:
        ttl_seconds = cache.ttl_seconds if cache else None
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        entry = CacheEntry(value=value, expires_at=expires_at)
        self._backend.set(key, entry)


def build_cache_key(
    meta: MetaBlock,
    profile: EngineProfile | None,
    prompt_signature: str,
    inputs: Dict[str, Any],
) -> str:
    payload = {
        "id": meta.identifier,
        "version": meta.version,
        "profile": None,
        "prompt": prompt_signature,
        "inputs": inputs,
    }
    if profile:
        payload["profile"] = {
            "name": profile.name,
            "provider": profile.provider,
            "model": profile.model,
            "temperature": profile.temperature,
            "max_output_tokens": profile.max_output_tokens,
        }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def select_profile(meta: MetaBlock, name: str | None = None) -> EngineProfile | None:
    if not meta.profiles:
        return None
    if name and name in meta.profiles:
        return meta.profiles[name]
    if "default" in meta.profiles:
        return meta.profiles["default"]
    return next(iter(meta.profiles.values()))


class EngineAdapter(Protocol):
    """Abstracts provider-specific execution (OpenAI, Anthropic, etc.)."""

    provider: str

    def invoke(self, document: PromlDocument, profile: EngineProfile, inputs: Dict[str, Any]) -> str: ...


class AdapterRegistry:
    def __init__(self) -> None:
        self._registry: Dict[str, EngineAdapter] = {}

    def register(self, adapter: EngineAdapter) -> None:
        self._registry[adapter.provider] = adapter

    def get(self, provider: str) -> EngineAdapter:
        if provider not in self._registry:
            raise KeyError(f"No engine adapter registered for provider '{provider}'.")
        return self._registry[provider]


class OpenAIAdapter:
    provider = "openai"

    def invoke(self, document: PromlDocument, profile: EngineProfile, inputs: Dict[str, Any]) -> str:  # pragma: no cover - requires network
        raise NotImplementedError(
            "OpenAIAdapter.invoke requires the OpenAI SDK and network access. "
            "Set provider='stub' in the profile for offline development."
        )


class AnthropicAdapter:
    provider = "anthropic"

    def invoke(self, document: PromlDocument, profile: EngineProfile, inputs: Dict[str, Any]) -> str:  # pragma: no cover - requires network
        raise NotImplementedError(
            "AnthropicAdapter.invoke requires the Anthropic SDK and network access. "
            "Set provider='stub' in the profile for offline development."
        )


class LocalAdapter:
    provider = "local"

    def invoke(self, document: PromlDocument, profile: EngineProfile, inputs: Dict[str, Any]) -> str:
        raise NotImplementedError(
            "LocalAdapter.invoke should integrate with a local runtime (e.g. transformers pipeline)."
        )


class OllamaAdapter:
    provider = "ollama"

    def invoke(self, document: PromlDocument, profile: EngineProfile, inputs: Dict[str, Any]) -> str:
        raise NotImplementedError("OllamaAdapter.invoke should call the Ollama HTTP API.")


class StubAdapter:
    provider = "stub"

    def invoke(self, document: PromlDocument, profile: EngineProfile, inputs: Dict[str, Any]) -> str:
        match = _find_matching_mock_output(document, inputs)
        if match is None:
            payload = {
                "message": "stub-adapter",
                "inputs": inputs,
            }
        else:
            payload = match
        return json.dumps(payload, sort_keys=True)


def _find_matching_mock_output(document: PromlDocument, inputs: Dict[str, Any]) -> Optional[Any]:
    for case in document.tests:
        base_inputs = dict(case.input)
        if base_inputs == inputs and case.steps:
            return case.steps[-1].mock_output
        for step in case.steps:
            combined = dict(case.input)
            combined.update(step.input)
            if combined == inputs:
                return step.mock_output
    if document.tests:
        fallback_case = document.tests[0]
        if fallback_case.steps:
            return fallback_case.steps[-1].mock_output
    return None


default_adapter_registry = AdapterRegistry()
default_adapter_registry.register(OpenAIAdapter())
default_adapter_registry.register(AnthropicAdapter())
default_adapter_registry.register(LocalAdapter())
default_adapter_registry.register(OllamaAdapter())
default_adapter_registry.register(StubAdapter())


@dataclass
class PromptExecutionResult:
    raw_output: str
    parsed_output: Any
    from_cache: bool
    duration: float
    estimated_cost: float
    profile_name: str
    provider: str
    warnings: List[str]


class PromptExecutor:
    """High-level orchestrator that enforces schema, policy, and caching."""

    def __init__(
        self,
        adapters: AdapterRegistry | None = None,
        cache: PromptCache | None = None,
    ) -> None:
        self._adapters = adapters or default_adapter_registry
        self._cache = cache or PromptCache()

    def execute(
        self,
        document: PromlDocument,
        inputs: Dict[str, Any],
        *,
        profile_name: Optional[str] = None,
        override_provider: Optional[str] = None,
        use_cache: bool = True,
    ) -> PromptExecutionResult:
        profile = select_profile(document.meta, profile_name)
        if profile is None:
            raise RuntimeError("No engine profile defined in META.profiles.")
        if override_provider:
            profile = dataclasses.replace(profile, provider=override_provider)

        constraint_engine = ConstraintEngine(document.output)
        policy_evaluator = PolicyEvaluator(document.policy)
        warnings = [warning.message for warning in policy_evaluator.validate()]

        cache_config = profile.cache if profile.cache and use_cache else None
        cache_key = build_cache_key(document.meta, profile, document.meta.identifier, inputs)
        cached_payload = self._cache.fetch(cache_key) if cache_config else None

        duration = 0.0
        from_cache = False

        if cached_payload is not None:
            raw_output, parsed_output = _coerce_cached_payload(cached_payload)
            from_cache = True
        else:
            adapter = self._resolve_adapter(profile.provider)
            start = time.perf_counter()
            try:
                raw_output = adapter.invoke(document, profile, inputs)
            except NotImplementedError as exc:
                warnings.append(str(exc))
                stub_adapter = self._resolve_adapter("stub")
                raw_output = stub_adapter.invoke(document, profile, inputs)
            duration = time.perf_counter() - start
            parsed_output = _parse_json_output(raw_output)
            if cache_config:
                self._cache.store(cache_key, {"raw": raw_output, "parsed": parsed_output}, cache_config)

        report = constraint_engine.validate_all(raw_output, parsed_output)
        if not report.passed:
            joined = "; ".join(report.errors)
            raise RuntimeError(f"Output failed constraint validation: {joined}")

        policy_evaluator.enforce(parsed_output)

        estimated_cost = 0.0 if from_cache else float(profile.cost_budget or 0.0)

        return PromptExecutionResult(
            raw_output=raw_output,
            parsed_output=parsed_output,
            from_cache=from_cache,
            duration=duration,
            estimated_cost=estimated_cost,
            profile_name=profile.name,
            provider=profile.provider,
            warnings=warnings,
        )

    def _resolve_adapter(self, provider: str) -> EngineAdapter:
        try:
            return self._adapters.get(provider)
        except KeyError as exc:
            raise RuntimeError(str(exc)) from exc


def _coerce_cached_payload(payload: Any) -> tuple[str, Any]:
    if isinstance(payload, dict) and "raw" in payload and "parsed" in payload:
        raw = payload["raw"]
        parsed = payload["parsed"]
        raw_str = raw if isinstance(raw, str) else json.dumps(raw, separators=(",", ":"), sort_keys=True)
        return raw_str, parsed
    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            parsed = payload
        return payload, parsed
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return raw, payload


def _parse_json_output(raw_output: str) -> Any:
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Adapter returned invalid JSON: {exc}") from exc
