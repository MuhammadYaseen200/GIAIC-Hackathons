# ADR-0001: Watcher Base Class Design

> **Scope**: Defines the inheritance model and lifecycle contract for all watchers in the AI Employee system.

- **Status:** Accepted
- **Date:** 2026-02-17
- **Feature:** gmail-watcher (005)
- **Context:** Constitution Principle VI mandates "all watchers MUST inherit from a common BaseWatcher class." The watcher architecture is the perception layer of the AI Employee -- Gmail, WhatsApp, Calendar, and filesystem watchers all need a shared lifecycle (start/stop/poll/process_item), shared retry logic, shared state persistence, and shared logging. The design choice is how to define this shared contract in Python.

## Decision

Use an **Abstract Base Class (ABC)** for `BaseWatcher`, not a `typing.Protocol`.

Components:
- **Inheritance model**: `abc.ABC` with `@abstractmethod` decorators on `poll()`, `process_item()`, and `validate_prerequisites()`
- **Shared implementation**: Retry logic (`_retry_with_backoff`), state persistence (`_load_state`/`_save_state`), structured logging (`_log`), file locking (`_acquire_lock`/`_release_lock`), and the main poll loop (`_run_poll_cycle`) live in the base class
- **Lifecycle contract**: `start()` validates prerequisites, loads state, acquires lock, enters async poll loop; `stop()` saves state, releases lock, logs shutdown
- **Configuration**: `poll_interval` (minimum 30s), `vault_path`, `name` set in `__init__`

## Consequences

### Positive

- Abstract methods enforced at class-definition time (not just at call time like Protocol) -- catches missing implementations immediately
- Shared implementation in the base class eliminates duplication across watchers (retry, state, logging, locking are write-once)
- Future watchers (CalendarWatcher, WhatsAppWatcher) get full infrastructure by inheriting -- SC-007 targets <50 lines of watcher-specific code
- Clear IDE support: subclass stubs generated automatically, type checking catches incomplete implementations
- Matches Constitution Principle VI language exactly ("inherit from common BaseWatcher class")

### Negative

- Tight coupling: subclasses are bound to the base class implementation, not just the interface
- Multiple inheritance becomes complex if a watcher needs other base classes (unlikely in this project)
- Harder to mock in tests compared to Protocol (must subclass rather than just implement methods) -- mitigated by creating a `MockWatcher` test helper
- If base class assumptions change (e.g., state format), all subclasses must adapt

## Alternatives Considered

**Alternative A: `typing.Protocol` (structural subtyping)**
- Pros: Loose coupling, easy to mock, no inheritance required
- Cons: No shared implementation -- each watcher reimplements retry, state, logging; no enforcement at definition time (errors only at call sites); doesn't match Constitution wording
- Rejected: The volume of shared logic (retry, state, logging, locking) makes Protocol impractical -- it would lead to massive duplication

**Alternative B: Plain duck typing (no formal contract)**
- Pros: Maximum flexibility, zero framework
- Cons: No compile-time or definition-time enforcement; shared logic scattered or duplicated; no discoverability for new developers
- Rejected: Unacceptable for a multi-watcher system where consistency is a core requirement

**Alternative C: Mixin pattern (separate ABC + mixin classes)**
- Pros: Separates interface from implementation, more composable
- Cons: Over-engineered for 3-5 watchers; Python mixins have MRO complexity; harder to understand lifecycle
- Rejected: YAGNI -- premature abstraction for the current phase

## References

- Feature Spec: `specs/005-gmail-watcher/spec.md` (FR-001, FR-016, SC-007)
- Implementation Plan: `specs/005-gmail-watcher/plan.md`
- Related ADRs: None (first ADR)
- Constitution: `.specify/memory/constitution.md` Principle VI (Watcher Architecture)
