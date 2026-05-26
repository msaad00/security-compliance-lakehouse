"""Controls-as-code policy engine.

Each control in ``controls/catalog.json`` declares an ``evaluation_rule``. This
module evaluates that rule against a control's evidence to derive pass/fail with
human-readable reasons, instead of the pipeline hard-coding "fail if any open
event". Rules are declarative specs (or named aliases), so control logic lives
in the catalog and is lintable, not buried in pipeline code.

Rule spec shape::

    {"fail_if": <predicate>}

Predicates compose with ``all`` / ``any`` / ``not`` over these leaves:

- ``open_violations``: ``{"min": N}`` / ``{"max": N}`` — open violation count
- ``max_severity``:    ``{"at_least": "high"}`` — highest open-violation severity
- ``evidence_present``: ``true`` / ``false`` — any evidence attached
- ``evidence_status``: ``{"in": ["stale", "expired", "missing"]}`` — freshness
- ``min_evidence_coverage``: ``{"below": 0.5}`` — evidence/event ratio
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
STALE_EVIDENCE = ["stale", "expired", "missing"]

# Named aliases map the catalog's string rules onto declarative specs.
NAMED_RULES: dict[str, dict[str, Any]] = {
    "fail_when_open_violation": {"fail_if": {"open_violations": {"min": 1}}},
    "fail_when_stale_evidence": {
        "fail_if": {"any": [{"evidence_status": {"in": STALE_EVIDENCE}}, {"open_violations": {"min": 1}}]}
    },
    "fail_when_open_violation_or_stale_evidence": {
        "fail_if": {"any": [{"open_violations": {"min": 1}}, {"evidence_status": {"in": STALE_EVIDENCE}}]}
    },
    "fail_when_missing_evidence": {"fail_if": {"any": [{"evidence_present": False}, {"open_violations": {"min": 1}}]}},
    "fail_when_high_severity_open": {
        "fail_if": {"all": [{"open_violations": {"min": 1}}, {"max_severity": {"at_least": "high"}}]}
    },
}

DEFAULT_RULE = "fail_when_open_violation"

_LEAF_KEYS = {
    "open_violations",
    "max_severity",
    "evidence_present",
    "evidence_status",
    "min_evidence_coverage",
}


@dataclass(frozen=True)
class ControlContext:
    """Evidence facts a rule is evaluated against."""

    control_id: str
    open_violation_count: int = 0
    event_count: int = 0
    evidence_count: int = 0
    max_severity: str = "info"
    evidence_status: str | None = None

    @property
    def evidence_coverage(self) -> float:
        return self.evidence_count / self.event_count if self.event_count else 0.0


@dataclass
class RuleResult:
    status: str  # "pass" | "fail"
    rule: str
    reasons: list[str] = field(default_factory=list)


class PolicyError(ValueError):
    """Raised when a rule spec is malformed (used by linting)."""


def resolve_rule(rule: Any) -> tuple[dict[str, Any], str]:
    """Resolve a rule (named string or inline spec) to ``(spec, name)``. Strict; raises on unknown."""
    if rule is None or rule == "":
        return NAMED_RULES[DEFAULT_RULE], DEFAULT_RULE
    if isinstance(rule, str):
        spec = NAMED_RULES.get(rule)
        if spec is None:
            raise PolicyError(f"unknown named rule {rule!r}; known: {sorted(NAMED_RULES)}")
        return spec, rule
    if isinstance(rule, Mapping):
        if "fail_if" not in rule:
            raise PolicyError("inline rule must contain a 'fail_if' predicate")
        return dict(rule), "inline"
    raise PolicyError(f"rule must be a name or a spec object, got {type(rule).__name__}")


def evaluate_control(context: ControlContext, rule: Any) -> RuleResult:
    """Evaluate ``rule`` against ``context`` → pass/fail with reasons.

    Resilient: an unknown/malformed rule falls back to the default rule (so one
    bad catalog entry never crashes the pipeline) while ``policy lint`` still
    flags it via :func:`validate_rule`.
    """
    try:
        spec, name = resolve_rule(rule)
    except PolicyError as exc:
        spec, name = NAMED_RULES[DEFAULT_RULE], DEFAULT_RULE
        matched, reasons = _eval_predicate(spec["fail_if"], context)
        reasons = [f"rule fallback ({exc}); evaluated as {DEFAULT_RULE}", *reasons]
        return RuleResult(status="fail" if matched else "pass", rule=name, reasons=reasons)
    matched, reasons = _eval_predicate(spec["fail_if"], context)
    return RuleResult(status="fail" if matched else "pass", rule=name, reasons=reasons)


def validate_rule(rule: Any) -> list[str]:
    """Return a list of problems with ``rule`` (empty == valid). Used by linting."""
    try:
        spec, _name = resolve_rule(rule)
    except PolicyError as exc:
        return [str(exc)]
    problems: list[str] = []
    _validate_predicate(spec["fail_if"], problems)
    return problems


def _eval_predicate(pred: Any, ctx: ControlContext) -> tuple[bool, list[str]]:
    if not isinstance(pred, Mapping):
        raise PolicyError(f"predicate must be an object, got {type(pred).__name__}")
    if "all" in pred:
        results = [_eval_predicate(sub, ctx) for sub in _as_list(pred["all"])]
        matched = all(r[0] for r in results)
        return matched, [reason for ok, reasons in results if ok for reason in reasons]
    if "any" in pred:
        results = [_eval_predicate(sub, ctx) for sub in _as_list(pred["any"])]
        matched = any(r[0] for r in results)
        return matched, [reason for ok, reasons in results if ok for reason in reasons]
    if "not" in pred:
        inner, _ = _eval_predicate(pred["not"], ctx)
        return (not inner), ([] if inner else ["negated condition held"])
    return _eval_leaf(pred, ctx)


def _eval_leaf(pred: Mapping[str, Any], ctx: ControlContext) -> tuple[bool, list[str]]:
    keys = set(pred) & _LEAF_KEYS
    if len(keys) != 1:
        raise PolicyError(f"leaf predicate must name exactly one of {sorted(_LEAF_KEYS)}, got {sorted(pred)}")
    key = keys.pop()
    spec = pred[key]
    if key == "open_violations":
        n = ctx.open_violation_count
        if "min" in spec and n >= int(spec["min"]):
            return True, [f"{n} open violation(s) (>= {spec['min']})"]
        if "max" in spec and n > int(spec["max"]):
            return True, [f"{n} open violation(s) (> max {spec['max']})"]
        return False, []
    if key == "max_severity":
        floor = SEVERITY_ORDER.get(str(spec.get("at_least", "high")).lower(), 3)
        actual = SEVERITY_ORDER.get(ctx.max_severity.lower(), 0)
        hit = actual >= floor and ctx.open_violation_count > 0
        return hit, ([f"open severity {ctx.max_severity} >= {spec.get('at_least', 'high')}"] if hit else [])
    if key == "evidence_present":
        present = ctx.evidence_count > 0
        matched = present == bool(spec)
        return matched, ([f"evidence_present={present}"] if matched else [])
    if key == "evidence_status":
        wanted = {str(s).lower() for s in spec.get("in", [])}
        status = (ctx.evidence_status or "").lower()
        matched = bool(status) and status in wanted
        return matched, ([f"evidence is {status}"] if matched else [])
    if key == "min_evidence_coverage":
        threshold = float(spec.get("below", 0.5))
        matched = ctx.evidence_coverage < threshold
        return matched, ([f"evidence coverage {ctx.evidence_coverage:.0%} < {threshold:.0%}"] if matched else [])
    return False, []


def _validate_predicate(pred: Any, problems: list[str]) -> None:
    if not isinstance(pred, Mapping):
        problems.append(f"predicate must be an object, got {type(pred).__name__}")
        return
    for combinator in ("all", "any"):
        if combinator in pred:
            for sub in _as_list(pred[combinator]):
                _validate_predicate(sub, problems)
            return
    if "not" in pred:
        _validate_predicate(pred["not"], problems)
        return
    if not (set(pred) & _LEAF_KEYS):
        problems.append(f"unknown predicate keys {sorted(pred)}; expected one of {sorted(_LEAF_KEYS)}")


def _as_list(value: Any) -> Sequence[Any]:
    if isinstance(value, str | Mapping):
        return [value]
    if isinstance(value, Sequence):
        return value
    raise PolicyError("all/any expects a list of predicates")
