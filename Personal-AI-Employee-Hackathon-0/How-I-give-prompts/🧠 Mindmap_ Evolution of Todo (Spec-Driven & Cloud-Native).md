---

# **🧠 Dynamic Mind Map: The Evolution of Todo**

## **🗺️ 1\. Prerequisites & Resource Allocation**

*Before writing code, we configure the "Intelligence Infrastructure".*

### **1.1 Agent Orchestration (Role Assignment)**

* **lead-architect (Opus):** High-level strategy, constitution management, and phase transition planning.  
* **spec-architect (Opus):** Writing/refining .md specs in specs/features/ and specs/api/.  
* **backend-builder (Opus):** Python, FastAPI, SQLModel, and MCP server implementation.  
* **ux-frontend-developer (Sonnet):** Next.js 16, Tailwind, and Better Auth integration.  
* **devops-rag-engineer (Sonnet):** Docker, Kubernetes (Minikube/DOKS), Helm, and Kafka/Dapr setup.  
* **qa-overseer (Opus):** Validating "Acceptance Criteria" from specs.

### **1.2 Critical Skills & MCPs**

* **Required Skills:**  
  * skill-creator: To generate project-specific reusable skills (e.g., a skill to generate Helm charts).  
  * mcp-builder: For Phase III (building the Todo MCP Server).  
  * doc-coauthoring / brand-guidelines: For documentation and maintaining consistent UI/UX.  
* **Active MCPs:**  
  * filesystem: Essential for monorepo file management.  
  * github: For PRs and issue tracking (/sp.taskstoissues).  
  * ragie: For indexing documentation (Hackathon PDF) to query requirements instantly.

### **1.3 Environment Setup**

* **Monorepo Strategy:** hackathon-todo/ root.  
  * Global .spec-kit/config.yaml.  
  * Shared specs/ folder.  
* **CLI Tools:** uv (Python), npm (Node), docker, minikube, kubectl, helm.

---

## **🚀 2\. Phase I: The Greenfield Foundation**

*Goal: In-Memory Python Console App | Deadline: Dec 7*

* **Workflow:** Greenfield SDD  
  * **Step 1: Specification (/sp.specify)**  
    * Define specs/features/core-crud.md (Add, Delete, Update, View, Mark Complete).  
    * Define specs/architecture.md (In-memory dict structure).  
  * **Step 2: Planning (/sp.plan)**  
    * Create plan.md: Define Python class structure (TodoService, TodoApp).  
  * **Step 3: Implementation (/sp.implement)**  
    * Use backend-builder agent.  
    * Stack: Python 3.13+, typer or cmd module.  
  * **Step 4: Documentation**  
    * Generate CLAUDE.md (Root) with Python running instructions.  
    * Generate README.md.

---

## **🔄 3\. Phase II: The Brownfield Evolution (Web)**

*Goal: Full-Stack Web App (Next.js \+ FastAPI \+ DB) | Deadline: Dec 14*

* **Transition Strategy:** **"Safe Brownfield Adoption"**  
  * *Constraint:* Phase I code exists. We must evolve it, not destroy logic.  
  * **Action:** cp CLAUDE.md CLAUDE.md.backup \-\> specifyplus init \--here \-\> Merge Constitution.  
* **Workflow:** Brownfield SDD  
  * **Step 1: Refactor Spec**  
    * Update specs/architecture.md: Move from In-Memory \-\> SQLModel (Neon DB).  
    * Create specs/api/rest-endpoints.md: Define API contract.  
    * Create specs/ui/pages.md: Next.js App Router structure.  
  * **Step 2: Plan Migration**  
    * Plan: Move Phase I logic into backend/app/services/.  
    * Plan: Setup frontend/ directory.  
  * **Step 3: Implementation**  
    * **Backend:** Implement FastAPI, better-auth (JWT verification), SQLModel.  
    * **Frontend:** Next.js \+ Tailwind \+ Better Auth Client.  
  * **Step 4: Verification**  
    * qa-overseer checks if Phase I features still work in Phase II web format.

---

## **🤖 4\. Phase III: The Intelligence Layer**

*Goal: AI Chatbot via MCP & Agents SDK | Deadline: Dec 21*

* **Transition Strategy:** **"Layering Intelligence"**  
  * The Web App (Phase II) becomes the "Tool Provider".  
* **Workflow:** Agentic SDD  
  * **Step 1: Spec MCP Tools**  
    * Create specs/api/mcp-tools.md: Map CRUD operations to MCP Tools (add\_task, list\_tasks).  
  * **Step 2: Architecture Plan**  
    * Design **Stateless Agent Architecture**:  
      * User sends msg \-\> Backend \-\> DB (Load History) \-\> Agent \-\> MCP Tool \-\> DB (Save State) \-\> Response.  
  * **Step 3: Implementation**  
    * **MCP Server:** Use Official MCP SDK to expose FastAPI logic as tools.  
    * **Agent:** OpenAI Agents SDK integration.  
    * **UI:** OpenAI ChatKit integration in Next.js.  
  * **Step 4: Brownfield Check**  
    * Ensure existing REST API still functions alongside new Chat API.

---

## **🐳 5\. Phase IV: Local Ops (Containerization)**

*Goal: Local K8s (Minikube) & Docker AI | Deadline: Jan 4*

* **Transition Strategy:** **"Infrastructure as Code"**  
  * The code doesn't change much; the *wrapper* changes.  
* **Workflow:** DevOps SDD  
  * **Step 1: Spec Infrastructure**  
    * Create specs/infra/kubernetes.md: Define Pods, Services, Ingress.  
  * **Step 2: Docker AI (Gordon) Integration**  
    * Use docker ai to generate optimized Dockerfile for Frontend and Backend.  
  * **Step 3: K8s Implementation**  
    * Use kubectl-ai / kagent to generate Helm Charts.  
    * Deploy: frontend pod, backend pod, postgres (local) or external link.  
  * **Step 4: Verification**  
    * Test functionality inside Minikube tunnel.

---

## **☁️ 6\. Phase V: Cloud Scale (Distributed Systems)**

*Goal: DOKS, Kafka, Dapr, Event-Driven | Deadline: Jan 18*

* **Transition Strategy:** **"Decoupling"**  
  * Monolithic API \-\> Microservices event bus.  
* **Workflow:** Distributed SDD  
  * **Step 1: Spec Event Architecture**  
    * Create specs/architecture/events.md: Define Topics (task-events, reminders).  
    * Define Dapr Components (pubsub.kafka, statestore).  
  * **Step 2: Advanced Features Plan**  
    * Recurring Tasks (Event Triggered).  
    * Reminders (Cron Binding).  
  * **Step 3: Implementation**  
    * Deploy **Redpanda** (Kafka).  
    * Implement **Dapr Sidecars** in K8s manifests.  
    * Refactor Backend to publish events via Dapr HTTP API (instead of direct logic).  
  * **Step 4: Cloud Deploy**  
    * Push to DigitalOcean Container Registry.  
    * Deploy Helm charts to DOKS.

---

## **💎 Bonus: Reusable Intelligence & Blueprints**

*Goal: \+600 Points | Continuous Integration*

* **Strategy:** Throughout Phases III-V.  
* **Task:**  
  1. **Subagent Creation:** Create a .claude/agents/todo-expert.json that "knows" the Todo project architecture specifically.  
  2. **Blueprints:** Create a specs/blueprints/k8s-deployment.md that acts as a reusable pattern for future deployments.  
  3. **Voice/Urdu:** Add as additional "Skills" or MCP tools in Phase III.

---

## **⚡ Execution Workflow (For Every Phase)**

1. **/sp.specify**: Write the .md spec.  
2. **/sp.clarify**: Let spec-architect ask YOU questions to fix holes.  
3. **/sp.plan**: Generate plan.md and tasks.md.  
4. **/sp.taskstoissues**: Push tasks to GitHub Issues (Project Management).  
5. **/sp.implement**:  
   * Agent picks a task.  
   * Reads CLAUDE.md (Constitution).  
   * Writes Code.  
   * Runs Tests.  
6. **/sp.git.commit\_pr**: Commit working code.  
7. **Transition:** Backup CLAUDE.md, move to next phase folder/branch, run Brownfield Protocol.

---

