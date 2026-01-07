# PHR-011: Deployment Pre-Flight Check Skill Creation

**Date**: 2026-01-03
**Phase**: Phase 2 Post-Mortem
**Agents Used**: @skill-creator (manual due to encoding error)
**Duration**: ~15 minutes
**Status**: COMPLETE

---

## Context

After completing Phase 2 retrospective (PHR-010), identified that deployment failures could have been prevented with pre-flight checks. Created a reusable skill to validate deployment artifacts before pushing to Vercel.

## Problem Statement

Phase 2 deployment encountered several preventable errors:
1. `pydantic_core._pydantic_core` import error due to `uv.lock` conflict
2. `CORS_ORIGINS` Pydantic validation error due to wrong format
3. Credential exposure risk from `settings.local.json`

## Solution

Created `/sp.preflight-check` skill with:
- SKILL.md documentation
- Automated Python validation script
- 5 check categories

## Skill Structure

```
.claude/skills/deployment-preflight-check/
├── SKILL.md              # Skill documentation
└── scripts/
    └── preflight_check.py  # Automated validation script
```

## Check Categories

| Check | Purpose | Prevents |
|-------|---------|----------|
| lockfiles | Detect uv.lock/poetry.lock conflicts | Binary dependency crashes |
| credentials | Scan for hardcoded secrets | Credential leaks |
| env-schema | Validate .env.example vs config.py | Type mismatch errors |
| cors | Validate CORS_ORIGINS format | Pydantic validation errors |
| gitignore | Verify .gitignore completeness | Accidental commits |

## Test Results

Ran against `phase-2-web/backend/`:

```
PASSED:
  [OK] No conflicting lock files found
  [OK] Environment schema validation complete
  [OK] CORS_ORIGINS is valid JSON array with 1 origins

ERRORS:
  [FAIL] Potential credentials found in tracked files:
       - comprehensive_test.py: Hardcoded password
  [FAIL] Missing required .gitignore patterns:
       - node_modules (Node modules)
```

Script correctly identified issues that should be addressed.

## Technical Note

The `init_skill.py` script from skill-creator failed with:
```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680'
```

Workaround: Manually created skill directory structure instead of using init script.

## Usage

```bash
# Full preflight check
python .claude/skills/deployment-preflight-check/scripts/preflight_check.py --path ./backend

# Specific check
python .claude/skills/deployment-preflight-check/scripts/preflight_check.py --path ./backend --check credentials
```

## Integration Points

Use this skill:
1. Before `vercel --prod` - Run full preflight
2. Before `git push origin main` - Run credentials check
3. After modifying `requirements.txt` - Run lockfiles check
4. After modifying `.env.example` - Run env-schema check

## Files Created

| File | Purpose |
|------|---------|
| `.claude/skills/deployment-preflight-check/SKILL.md` | Skill documentation |
| `.claude/skills/deployment-preflight-check/scripts/preflight_check.py` | Validation script |
| `history/prompts/phase-2-web/PHR-011-deployment-preflight-skill.md` | This PHR |

## Lessons Applied

This skill directly addresses Improvement 1 from the retrospective (phase-2-retrospective.md):
> Create Deployment Pre-Flight Skill

---

**End of PHR-011**
