# UI Specification: Pages and Components

**Status**: Draft
**Owner**: Frontend Team (ux-frontend-developer)
**Dependencies**: REST API Spec (rest-endpoints.md), Authentication Spec
**Estimated Complexity**: Medium
**Created**: 2025-12-29
**Phase**: Phase II - Full-Stack Web Application

---

## 1. Purpose & Context

- **What**: Next.js 15+ App Router pages and React components for the Todo application UI
- **Why**: Provide authenticated users with a web interface to manage their tasks
- **Where**: Frontend application (`/frontend`) consuming the FastAPI backend (`/api/v1/tasks/*`)

---

## 2. Constraints (MANDATORY)

### NOT Supported (v1)

- Drag-and-drop task reordering
- Offline mode / Service Worker caching
- Real-time collaborative editing
- Mobile-native gestures (swipe-to-delete)
- Dark mode toggle (Phase V scope)
- Keyboard shortcuts beyond standard form navigation
- Task priority indicators (Phase V scope)
- Task tagging/categorization (Phase V scope)
- Bulk task operations (select multiple, delete all)
- Task search or filtering (Phase V scope)
- Task sorting controls (Phase V scope)

### Performance Limits

- **Initial Page Load (LCP)**: < 2.5 seconds
- **Time to Interactive (TTI)**: < 3.5 seconds
- **Cumulative Layout Shift (CLS)**: < 0.1
- **Bundle Size (gzipped)**: < 150KB for initial route

### Browser Support

- Chrome 90+
- Firefox 90+
- Safari 15+
- Edge 90+
- No Internet Explorer support

### Accessibility Requirements

- WCAG 2.1 Level AA compliance
- All interactive elements keyboard-navigable
- Screen reader compatible (ARIA labels)
- Color contrast ratio >= 4.5:1

### Technical Debt

- No i18n infrastructure in v1 (English only)
- No component library documentation (Storybook deferred to Phase V)
- No end-to-end testing framework (Playwright deferred to Phase III)

---

## 3. App Router Structure

### File System Routing

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout with providers
│   ├── page.tsx                # Landing page (redirect to /dashboard)
│   ├── globals.css             # Global styles (Tailwind imports)
│   ├── loading.tsx             # Root loading state
│   ├── error.tsx               # Root error boundary
│   ├── not-found.tsx           # 404 page
│   │
│   ├── login/
│   │   ├── page.tsx            # Login form page
│   │   └── loading.tsx         # Login loading state
│   │
│   ├── register/
│   │   ├── page.tsx            # Registration form page
│   │   └── loading.tsx         # Register loading state
│   │
│   └── dashboard/
│       ├── layout.tsx          # Protected layout (auth guard)
│       ├── page.tsx            # Task list page (main view)
│       ├── loading.tsx         # Dashboard skeleton loader
│       └── error.tsx           # Dashboard error boundary
│
├── components/
│   ├── ui/                     # Primitive UI components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── textarea.tsx
│   │   ├── modal.tsx
│   │   ├── dialog.tsx
│   │   ├── checkbox.tsx
│   │   ├── skeleton.tsx
│   │   └── toast.tsx
│   │
│   ├── layout/                 # Layout components
│   │   ├── navbar.tsx
│   │   ├── user-menu.tsx
│   │   └── footer.tsx
│   │
│   ├── auth/                   # Authentication components
│   │   ├── login-form.tsx
│   │   ├── register-form.tsx
│   │   └── auth-guard.tsx
│   │
│   └── tasks/                  # Task-specific components
│       ├── task-list.tsx
│       ├── task-card.tsx
│       ├── create-task-form.tsx
│       ├── edit-task-modal.tsx
│       ├── delete-confirm-dialog.tsx
│       └── empty-state.tsx
│
├── lib/
│   ├── auth.ts                 # Better Auth client configuration
│   ├── api.ts                  # API client (fetch wrapper)
│   └── utils.ts                # Utility functions
│
├── hooks/
│   ├── use-tasks.ts            # Task data fetching hook
│   ├── use-auth.ts             # Authentication state hook
│   └── use-optimistic.ts       # Optimistic update utilities
│
└── types/
    ├── task.ts                 # Task type definitions
    └── api.ts                  # API response types
```

---

## 4. Component Hierarchy

### Visual Component Tree

```
RootLayout
├── Providers (AuthProvider, QueryClientProvider)
│
├── [Unauthenticated Routes]
│   ├── /login → LoginPage
│   │   └── LoginForm
│   │       ├── Input (email)
│   │       ├── Input (password)
│   │       ├── Button (submit)
│   │       └── Link (to /register)
│   │
│   └── /register → RegisterPage
│       └── RegisterForm
│           ├── Input (name)
│           ├── Input (email)
│           ├── Input (password)
│           ├── Input (confirm password)
│           ├── Button (submit)
│           └── Link (to /login)
│
└── [Protected Routes] → AuthGuard
    └── /dashboard → DashboardLayout
        ├── Navbar
        │   ├── Logo
        │   ├── UserMenu
        │   │   ├── Avatar
        │   │   ├── UserName
        │   │   └── LogoutButton
        │   └── CreateTaskButton (+)
        │
        └── DashboardPage
            ├── CreateTaskForm (inline, collapsible)
            │   ├── Input (title)
            │   ├── Textarea (description)
            │   └── Button (submit)
            │
            ├── TaskList
            │   ├── TaskCard (repeated)
            │   │   ├── Checkbox (toggle complete)
            │   │   ├── TaskTitle
            │   │   ├── TaskDescription
            │   │   ├── TaskTimestamp
            │   │   ├── EditButton
            │   │   └── DeleteButton
            │   │
            │   └── EmptyState (when no tasks)
            │
            ├── EditTaskModal (conditional)
            │   ├── Input (title)
            │   ├── Textarea (description)
            │   ├── Button (save)
            │   └── Button (cancel)
            │
            └── DeleteConfirmDialog (conditional)
                ├── WarningMessage
                ├── Button (confirm delete)
                └── Button (cancel)
```

---

## 5. Page Specifications

---

### PAGE-001: Root Landing Page

**Route**: `/`
**File**: `app/page.tsx`
**Type**: Server Component

#### Purpose

Redirect authenticated users to dashboard, unauthenticated users to login.

#### Behavior

```typescript
// Pseudocode logic
if (user.isAuthenticated) {
  redirect('/dashboard');
} else {
  redirect('/login');
}
```

#### Acceptance Criteria

- [ ] AC-ROOT-01: Authenticated user redirected to `/dashboard`
- [ ] AC-ROOT-02: Unauthenticated user redirected to `/login`
- [ ] AC-ROOT-03: Redirect happens server-side (no flash of content)

---

### PAGE-002: Login Page

**Route**: `/login`
**File**: `app/login/page.tsx`
**Type**: Client Component (form interactivity)

#### Purpose

Allow existing users to authenticate with email and password.

#### UI Layout

```
┌─────────────────────────────────────────┐
│                                         │
│              [App Logo]                 │
│           "Welcome Back"                │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Email                           │    │
│  │ [________________________]      │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Password                        │    │
│  │ [________________________]      │    │
│  └─────────────────────────────────┘    │
│                                         │
│  [        Sign In Button          ]     │
│                                         │
│  "Don't have an account? Register"      │
│                                         │
└─────────────────────────────────────────┘
```

#### Form Fields

| Field | Type | Validation | Error Message |
|-------|------|------------|---------------|
| Email | `email` | Required, valid email format | "Please enter a valid email address" |
| Password | `password` | Required, min 8 characters | "Password must be at least 8 characters" |

#### States

| State | Description | Visual |
|-------|-------------|--------|
| `idle` | Default state | Form enabled, no errors |
| `submitting` | Form submitted | Button shows spinner, inputs disabled |
| `error` | Authentication failed | Error message displayed above form |
| `success` | Login successful | Redirect to `/dashboard` |

#### Error Handling

| API Error | User Message |
|-----------|--------------|
| Invalid credentials | "Invalid email or password. Please try again." |
| Account not found | "No account found with this email address." |
| Network error | "Unable to connect. Please check your internet connection." |

#### Acceptance Criteria

- [ ] AC-LOGIN-01: Valid credentials redirect to `/dashboard`
- [ ] AC-LOGIN-02: Invalid credentials show error message (no page reload)
- [ ] AC-LOGIN-03: Form validates on blur and on submit
- [ ] AC-LOGIN-04: Submit button disabled during request
- [ ] AC-LOGIN-05: "Register" link navigates to `/register`
- [ ] AC-LOGIN-06: Already authenticated users redirected to `/dashboard`
- [ ] AC-LOGIN-07: Password field masks input

---

### PAGE-003: Register Page

**Route**: `/register`
**File**: `app/register/page.tsx`
**Type**: Client Component (form interactivity)

#### Purpose

Allow new users to create an account.

#### UI Layout

```
┌─────────────────────────────────────────┐
│                                         │
│              [App Logo]                 │
│          "Create Account"               │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Full Name                       │    │
│  │ [________________________]      │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Email                           │    │
│  │ [________________________]      │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Password                        │    │
│  │ [________________________]      │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Confirm Password                │    │
│  │ [________________________]      │    │
│  └─────────────────────────────────┘    │
│                                         │
│  [       Create Account Button    ]     │
│                                         │
│  "Already have an account? Sign In"     │
│                                         │
└─────────────────────────────────────────┘
```

#### Form Fields

| Field | Type | Validation | Error Message |
|-------|------|------------|---------------|
| Name | `text` | Required, 2-100 chars | "Name must be between 2 and 100 characters" |
| Email | `email` | Required, valid email | "Please enter a valid email address" |
| Password | `password` | Required, min 8 chars, 1 uppercase, 1 number | "Password must be at least 8 characters with 1 uppercase and 1 number" |
| Confirm Password | `password` | Required, must match password | "Passwords do not match" |

#### States

| State | Description | Visual |
|-------|-------------|--------|
| `idle` | Default state | Form enabled, no errors |
| `submitting` | Form submitted | Button shows spinner, inputs disabled |
| `error` | Registration failed | Error message displayed |
| `success` | Account created | Redirect to `/dashboard` (auto-login) |

#### Error Handling

| API Error | User Message |
|-----------|--------------|
| Email already exists | "An account with this email already exists. Try signing in." |
| Weak password | "Password does not meet security requirements." |
| Network error | "Unable to connect. Please check your internet connection." |

#### Acceptance Criteria

- [ ] AC-REG-01: Valid registration creates account and redirects to `/dashboard`
- [ ] AC-REG-02: Duplicate email shows appropriate error
- [ ] AC-REG-03: Password mismatch shows inline error
- [ ] AC-REG-04: All fields validate on blur
- [ ] AC-REG-05: Submit button disabled during request
- [ ] AC-REG-06: "Sign In" link navigates to `/login`
- [ ] AC-REG-07: Already authenticated users redirected to `/dashboard`

---

### PAGE-004: Dashboard Page (Main Task View)

**Route**: `/dashboard`
**File**: `app/dashboard/page.tsx`
**Type**: Hybrid (Server Component with Client islands)

#### Purpose

Display all tasks for the authenticated user with full CRUD capabilities.

#### UI Layout

```
┌────────────────────────────────────────────────────────┐
│ [Logo]                              [User] [Logout]    │  <- Navbar
├────────────────────────────────────────────────────────┤
│                                                        │
│  My Tasks                                     [+ Add]  │  <- Header
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ [+] Add a new task...                            │  │  <- Create Form (collapsed)
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ [✓] Buy groceries                       [✎] [🗑] │  │  <- Task Card
│  │     Milk, eggs, bread                            │  │
│  │     Created: Dec 28, 2025                        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ [ ] Call the dentist                    [✎] [🗑] │  │  <- Task Card
│  │     Schedule annual checkup                      │  │
│  │     Created: Dec 27, 2025                        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ [✓] Review project proposal             [✎] [🗑] │  │  <- Task Card (completed)
│  │     Check budget section                         │  │
│  │     Created: Dec 26, 2025                        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

#### Empty State Layout

```
┌────────────────────────────────────────────────────────┐
│ [Logo]                              [User] [Logout]    │
├────────────────────────────────────────────────────────┤
│                                                        │
│                    [Illustration]                      │
│                                                        │
│               "No tasks yet!"                          │
│    "Add your first task to get started."              │
│                                                        │
│            [  + Add Your First Task  ]                 │
│                                                        │
└────────────────────────────────────────────────────────┘
```

#### Data Fetching Strategy

1. **Initial Load**: Server Component fetches tasks via `GET /api/v1/tasks`
2. **Mutations**: Client-side with optimistic updates
3. **Revalidation**: After each mutation, revalidate server cache

```typescript
// Server Component data fetching
async function DashboardPage() {
  const tasks = await fetchTasks(); // Server-side fetch with cookies
  return <TaskList initialTasks={tasks} />;
}
```

#### Acceptance Criteria

- [ ] AC-DASH-01: Page shows all user tasks on load
- [ ] AC-DASH-02: Tasks display title, description (if any), and created date
- [ ] AC-DASH-03: Completed tasks show visual distinction (strikethrough, muted)
- [ ] AC-DASH-04: Unauthenticated users redirected to `/login`
- [ ] AC-DASH-05: Empty state shown when no tasks exist
- [ ] AC-DASH-06: Loading skeleton shown during initial fetch
- [ ] AC-DASH-07: Error state shown if API fails

---

## 6. Component Specifications

---

### COMP-001: Navbar

**File**: `components/layout/navbar.tsx`
**Type**: Client Component (user menu interactivity)

#### Props

```typescript
interface NavbarProps {
  user: {
    id: string;
    name: string;
    email: string;
  };
}
```

#### Elements

| Element | Description | Behavior |
|---------|-------------|----------|
| Logo | App logo/name | Clicking navigates to `/dashboard` |
| UserMenu | Dropdown with user info | Toggle on click |
| LogoutButton | Signs out user | Calls `signOut()`, redirects to `/login` |

#### Acceptance Criteria

- [ ] AC-NAV-01: Logo click navigates to `/dashboard`
- [ ] AC-NAV-02: User name displayed in menu
- [ ] AC-NAV-03: Logout clears session and redirects to `/login`

---

### COMP-002: TaskList

**File**: `components/tasks/task-list.tsx`
**Type**: Client Component (interactivity required)

#### Props

```typescript
interface TaskListProps {
  initialTasks: Task[];
}

interface Task {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  created_at: string;
  updated_at: string;
}
```

#### Behavior

- Renders list of `TaskCard` components
- Manages local state for optimistic updates
- Shows `EmptyState` when `tasks.length === 0`

#### Acceptance Criteria

- [ ] AC-TASKLIST-01: Renders all provided tasks
- [ ] AC-TASKLIST-02: Shows empty state when no tasks
- [ ] AC-TASKLIST-03: Updates immediately on task mutations (optimistic)

---

### COMP-003: TaskCard

**File**: `components/tasks/task-card.tsx`
**Type**: Client Component

#### Props

```typescript
interface TaskCardProps {
  task: Task;
  onToggleComplete: (taskId: string) => void;
  onEdit: (task: Task) => void;
  onDelete: (taskId: string) => void;
}
```

#### Visual States

| State | Visual Treatment |
|-------|------------------|
| Pending | Normal text, unchecked checkbox |
| Completed | Strikethrough title, muted colors, checked checkbox |
| Hovering | Subtle background highlight, action buttons visible |
| Deleting | Fade-out animation (optimistic) |

#### Elements

| Element | Type | Action |
|---------|------|--------|
| Checkbox | `<Checkbox>` | Calls `onToggleComplete(task.id)` |
| Title | `<h3>` | Display only |
| Description | `<p>` | Display only (if present) |
| Created Date | `<span>` | Formatted as "Dec 28, 2025" |
| Edit Button | `<Button>` | Calls `onEdit(task)` |
| Delete Button | `<Button>` | Calls `onDelete(task.id)` |

#### Acceptance Criteria

- [ ] AC-TASKCARD-01: Displays title, description, and date
- [ ] AC-TASKCARD-02: Checkbox toggles completion state
- [ ] AC-TASKCARD-03: Edit button opens edit modal
- [ ] AC-TASKCARD-04: Delete button opens confirm dialog
- [ ] AC-TASKCARD-05: Completed tasks have visual distinction

---

### COMP-004: CreateTaskForm

**File**: `components/tasks/create-task-form.tsx`
**Type**: Client Component

#### Props

```typescript
interface CreateTaskFormProps {
  onTaskCreated: (task: Task) => void;
}
```

#### Form Fields

| Field | Name | Type | Required | Constraints |
|-------|------|------|----------|-------------|
| Title | `title` | `text` | Yes | 1-200 characters |
| Description | `description` | `textarea` | No | 0-1000 characters |

#### States

| State | Description | Visual |
|-------|-------------|--------|
| `collapsed` | Initial state | Single line with "+" button or placeholder |
| `expanded` | User clicked to add | Full form visible |
| `submitting` | Form submitted | Button disabled, spinner shown |
| `error` | Submission failed | Error message shown |

#### Behavior

1. Clicking "Add Task" or "+" expands the form
2. User enters title (required) and description (optional)
3. Submit creates task via `POST /api/v1/tasks`
4. On success: Form collapses, new task appears in list (optimistic)
5. On error: Error message shown, form remains open

#### Validation

| Field | Rule | Client-Side Message |
|-------|------|---------------------|
| Title | Required | "Title is required" |
| Title | Max 200 chars | "Title must be 200 characters or less" |
| Description | Max 1000 chars | "Description must be 1000 characters or less" |

#### Acceptance Criteria

- [ ] AC-CREATE-01: Form expands on click
- [ ] AC-CREATE-02: Title field is required
- [ ] AC-CREATE-03: Submit with valid data creates task
- [ ] AC-CREATE-04: New task appears immediately (optimistic update)
- [ ] AC-CREATE-05: Form resets after successful creation
- [ ] AC-CREATE-06: Error message shown on API failure
- [ ] AC-CREATE-07: Submit button disabled during request

---

### COMP-005: EditTaskModal

**File**: `components/tasks/edit-task-modal.tsx`
**Type**: Client Component

#### Props

```typescript
interface EditTaskModalProps {
  task: Task;
  isOpen: boolean;
  onClose: () => void;
  onSave: (taskId: string, updates: TaskInput) => void;
}

interface TaskInput {
  title?: string;
  description?: string;
}
```

#### UI Layout

```
┌─────────────────────────────────────────┐
│ Edit Task                           [X] │  <- Modal Header
├─────────────────────────────────────────┤
│                                         │
│  Title                                  │
│  ┌─────────────────────────────────┐    │
│  │ [Current title value          ] │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Description                            │
│  ┌─────────────────────────────────┐    │
│  │ [Current description value    ] │    │
│  │ [                             ] │    │
│  │ [                             ] │    │
│  └─────────────────────────────────┘    │
│                                         │
│           [ Cancel ]  [ Save Changes ]  │  <- Actions
│                                         │
└─────────────────────────────────────────┘
```

#### Behavior

1. Modal opens with current task data pre-filled
2. User modifies title and/or description
3. "Save Changes" triggers `PUT /api/v1/tasks/{task_id}`
4. On success: Modal closes, task updated in list
5. On error: Error message shown, modal remains open

#### Acceptance Criteria

- [ ] AC-EDIT-01: Modal opens with task data pre-filled
- [ ] AC-EDIT-02: Cancel closes modal without saving
- [ ] AC-EDIT-03: Save updates task and closes modal
- [ ] AC-EDIT-04: Task list updates immediately (optimistic)
- [ ] AC-EDIT-05: Error message shown on API failure
- [ ] AC-EDIT-06: Escape key closes modal
- [ ] AC-EDIT-07: Clicking overlay closes modal

---

### COMP-006: DeleteConfirmDialog

**File**: `components/tasks/delete-confirm-dialog.tsx`
**Type**: Client Component

#### Props

```typescript
interface DeleteConfirmDialogProps {
  taskTitle: string;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
}
```

#### UI Layout

```
┌─────────────────────────────────────────┐
│ Delete Task                         [X] │
├─────────────────────────────────────────┤
│                                         │
│  Are you sure you want to delete        │
│  "Buy groceries"?                       │
│                                         │
│  This action cannot be undone.          │
│                                         │
│           [ Cancel ]  [ Delete ]        │
│                        (red button)     │
└─────────────────────────────────────────┘
```

#### Behavior

1. Dialog opens when user clicks delete on a task
2. Shows task title for confirmation
3. "Cancel" closes dialog
4. "Delete" triggers `DELETE /api/v1/tasks/{task_id}`
5. On success: Dialog closes, task removed from list
6. On error: Error message shown

#### Acceptance Criteria

- [ ] AC-DELETE-01: Dialog shows task title
- [ ] AC-DELETE-02: Cancel closes dialog without action
- [ ] AC-DELETE-03: Confirm deletes task and closes dialog
- [ ] AC-DELETE-04: Task removed from list immediately (optimistic)
- [ ] AC-DELETE-05: Error shown if delete fails (task restored)
- [ ] AC-DELETE-06: Escape key closes dialog

---

### COMP-007: EmptyState

**File**: `components/tasks/empty-state.tsx`
**Type**: Client Component

#### Props

```typescript
interface EmptyStateProps {
  onAddTask: () => void;
}
```

#### Visual

- Illustration or icon (clipboard, checklist)
- Heading: "No tasks yet!"
- Subtext: "Add your first task to get started."
- CTA Button: "Add Your First Task"

#### Acceptance Criteria

- [ ] AC-EMPTY-01: Shown when task list is empty
- [ ] AC-EMPTY-02: CTA button expands create form

---

## 7. User Interactions

---

### INT-001: Add Task

**Trigger**: User clicks "+" button or "Add Task" area

**Flow**:

```
1. User clicks "+" button
   ↓
2. CreateTaskForm expands (transition: slide down, 200ms)
   ↓
3. User enters title (required)
4. User enters description (optional)
   ↓
5. User clicks "Add Task" button
   ↓
6. [Optimistic Update] Task appears in list immediately
7. [API Call] POST /api/v1/tasks
   ↓
8a. [Success] Form collapses, task confirmed in list
8b. [Failure] Error toast shown, task removed from list, form remains open
```

**Optimistic Update Schema**:

```typescript
const optimisticTask: Task = {
  id: crypto.randomUUID(), // Temporary ID
  title: formData.title,
  description: formData.description || '',
  completed: false,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};
```

---

### INT-002: Edit Task

**Trigger**: User clicks edit icon on TaskCard

**Flow**:

```
1. User clicks edit icon
   ↓
2. EditTaskModal opens (transition: fade in, scale up, 150ms)
3. Form pre-filled with current task data
   ↓
4. User modifies title and/or description
   ↓
5. User clicks "Save Changes"
   ↓
6. [Optimistic Update] Task updated in list immediately
7. [API Call] PUT /api/v1/tasks/{task_id}
   ↓
8a. [Success] Modal closes
8b. [Failure] Error shown, task reverted to previous state
```

---

### INT-003: Delete Task

**Trigger**: User clicks delete icon on TaskCard

**Flow**:

```
1. User clicks delete icon
   ↓
2. DeleteConfirmDialog opens
   ↓
3a. User clicks "Cancel" → Dialog closes, no action
3b. User clicks "Delete"
   ↓
4. [Optimistic Update] Task fades out and removed from list
5. [API Call] DELETE /api/v1/tasks/{task_id}
   ↓
6a. [Success] Toast: "Task deleted"
6b. [Failure] Toast: "Failed to delete task", task restored to list
```

---

### INT-004: Toggle Complete

**Trigger**: User clicks checkbox on TaskCard

**Flow**:

```
1. User clicks checkbox
   ↓
2. [Optimistic Update] Checkbox state toggles immediately
3. Task visual state updates (strikethrough if completed)
4. [API Call] PATCH /api/v1/tasks/{task_id}/complete
   ↓
5a. [Success] State confirmed
5b. [Failure] Checkbox reverts, toast: "Failed to update task"
```

**Animation**: Checkbox transition 150ms, strikethrough slides in 200ms

---

## 8. State Management

### Server vs Client State

| Data | Location | Rationale |
|------|----------|-----------|
| Task list (initial) | Server Component | SEO, fast initial render |
| Task list (mutations) | Client state | Optimistic updates |
| Form state | Client state | User input tracking |
| Modal open/close | Client state | UI interaction |
| Auth state | Client context | Persistent across routes |

### State Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Server Component                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  await fetchTasks() // Server-side fetch             │  │
│  │  return <TaskList initialTasks={tasks} />            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Client Component                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  const [tasks, setTasks] = useState(initialTasks);   │  │
│  │  // Mutations update local state optimistically      │  │
│  │  // Then sync with server                            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Optimistic Update Pattern

```typescript
// Pattern for all mutations
async function handleMutation(action: () => Promise<void>, rollback: () => void) {
  const previousState = tasks;

  try {
    applyOptimisticUpdate(); // Immediate UI update
    await action();          // API call
  } catch (error) {
    rollback();              // Revert on failure
    showErrorToast(error);
  }
}
```

---

## 9. API Integration

### API Client Configuration

```typescript
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
  meta?: {
    total: number;
    limit: number;
    offset: number;
  };
}

async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${getAuthToken()}`,
      ...options?.headers,
    },
  });

  return response.json();
}
```

### Endpoint Mapping

| Action | Client Function | API Endpoint |
|--------|-----------------|--------------|
| List tasks | `getTasks()` | `GET /api/v1/tasks` |
| Create task | `createTask(input)` | `POST /api/v1/tasks` |
| Get task | `getTask(id)` | `GET /api/v1/tasks/{id}` |
| Update task | `updateTask(id, input)` | `PUT /api/v1/tasks/{id}` |
| Delete task | `deleteTask(id)` | `DELETE /api/v1/tasks/{id}` |
| Toggle complete | `toggleComplete(id)` | `PATCH /api/v1/tasks/{id}/complete` |

---

## 10. Error Handling

### Error Display Hierarchy

1. **Field-level errors**: Inline below input (validation)
2. **Form-level errors**: Above submit button
3. **Global errors**: Toast notification (bottom-right)

### Error Type Mapping

| API Error Code | User-Facing Message | Display Location |
|----------------|---------------------|------------------|
| `VALIDATION_ERROR` | Field-specific message | Inline |
| `AUTH_INVALID` | "Session expired. Please log in again." | Toast + Redirect |
| `TASK_NOT_FOUND` | "Task not found. It may have been deleted." | Toast |
| `INTERNAL_ERROR` | "Something went wrong. Please try again." | Toast |
| Network error | "Unable to connect. Check your internet." | Toast |

### Toast Configuration

```typescript
interface Toast {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration: number; // milliseconds (default: 5000)
  dismissible: boolean;
}
```

---

## 11. Loading States

### Skeleton Patterns

#### Dashboard Skeleton

```
┌────────────────────────────────────────────────────────┐
│ [████████]                          [████] [██████]    │
├────────────────────────────────────────────────────────┤
│  ██████████                                   [█████]  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ ████████████████████████████████████████████████ │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ ████████████████████████████████████████████████ │  │
│  │ ████████████████████████                        │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ ████████████████████████████████████████████████ │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### State Indicators

| Component | Loading State | Duration |
|-----------|---------------|----------|
| Dashboard | Skeleton cards | Until tasks fetched |
| CreateTaskForm | Button spinner | During submission |
| EditTaskModal | Button spinner | During save |
| DeleteConfirmDialog | Button spinner | During deletion |
| TaskCard checkbox | Pulsing animation | During toggle |

---

## 12. Accessibility Requirements

### ARIA Labels

| Component | ARIA Attribute | Value |
|-----------|----------------|-------|
| Task checkbox | `aria-label` | "Mark {task title} as complete" |
| Edit button | `aria-label` | "Edit {task title}" |
| Delete button | `aria-label` | "Delete {task title}" |
| Modal | `role` | "dialog" |
| Modal | `aria-modal` | "true" |
| Modal | `aria-labelledby` | ID of modal title |

### Keyboard Navigation

| Key | Context | Action |
|-----|---------|--------|
| `Tab` | Form | Move to next field |
| `Shift+Tab` | Form | Move to previous field |
| `Enter` | Form | Submit form |
| `Escape` | Modal/Dialog | Close modal |
| `Space` | Checkbox | Toggle state |

### Focus Management

1. When modal opens, focus moves to first focusable element
2. Focus trapped within modal while open
3. When modal closes, focus returns to trigger element
4. Skip link available for keyboard users

---

## 13. Responsive Design

### Breakpoints

| Name | Width | Description |
|------|-------|-------------|
| `sm` | 640px | Mobile phones |
| `md` | 768px | Tablets |
| `lg` | 1024px | Laptops |
| `xl` | 1280px | Desktops |

### Layout Adaptations

| Viewport | Layout Change |
|----------|---------------|
| < 640px | Single column, full-width cards, hamburger menu |
| 640-768px | Single column, cards with padding |
| 768-1024px | Single column, wider content area |
| > 1024px | Centered content (max-width: 800px) |

### Touch Targets

- All interactive elements minimum 44x44 pixels on mobile
- Adequate spacing between buttons (min 8px)

---

## 14. Type Definitions

```typescript
// types/task.ts

export interface Task {
  id: string;
  user_id: string;
  title: string;
  description: string;
  completed: boolean;
  created_at: string;
  updated_at: string;
}

export interface TaskInput {
  title: string;
  description?: string;
}

export interface TaskUpdateInput {
  title?: string;
  description?: string;
}

// types/api.ts

export interface ApiSuccessResponse<T> {
  success: true;
  data: T;
  meta?: {
    total: number;
    limit: number;
    offset: number;
  };
}

export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, string>;
  };
}

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse;

// types/auth.ts

export interface User {
  id: string;
  name: string;
  email: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
```

---

## 15. Acceptance Criteria Summary

### Authentication Pages

- [ ] AC-AUTH-01: Login form validates email and password
- [ ] AC-AUTH-02: Register form validates all fields including password match
- [ ] AC-AUTH-03: Successful login redirects to dashboard
- [ ] AC-AUTH-04: Failed login shows error without page reload
- [ ] AC-AUTH-05: Successful registration auto-logs in user
- [ ] AC-AUTH-06: Auth pages redirect authenticated users to dashboard

### Dashboard

- [ ] AC-DASH-01: Protected route redirects unauthenticated users to login
- [ ] AC-DASH-02: All user tasks displayed on load
- [ ] AC-DASH-03: Empty state shown when no tasks
- [ ] AC-DASH-04: Loading skeleton shown during fetch
- [ ] AC-DASH-05: Error state shown on API failure

### Task Operations

- [ ] AC-TASK-01: Create task with title only (description optional)
- [ ] AC-TASK-02: Edit task updates title and/or description
- [ ] AC-TASK-03: Delete task removes from list with confirmation
- [ ] AC-TASK-04: Toggle complete changes task status
- [ ] AC-TASK-05: All operations use optimistic updates
- [ ] AC-TASK-06: Failed operations revert state and show error

### UX Quality

- [ ] AC-UX-01: All forms disable during submission
- [ ] AC-UX-02: Loading states shown for async operations
- [ ] AC-UX-03: Keyboard navigation works for all interactive elements
- [ ] AC-UX-04: Modals trap focus and close on Escape
- [ ] AC-UX-05: Error messages are user-friendly (no technical jargon)

---

## 16. Non-Functional Requirements

### Performance

- **Time to First Byte (TTFB)**: < 200ms
- **Largest Contentful Paint (LCP)**: < 2.5s
- **First Input Delay (FID)**: < 100ms
- **Cumulative Layout Shift (CLS)**: < 0.1
- **API Response Latency (p99)**: < 500ms

### Security

- **XSS Prevention**: All user input escaped in JSX
- **CSRF Protection**: Better Auth handles via cookies
- **Token Storage**: HTTP-only cookies (not localStorage)
- **Content Security Policy**: Strict CSP headers

### Observability

- **Error Tracking**: Client-side errors logged (console in v1, Sentry in v2)
- **Performance Monitoring**: Web Vitals logged to console
- **User Actions**: Key interactions logged for debugging

---

## 17. Styling Guidelines

### Tailwind CSS Classes (Reference)

```css
/* Task card base */
.task-card: "bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow"

/* Task completed */
.task-completed: "opacity-60"
.task-title-completed: "line-through text-gray-500"

/* Buttons */
.btn-primary: "bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
.btn-secondary: "bg-gray-200 text-gray-800 px-4 py-2 rounded-md hover:bg-gray-300"
.btn-danger: "bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"

/* Form inputs */
.input: "w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
.input-error: "border-red-500 focus:ring-red-500"

/* Modal overlay */
.modal-overlay: "fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center"
.modal-content: "bg-white rounded-lg shadow-xl max-w-md w-full mx-4"
```

---

## Approval

**Specification Status**: Draft - Ready for Review

- [x] App Router structure defined
- [x] All pages specified with layouts
- [x] Component hierarchy documented
- [x] User interactions detailed with flows
- [x] State management strategy defined
- [x] API integration patterns specified
- [x] Error handling documented
- [x] Loading states defined
- [x] Accessibility requirements listed
- [x] Acceptance criteria testable
- [x] Type definitions provided

**Dependencies**:

- REST API Spec (`rest-endpoints.md`) - Approved
- Authentication Spec (Better Auth) - Pending
- Database Schema Spec - Pending

**Next Step**: Upon approval, proceed to authentication specification (`auth/better-auth.md`).
