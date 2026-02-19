# **📘 ULTIMATE PROJECT BLUEPRINT (V2 \- Claude CLI & Skills Edition)**

*Complete hierarchical structure of your full system \+ agent ecosystem \+ hackathon plan \+ The "Intelligence Engine"*

---

# **\#️⃣ 0\. PROJECT VISION**

Build a **Fully Agentic Learning System** where:

* **Claude CLI is the Orchestrator:** It serves as the primary interface for all development, testing, and agent management.  
* **The Website IS an Agent:** Not just static code, but a living system.  
* **Reusable Intelligence:** No work is lost. Every spec, prompt, and decision is documented in Docusaurus (Markdown) to be reused by future agents.  
* **Skill-Based Architecture:** Agents utilize a library of **Modular Skills** (defined capabilities) rather than just raw prompting.  
* **RAG \+ Agent SDK:** The "Brain" of the ecosystem.  
* **Spec-Driven Development (SDD):** Specification → Planning → Tasks → Implementation.  
* **95% AI / 5% Human:** You direct; Claude CLI executes.

---

# **\#️⃣ 1\. HACKATHON PRE-SETUP (Highest Priority)**

## **1.1 MCP Server Setup (Foundation)**

Required MCP servers to give Claude CLI "hands":

* **Context-7 MCP**  
* **Playwright MCP** (Testing/Browsing)  
* **GitHub MCP** (Repo management)  
* **File System MCP** (Reading/Writing code)  
* **Knowledge Base MCP** (RAG embeddings)  
* **Tools MCP** (Bash execution)

## **1.2 The "Intelligence Engine" Setup (NEW)**

Before coding, establish the **Claude CLI Workflow**:

1. **Skills Library (`/skills`):** Create a folder of reusable prompts/scripts (e.g., `generate_spec.md`, `review_pr.md`, `extract_knowledge.md`).  
2. **Memory Bank (`/docs`):** Ensure Docusaurus is configured not just for users, but as the **Long-term Memory** for Claude.  
3. **CLI Config:** Configure Claude CLI to auto-load the project context and skills on startup.

---

# **\#️⃣ 2\. AGENT EMPIRE (The Hierarchy)**

*Agents are essentially **Claude CLI Sessions** initialized with specific **Skills** and **Context**.*

## **2.1 CORE LEADERSHIP AGENTS**

* **Lead Agent:** (Uses *Strategy Skill*) \- Approves Specs.  
* **Manager Agent:** (Uses *Breakdown Skill*) \- Assigns Tasks.  
* **QA/QC Agents:** (Uses *Testing Skill*) \- Verifies output.

## **2.2 PLANNING & SPECIFICATION AGENTS**

* **Specification Agent:** (Uses *Spec-Writer Skill*) \- Writes rigorous markdown specs.  
* **Planning Agent:** (Uses *Roadmap Skill*) \- Estimates timeline.

## **2.3 CONTENT & CREATIVE AGENTS**

* **Writer Agent:** (Uses *Copywriting Skill*) \- Professional tone.  
* **Research Agent:** (Uses *RAG Skill*) \- Fetches true info.

## **2.4 TECHNICAL AGENTS**

* **Backend/Frontend Agents:** (Uses *Coding Skills* via MCP).  
* **Integration Agent:** Connects MCPs and APIs.  
* **Docusaurus Agent:** **(CRITICAL)** \- The guardian of Reusable Intelligence. Ensures all learnings are committed to `/docs`.

---

# **\#️⃣ 3\. THE "REUSABLE INTELLIGENCE" LIFECYCLE**

*How we ensure Claude gets smarter over time.*

1. **Specify:** Claude CLI reads the "Master Spec" (Reusable Intelligence).  
2. **Execute:** Claude CLI uses a "Skill" (e.g., *React Component Builder*) to write code.  
3. **Document:** Claude CLI updates `/docs` with how the feature was built.  
4. **Reuse:** The next time a similar feature is needed, Claude CLI reads that doc first.

**Framework:** `Constitution → Specification → Planning → Tasks → Implementation → Documentation (Memory)`

---

# **\#️⃣ 4\. PROJECT STRUCTURE**

/frontend  
/backend  
/docs          \<-- REUSABLE INTELLIGENCE (The Brain)  
/agents  
/rag  
/skills        \<-- CLAUDE CLI SKILLS (The Tools)  
   /coding  
   /writing  
   /testing  
/integrations  
/database

---

# **\#️⃣ 5\. CLAUDE CLI SKILLS LIBRARY**

*Instead of random prompting, we build a library of repeatable skills.*

### **Core Skills to Create:**

* **`skill:generate-spec`**: Takes a user idea, outputs a standard MD spec.  
* **`skill:refactor-component`**: analyzing a React component and applying best practices.  
* **`skill:commit-knowledge`**: Summarizing a coding session and writing it to Docusaurus.  
* **`skill:rag-lookup`**: Querying the vector DB for specific knowledge.  
* **`skill:test-ui`**: Launching Playwright via MCP to screenshot and verify UI.

---

# **\#️⃣ 6\. ARCHITECTURE (Frontend & Backend)**

* **Frontend:** React.js \+ Tailwind (built by agents using *Frontend Skills*).  
* **Backend:** Node/Python \+ Vector DB (built by agents using *Backend Skills*).  
* **Docs:** Docusaurus (The Source of Truth).

---

# **\#️⃣ 7\. REUSABLE INTELLIGENCE & DOCUSAURUS**

**This is no longer just "Documentation." It is the System Prompt.**

* **Role:** The "Hippocampus" (Memory Center).  
* **Function:**  
  * Stores "Lessons Learned."  
  * Stores "Design Patterns."  
  * Stores "Business Rules."  
* **Workflow:** Before starting ANY task, Claude CLI must query Docusaurus to see if this problem has been solved before.

---

# **\#️⃣ 8\. FEATURE SET (Learning System)**

* Gamification (Levels, Streaks)  
* Adaptive Difficulty  
* **Teacher Mode:** (Gatekeeping mechanism)  
* **RAG Chatbot:** (The interface for the Reusable Intelligence)

---

# **\#️⃣ 9\. HACKATHON EXECUTION PLAN (Updated)**

## **DAY 1: Foundation & Intelligence**

* **Step 1:** Setup MCP Servers & Claude CLI.  
* **Step 2:** **Build Skills Library (`/skills`).** (Define the standard way to code).  
* **Step 3:** Setup Docusaurus as Reusable Intelligence storage.  
* **Step 4:** Generate Specs for Core Chapters (using `skill:generate-spec`).  
* **Step 5:** Repo Skeleton.

## **DAY 2: Implementation & Loop**

* **Step 6:** Implement RAG (Ingest the `/docs` created on Day 1).  
* **Step 7:** Backend/Frontend coding (using `skill:coding`).  
* **Step 8:** Personalization & Auth.  
* **Step 9:** **Feedback Loop:** Extract learnings from Day 2 and write back to `/docs`.  
* **Step 10:** Final Review Video.

---

# **\#️⃣ 10\. WHY THIS WORKS (The "Flywheel")**

1. **Claude CLI** executes faster than human typing.  
2. **Skills** ensure consistency (same quality every time).  
3. **Reusable Intelligence** means you never solve the same bug twice.  
4. **MCPs** give the agent God-mode access to your file system and browser.

---

# **\#️⃣ 11\. CONTENT SOURCE**

* Official Docs.  
* RAG Retrieval.  
* **Self-Generated Insights** (stored in Reusable Intelligence).

---

# **\#️⃣ 12\. FINAL NOTES**

This is the **Industrial-Grade Setup**.

* **Claude CLI** is the engine.  
* **Skills** are the fuel.  
* **Reusable Intelligence** is the map.

**Next Step:** Start your terminal, login to Claude CLI, and run: `mkdir skills docs`.

# **📘 UNIFIED PROJECT BLUEPRINT: Physical AI Textbook Agent System**

**Target:** Panaversity Hackathon | **Deadline:** Nov 30 | **Tool:** Claude Code & Spec-Kit Plus

---

## **\#️⃣ 0\. PROJECT VISION & SCORING STRATEGY**

* **Core Objective:** Build an AI-Native Textbook for "Physical AI & Humanoid Robotics" using Spec-Driven Development.  
* **The "Flywheel":** You are not just writing a book; you are building an *Agentic System* that writes the book and improves itself.  
* **Point Maximization Strategy (300 Total Points):**  
  * **Base (100):** Docusaurus Book \+ RAG Chatbot (Qdrant/Neon/FastAPI).  
  * **Bonus A (50):** Reusable Intelligence (Claude Code Sub-agents/Skills).  
  * **Bonus B (50):** Better-Auth (Signup/Login with Hardware Survey).  
  * **Bonus C (50):** Personalization (Content adapts to User Hardware).  
  * **Bonus D (50):** Urdu Translation (One-click toggle).

---

## **\#️⃣ 1\. CLAUDE CLI WORKFLOW (The "Engine")**

*Strict adherence to MCP-First logic.*

### **Phase 1: Connection & Foundation**

1. **Connect MCPs:** Filesystem, GitHub, Playwright (for UI testing), Context-7.  
2. **Initialize Structure:** `spec-kit-plus` boilerplate.  
3. **Define Memory:** Configure `/docs` not just as the book output, but as the *system memory* for the agent.

### **Phase 2: Skill Fabrication (The 50pt Bonus)**

*Create these executable Markdown files in `/skills`:*

* `skill:generate-chapter`: Prompt template that takes a Course Module (e.g., ROS 2\) and outputs Docusaurus MDX.  
* `skill:rag-ingest`: Script to chunk book content and upsert to Qdrant.  
* `skill:deploy-component`: Standard procedure to add a React component (like the Chat widget) to Docusaurus.  
* `skill:translate-urdu`: A specialized prompt to take an MDX file and generate an Urdu variant while preserving code blocks.

---

## **\#️⃣ 2\. SYSTEM ARCHITECTURE**

### **Frontend (The Book)**

* **Framework:** Docusaurus (React-based static site).  
* **Hosting:** GitHub Pages / Vercel.  
* **Interactivity:** React Components for "Personalize," "Translate," and "Chat."

### **Backend (The Intelligence)**

* **Auth:** Better-Auth (handling user session & metadata).  
* **Database:** Neon (Serverless Postgres) for user data (Hardware Profile).  
* **Vector DB:** Qdrant Cloud (Free Tier) for Book Embeddings.  
* **API:** FastAPI (Python) to bridge ChatKit SDK and the Database.

---

## **\#️⃣ 3\. AGENT HIERARCHY (Claude CLI Sessions)**

*Direct Claude to assume these roles using the Context-7 MCP.*

* **Lead Architect Agent:** Maintains the `master-plan.md` and assigns modules.  
* **Curriculum Agent:** Reads the "Physical AI" syllabus and creates chapter specs.  
* **DevOps Agent:** Manages GitHub Actions, Vercel deployments, and Qdrant connections.  
* **UX Agent:** Implements the "Translation Toggle" and "Personalization Button" in React.

---

## **\#️⃣ 4\. CONTENT STRATEGY (The "Physical AI" Syllabus)**

*The Curriculum Agent must generate specs for these modules:*

* **Module 1: The Robotic Nervous System (ROS 2\)**  
  * *Key Concepts:* Nodes, Topics, URDF.  
  * *Lab:* Bridging Python Agents to ROS controllers.  
* **Module 2: The Digital Twin**  
  * *Tools:* Gazebo & Unity.  
  * *Simulations:* Gravity, Collisions, LiDAR.  
* **Module 3: The AI-Robot Brain**  
  * *Tools:* NVIDIA Isaac Sim & Nav2.  
  * *Hardware Focus:* RTX 4070 Ti requirements (Integration with Personalization Bonus).  
* **Module 4: Vision-Language-Action (VLA)**  
  * *Tech:* OpenAI Whisper, LLM Cognitive Planning.  
  * *Capstone:* The Autonomous Humanoid.

---

## **\#️⃣ 5\. IMPLEMENTATION PLAN (Hackathon Sprint)**

### **Day 1: Infrastructure & Reusable Intelligence (The "Skeleton")**

1. **Setup:** Repo init, MCP checks, Docusaurus install.  
2. **Skill Creation:** Write the `skill:generate-chapter` and `skill:commit-knowledge` scripts.  
3. **Auth Implementation:** Install Better-Auth. Create the "Sign Up" form asking:  
   * *Do you have an NVIDIA GPU? (Yes/No)*  
   * *Do you have a Jetson Orin? (Yes/No)*  
4. **Database:** Connect Neon and set up the User Schema.

### **Day 2: Content Generation & Personalization (The "Flesh")**

1. **Generate Chapters:** Run `skill:generate-chapter` for Modules 1-4.  
2. **Personalization Logic:**  
   * *If User GPU \= NULL:* Show "Cloud Workstation (AWS)" guide in Module 3\.  
   * *If User GPU \= RTX 4090:* Show "Local Sim" guide in Module 3\.  
3. **Translation Logic:**  
   * Implement `UseUrduContext` in React.  
   * Run `skill:translate-urdu` to generate `_ur.md` files for all chapters.

### **Day 3: RAG & Polish (The "Brain")**

1. **RAG Pipeline:** Script to scrape the generated Docusaurus site \-\> Embed \-\> Store in Qdrant.  
2. **Chat UI:** Embed the ChatKit widget in the Docusaurus layout.  
3. **Testing:** Use Playwright MCP (`skill:test-ui`) to verify the "Translate" button works and Auth flow succeeds.  
4. **Demo Video:** Record the 90s intro.

---

## **\#️⃣ 6\. REUSABLE INTELLIGENCE (The Memory Bank)**

*The critical differentiator for the Panaversity Team.*

* **Documentation Rule:** Every major decision (e.g., "How we implemented Better-Auth with Docusaurus") must be written to `/docs/engineering-handbook`.  
* **Self-Correction:** If Claude fails a task, it must write a "Post-Mortem" to `/docs/learnings` so it doesn't fail again.  
* **Manifesto:** The output is not just a book; it is a **documented process** for creating future books.

---

## **\#️⃣ 7\. FINAL CHECKLIST (For Nov 30 Submission)**

* \[ \] Public GitHub Repo.  
* \[ \] Live URL (Vercel/GitHub Pages).  
* \[ \] Chatbot answers questions about "NVIDIA Isaac" correctly.  
* \[ \] "Translate to Urdu" button functions.  
* \[ \] Signup form collects Hardware Data.  
* \[ \] Content changes based on Hardware Data.  
* \[ \] 90s Demo Video.

