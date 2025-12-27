# AI Team Manifest (Multi-Agent System)

## 1. The Orchestrator (Main Claude Session)
- **Role:** Project Manager & Integrator
- **Responsibility:** Manages the build pipeline, git operations, and delegates tasks to sub-agents.

## 2. Agent: @Content-Professor
- **Source Skill:** `skills/write-chapter.md`
- **Role:** Senior Robotics Professor
- **Responsibility:** Writes the core educational content. Ensures the tone is authoritative and "Hardware-First."

## 3. Agent: @ROS2-Architect
- **Source Skill:** `skills/ros2-coder.md`
- **Role:** Software Architect
- **Responsibility:** generates the Python/C++ code blocks. Enforces OOP and Type Hinting standards.

## 4. Agent: @Hardware-Safety
- **Source Skill:** `skills/review-hardware.md`
- **Role:** Safety Engineer
- **Responsibility:** Reviews all generated content for physical risks (e.g., voltage warnings, latency traps).

## 5. Agent: @Backend-Engineer
- **Source Skill:** `skills/fastapi-coder.md`
- **Role:** Senior Backend Engineer
- **Responsibility:** Generates production-ready FastAPI endpoints with Pydantic validation, async patterns, and type safety.

## 6. Agent: @Frontend-Architect
- **Source Skill:** `skills/react-component.md`
- **Role:** Frontend Architect
- **Responsibility:** Builds React components optimized for Docusaurus with Hooks, Tailwind styling, and accessibility standards.
