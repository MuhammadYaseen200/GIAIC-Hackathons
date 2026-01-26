# AI Control Directory

**Version**: 1.0.0
**Created**: 2026-01-25
**Constitution Compliance**: v2.0.0
**AAIF Standard**: Compliant

---

## Purpose

This directory contains **behavioral constitutions** and **governance protocols** for AI agent orchestration in the Evolution of Todo project. These files define how different AI agents (Claude, Gemini, Codex, Swarm) interact with the codebase, enforce Spec-Driven Development principles, and maintain architectural consistency across all phases.

The `ai-control/` directory serves as the **central nervous system** for agent behavior, ensuring that regardless of which AI vendor or model is invoked, all agents adhere to the project's core principles: specification-first development, brownfield evolution, and intelligence capture.

---

## Relationship to Root AGENTS.md

### Root AGENTS.md (Vendor-Neutral Canonical)
The root `AGENTS.md` file contains:
- **AAIF (Agent Architecture Instruction Format)** standard compliance
- **Spec-Kit Plus workflow** overview (Specify → Plan → Tasks → Implement)
- **Universal agent protocols** applicable across all AI vendors
- **High-level orchestration principles** (lead-architect, spec-architect, etc.)

### ai-control/REGISTRY.md (Agent-Specific Governance)
The `REGISTRY.md` file in this directory contains:
- **Vendor-specific configuration** (Claude Opus/Sonnet, Gemini Flash/Pro, etc.)
- **Model-to-role mappings** (which model handles which agent persona)
- **Tool access permissions** (which agents can invoke MCP tools, Kubernetes commands, etc.)
- **Context budgets** and **rate limits** per agent

**Key Distinction**: Root AGENTS.md defines *what* agents should do (universal principles). `ai-control/REGISTRY.md` defines *how* each specific vendor/model executes those principles.

---

## File Manifest

### 1. **CLAUDE.md**
Anthropic Claude-specific instructions, including:
- Model selection logic (Opus 4.5 for architecture, Sonnet 4.5 for implementation)
- Claude Code CLI integration patterns
- Extended thinking mode usage for complex decisions
- MCP tool invocation standards

### 2. **GEMINI.md**
Google Gemini-specific instructions, including:
- Gemini 2.5 Flash vs Pro model routing
- Deep Research integration for specification phase
- Multimodal reasoning for diagram generation
- Execution sandbox configuration

### 3. **CODEX.md**
OpenAI Codex/GPT-specific instructions, including:
- GPT-4 Turbo vs GPT-4o model selection
- Code Interpreter tool usage patterns
- Function calling standards for MCP tools
- Streaming response handling

### 4. **SWARM.md**
Multi-agent orchestration framework, including:
- Agent handoff protocols (when spec-architect delegates to backend-builder)
- Shared context management across agent switches
- Conflict resolution when agents disagree
- Parallel task execution rules

### 5. **REGISTRY.md**
**Central governance registry** containing:
- Agent role definitions (lead-architect, spec-architect, backend-builder, etc.)
- Model-to-agent mappings (which vendor/model fulfills each role)
- Tool access control lists (MCP tools, Bash commands, file operations)
- Context window budgets and cost optimization rules

### 6. **SKILLS.md**
Reusable agent skills library index, including:
- Skill catalog (P+Q+P format: Persona + Questions + Principles)
- Invocation syntax for each skill (`/commit`, `/review-pr`, `/spec-architect`)
- Skill dependency chains (which skills can invoke other skills)
- Skill versioning and deprecation tracking

### 7. **MCP.md**
Model Context Protocol implementation guidelines, including:
- MCP server discovery and registration
- Tool schema validation requirements
- Error handling standards for tool failures
- Security protocols for tool invocation

### 8. **LOOP.md**
Agent loop control and safety protocols, including:
- Maximum iteration limits per task
- Infinite loop detection patterns
- Circuit breaker triggers (cost, time, context overflow)
- Graceful degradation strategies when loops are detected

---

## Usage

### When Files Are Loaded

| File | Auto-Loaded By | Trigger |
|------|---------------|---------|
| `CLAUDE.md` | Claude Code CLI | On session start |
| `GEMINI.md` | Gemini API clients | On agent invocation |
| `CODEX.md` | OpenAI API clients | On agent invocation |
| `SWARM.md` | All agents | On multi-agent task detection |
| `REGISTRY.md` | Orchestration layer | On project initialization |
| `SKILLS.md` | All agents | On skill invocation (`/command`) |
| `MCP.md` | MCP tool servers | On tool registration |
| `LOOP.md` | All agents | On task iteration start |

### Invocation Examples

```bash
# Claude Code auto-loads CLAUDE.md and REGISTRY.md
claude-code --agent spec-architect

# Gemini Deep Research loads GEMINI.md and REGISTRY.md
gemini-research --phase specify

# Multi-agent task triggers SWARM.md
orchestrator run --agents spec-architect,backend-builder
```

### Referenced in Constitution

The `.specify/memory/constitution.md` (project constitution) references this directory:

```markdown
## Agent Orchestration
See `ai-control/REGISTRY.md` for model-to-role mappings.
See `ai-control/SWARM.md` for handoff protocols.
```

---

## Maintenance

### Amendment Protocol

All files in `ai-control/` are **governance artifacts** and follow the same amendment process as the root constitution:

1. **Proposal**: Document rationale in a new spec (e.g., `specs/governance/update-registry.md`)
2. **Review**: QA Overseer validates against constitution v2.0.0
3. **PHR Creation**: Record decision in `history/prompts/constitution/PHR-<date>.md`
4. **Amendment**: Update file with version bump (e.g., `REGISTRY.md v1.0.0 → v1.1.0`)
5. **Commit**: Include constitution reference in commit message

### Version Control

Each file includes a version header:

```markdown
**Version**: 1.0.0
**Last Amended**: 2026-01-25
**Ratified By**: lead-architect
```

### Deprecation

When a vendor is retired (e.g., Codex replaced by newer models):
1. Add `[DEPRECATED]` tag to filename (e.g., `CODEX.md` → `CODEX.deprecated.md`)
2. Document replacement in `REGISTRY.md`
3. Create ADR in `history/adr/` explaining rationale

---

## AAIF Compliance

All governance files adhere to the **Agent Architecture Instruction Format (AAIF)** standard:

- **Persona Definition**: Each file defines agent identity and cognitive stance
- **Reasoning Questions**: Structured decision-making frameworks
- **Operational Principles**: Clear, actionable rules
- **Constraints**: Explicit boundaries and safety protocols

This ensures vendor portability: if Claude becomes unavailable, Gemini can assume the same role by following the same governance files.

---

## Directory Structure

```
ai-control/
├── README.md          # This file
├── REGISTRY.md        # Central agent governance registry
├── CLAUDE.md          # Anthropic Claude instructions
├── GEMINI.md          # Google Gemini instructions
├── CODEX.md           # OpenAI Codex/GPT instructions
├── SWARM.md           # Multi-agent orchestration
├── SKILLS.md          # Reusable skills library index
├── MCP.md             # Model Context Protocol guidelines
└── LOOP.md            # Agent loop control protocols
```

---

## Quick Reference

| Need | File to Consult |
|------|----------------|
| Which model handles spec writing? | `REGISTRY.md` |
| How does Claude invoke MCP tools? | `CLAUDE.md` |
| What happens when agents disagree? | `SWARM.md` |
| How to prevent infinite loops? | `LOOP.md` |
| Which skills are available? | `SKILLS.md` |
| MCP tool schema validation? | `MCP.md` |

---

**Maintained by**: The Librarian (Technical Archivist)
**Governed by**: Evolution of Todo Constitution v2.0.0
**Contact**: See `AGENTS.md` for agent role assignments
