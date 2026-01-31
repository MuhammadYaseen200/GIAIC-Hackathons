# Data Model: verify-env.py Validation System

**Feature**: 002-fix-verify-env-validation
**Date**: 2026-01-27

---

## Overview

The validation system uses a profile-based architecture where each phase (Phase 2, Phase 3, etc.) has a distinct validation profile defining required/optional variables and database format constraints.

---

## Entity: ValidationProfile

Represents a phase-specific set of validation rules.

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `phase_id` | `int \| None` | Yes | Phase number (2, 3, etc.) or None for generic mode |
| `phase_name` | `str` | Yes | Human-readable phase name |
| `required_vars` | `list[str]` | Yes | Environment variables that MUST exist |
| `optional_vars` | `list[str]` | Yes | Environment variables that MAY exist (checked but not required) |
| `database_formats` | `list[str]` | Yes | Allowed DATABASE_URL schemes (base scheme before '+') |
| `description` | `str` | Yes | Displayed to user when validation runs |

### Validation Rules

- `phase_id` must be unique across all profiles (or None for generic)
- `required_vars` must not be empty (except for generic mode)
- `database_formats` must contain at least one valid scheme
- Variable names in `required_vars` and `optional_vars` must not overlap

### Example Instances

**Phase 2 Profile**:
```python
{
    'phase_id': 2,
    'phase_name': 'Phase 2 Web',
    'required_vars': ['DATABASE_URL', 'SECRET_KEY', 'NEXTAUTH_SECRET'],
    'optional_vars': [],
    'database_formats': ['postgresql', 'postgres'],
    'description': 'Full-stack web application with NextAuth'
}
```

**Phase 3 Profile**:
```python
{
    'phase_id': 3,
    'phase_name': 'Phase 3 Chatbot',
    'required_vars': ['DATABASE_URL', 'OPENROUTER_API_KEY', 'SECRET_KEY'],
    'optional_vars': ['NEXTAUTH_SECRET', 'GEMINI_API_KEY'],
    'database_formats': ['sqlite', 'postgresql', 'postgres'],
    'description': 'AI chatbot with OpenRouter + SQLite/PostgreSQL'
}
```

**Generic Profile**:
```python
{
    'phase_id': None,
    'phase_name': 'Generic',
    'required_vars': ['DATABASE_URL'],
    'optional_vars': [],
    'database_formats': ['sqlite', 'postgresql', 'postgres', 'mysql', 'mariadb'],
    'description': 'Generic validation for unknown projects (DATABASE_URL only)'
}
```

---

## Entity: ValidationResult

Represents the outcome of a validation run.

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `success` | `bool` | Yes | Overall validation status (True = all checks passed) |
| `phase_detected` | `int \| None` | Yes | Which phase was auto-detected (None if no phase dirs found) |
| `phase_used` | `int \| None` | Yes | Which profile was actually used for validation (accounts for `--phase` override) |
| `errors` | `list[tuple[str, str, str]]` | Yes | List of errors: (var_name, error_msg, fix_hint) |
| `warnings` | `list[str]` | Yes | Non-critical issues (e.g., "python-dotenv not found") |
| `exit_code` | `int` | Yes | Exit code to return (0 = success, 2 = failure, 1 = execution error) |

### Validation Rules

- `success` is False if `errors` is non-empty
- `phase_used` may differ from `phase_detected` if `--phase` flag used
- `exit_code` must be 0, 1, or 2 (per ADR-013: Fail-Fast Environment Validation)
- `errors` tuples must have exactly 3 elements

### Example Instance

**Successful Validation**:
```python
{
    'success': True,
    'phase_detected': 3,
    'phase_used': 3,
    'errors': [],
    'warnings': [],
    'exit_code': 0
}
```

**Failed Validation (Missing Variables)**:
```python
{
    'success': False,
    'phase_detected': 3,
    'phase_used': 3,
    'errors': [
        ('DATABASE_URL', 'Missing required environment variable: DATABASE_URL', 'Add DATABASE_URL to .env file'),
        ('OPENROUTER_API_KEY', 'Missing required environment variable: OPENROUTER_API_KEY', 'Add OPENROUTER_API_KEY to .env file')
    ],
    'warnings': ['python-dotenv not found - .env file will not be auto-loaded'],
    'exit_code': 2
}
```

**Manual Override**:
```python
{
    'success': True,
    'phase_detected': 3,
    'phase_used': 2,  # User specified --phase 2
    'errors': [],
    'warnings': ['Using manual phase override (--phase 2)'],
    'exit_code': 0
}
```

---

## Entity: EnvironmentVariable

Represents metadata about an environment variable for validation purposes.

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | Yes | Environment variable name (e.g., "DATABASE_URL") |
| `value` | `str \| None` | No | Current value from environment (None if not set) |
| `required` | `bool` | Yes | Whether this variable must be present |
| `phase_id` | `int \| None` | Yes | Which phase requires this variable |
| `format_hint` | `str \| None` | No | Expected format (e.g., "sqlite+aiosqlite:///<path>") |
| `fix_hint` | `str` | Yes | Actionable command/instruction to fix if missing |

### Validation Rules

- `name` must be uppercase with underscores (e.g., "DATABASE_URL", "SECRET_KEY")
- If `required` is True and `value` is None → validation error
- `fix_hint` must be actionable (command or clear instruction)

### Example Instances

**DATABASE_URL (Phase 3)**:
```python
{
    'name': 'DATABASE_URL',
    'value': 'sqlite+aiosqlite:///./todo_app.db',
    'required': True,
    'phase_id': 3,
    'format_hint': 'sqlite+aiosqlite:///<path> or postgresql+asyncpg://user:pass@host:port/db',
    'fix_hint': 'Add DATABASE_URL to .env file'
}
```

**OPENROUTER_API_KEY (Phase 3)**:
```python
{
    'name': 'OPENROUTER_API_KEY',
    'value': 'sk-or-v1-abc123...',
    'required': True,
    'phase_id': 3,
    'format_hint': 'sk-or-v1-<hex>',
    'fix_hint': 'Get API key from https://openrouter.ai/keys'
}
```

**NEXTAUTH_SECRET (Phase 2)**:
```python
{
    'name': 'NEXTAUTH_SECRET',
    'value': None,  # Not set
    'required': True,
    'phase_id': 2,
    'format_hint': 'String (32+ characters)',
    'fix_hint': 'Generate with: openssl rand -hex 32'
}
```

---

## Relationships

```
ValidationProfile (1) ----< (N) EnvironmentVariable
  phase_id                    phase_id

ValidationResult (1) ----> (1) ValidationProfile
  phase_used                 phase_id
```

**Explanation**:
- Each **ValidationProfile** defines N **EnvironmentVariable** requirements
- Each **ValidationResult** references exactly one **ValidationProfile** that was used for validation

---

## State Transitions

### Phase Detection State Machine

```
START
  ↓
[Check CLI args]
  ↓
  ├─ --phase provided? → [Use manual override] → END (phase_used = manual value)
  ↓
  └─ No CLI arg
      ↓
     [Scan directories]
      ↓
      ├─ phase-3-chatbot/ exists? → [Use Phase 3] → END (phase_used = 3)
      ├─ phase-2-web/ exists? → [Use Phase 2] → END (phase_used = 2)
      ├─ phase-1-console/ exists? → [Use Phase 1] → END (phase_used = 1)
      └─ No phase dirs → [Use Generic] → END (phase_used = None)
```

### Validation Execution State Machine

```
START
  ↓
[Load Profile]
  ↓
[Check Required Variables]
  ↓
  ├─ All present? → Continue
  └─ Missing? → Add to errors[]
      ↓
[Check Optional Variables]
  ↓
  └─ Missing? → Log info (not error)
      ↓
[Validate DATABASE_URL Format]
  ↓
  ├─ Valid scheme? → Continue
  └─ Invalid? → Add to errors[]
      ↓
[Check python-dotenv]
  ↓
  └─ Not installed? → Add to warnings[]
      ↓
[Generate Result]
  ↓
  ├─ errors[] empty? → success = True, exit_code = 0
  └─ errors[] not empty? → success = False, exit_code = 2
      ↓
END
```

---

## Data Constraints

### Validation Profile Constraints

1. **Uniqueness**: `phase_id` must be unique across all profiles
2. **Completeness**: All attributes required (no None values except for `phase_id` in generic mode)
3. **Non-Empty Lists**: `required_vars` must have at least one item (except generic mode)
4. **Valid Schemes**: `database_formats` must contain recognized schemes (sqlite, postgresql, mysql, etc.)

### Environment Variable Constraints

1. **Naming Convention**: Variable names must match pattern `^[A-Z_]+$`
2. **No Duplicates**: A variable cannot be both required and optional in same profile
3. **Fix Hints**: Must be actionable (command or clear instruction)

### Validation Result Constraints

1. **Exit Code Range**: Must be 0, 1, or 2 (per ADR-013)
2. **Error Consistency**: If `errors` is non-empty, `success` must be False
3. **Phase Consistency**: `phase_used` must match a valid profile's `phase_id` or None

---

## Implementation Notes

**Python Data Structures**:
- ValidationProfile: Python dict
- ValidationResult: Python dict
- EnvironmentVariable: Not explicitly stored (checked on-the-fly)
- Profile registry: Constant `VALIDATION_PROFILES = {2: {...}, 3: {...}}`

**No Persistence**: All data structures are in-memory during script execution. No database, no file storage.

**Thread Safety**: Not applicable (single-threaded CLI script).

---

## Summary

| Entity | Purpose | Lifecycle |
|--------|---------|-----------|
| ValidationProfile | Define phase-specific rules | Static (hardcoded constant) |
| ValidationResult | Store validation outcome | Created during `main()`, used for output/exit code |
| EnvironmentVariable | Metadata for validation | Implicit (not stored, just checked) |

**Total Profiles**: 3 (Phase 2, Phase 3, Generic) initially; expandable for Phase 4, Phase 5

**Total Variables Tracked**: ~10 across all profiles (DATABASE_URL, SECRET_KEY, NEXTAUTH_SECRET, OPENROUTER_API_KEY, GEMINI_API_KEY, etc.)
