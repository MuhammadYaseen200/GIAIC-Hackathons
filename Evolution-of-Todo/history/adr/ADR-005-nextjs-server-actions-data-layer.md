# ADR-005: Next.js Server Actions as Data Layer

**Status**: Accepted
**Date**: 2025-12-29
**Deciders**: Lead Architect, UX Frontend Developer
**Applies To**: Phase II (Full-Stack Web Application)
**Supersedes**: N/A
**Related**: CL-002 (Clarification)

---

## Context

Phase II frontend uses Next.js 15+ with App Router. A key architectural decision is how to handle data mutations (create, update, delete operations):

**Problem Statement**: Next.js 15 offers multiple patterns for server-side data handling:
1. **API Routes** (`app/api/*/route.ts`): Traditional REST-like endpoints
2. **Server Actions** (`'use server'` functions): Integrated server-side functions callable from components
3. **Client-side fetch**: Direct browser requests to backend

**Constraints**:
1. Backend API already exists at FastAPI (`/api/v1/*`)
2. Frontend must be secure (no exposed credentials)
3. Bundle size should be minimized
4. Form handling should be simple and progressive enhancement-friendly
5. Data must refresh after mutations

---

## Decision

**Use Server Actions for all mutations (POST/PUT/DELETE/PATCH) to reduce client-side JavaScript bundle and simplify form handling. Use `revalidatePath` for cache invalidation. Reserve API Routes only for proxying scenarios where strictly necessary.**

### Architecture Pattern

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client        │    │   Server Action │    │   FastAPI       │
│   Component     │    │   (Node.js)     │    │   Backend       │
│                 │    │                 │    │                 │
│ <form action=   │───▶│ 'use server'    │───▶│ POST /api/v1/   │
│   {createTask}> │    │ async function  │    │ tasks           │
│                 │    │ + revalidatePath│    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### File Structure

```
frontend/app/
├── actions/
│   ├── auth.ts      # 'use server' - login, logout, register
│   └── tasks.ts     # 'use server' - createTask, updateTask, deleteTask, toggleComplete
└── (dashboard)/
    └── page.tsx     # Imports and uses actions
```

---

## Consequences

### Positive

| Benefit | Description |
|---------|-------------|
| Reduced Bundle Size | Server Actions don't ship to client; forms work without JS |
| Progressive Enhancement | Forms work with JavaScript disabled |
| Simplified State | No client-side state management for mutations |
| Secure by Default | Secrets (cookies, tokens) accessed server-side only |
| Integrated Cache | `revalidatePath` / `revalidateTag` for automatic UI refresh |
| Type Safety | Full TypeScript support with compile-time validation |

### Negative

| Drawback | Mitigation |
|----------|------------|
| Learning Curve | Team familiar with React hooks may need adjustment |
| Debugging | Server-side logs required; no browser DevTools visibility |
| Loading States | Must use `useFormStatus` hook for pending states |
| Optimistic Updates | Require `useOptimistic` hook (more complex than client state) |

### Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Action timeout | Low | Medium | Keep actions fast; async DB calls |
| State sync issues | Medium | Medium | Consistent `revalidatePath` usage |
| Error handling gaps | Medium | Low | Structured error returns |

---

## Alternatives Considered

### Alternative 1: API Routes as BFF (Backend for Frontend)

**Approach**: Create `app/api/tasks/route.ts` endpoints that proxy to FastAPI.

**Pros**:
- Familiar REST pattern
- Easy testing with curl/Postman
- Clear separation

**Cons**:
- Duplicate endpoint layer
- More files to maintain
- Larger bundle (needs client fetch code)

**Rejected Because**: Adds unnecessary indirection when Server Actions provide direct integration.

### Alternative 2: Client-Side Fetch with React Query

**Approach**: Use `@tanstack/react-query` for client-side data fetching and mutations.

**Pros**:
- Rich caching and revalidation features
- Optimistic updates built-in
- Familiar to React developers

**Cons**:
- Adds ~40KB to bundle
- Requires client-side token handling (security risk)
- More complex setup

**Rejected Because**: Increases bundle size; conflicts with httpOnly cookie strategy (ADR-004).

### Alternative 3: Hybrid (Actions for Mutations, Fetch for Reads)

**Approach**: Server Actions for writes, client fetch for reads.

**Pros**:
- Some bundle reduction
- Familiar read patterns

**Cons**:
- Inconsistent patterns
- Still requires client token handling for reads

**Rejected Because**: Inconsistency creates confusion; Server Components already handle reads.

---

## Implementation Patterns

### Server Action Definition

```typescript
// app/actions/tasks.ts
'use server'

import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'

export async function createTask(formData: FormData) {
  const cookieStore = await cookies()
  const token = cookieStore.get('auth-token')?.value

  const response = await fetch(`${process.env.BACKEND_URL}/api/v1/tasks`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title: formData.get('title'),
      description: formData.get('description') || '',
    }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error.message)
  }

  revalidatePath('/dashboard')
  return await response.json()
}
```

### Form Integration

```tsx
// app/(dashboard)/page.tsx
import { createTask } from '@/app/actions/tasks'

export default function Dashboard() {
  return (
    <form action={createTask}>
      <input name="title" required />
      <textarea name="description" />
      <button type="submit">Add Task</button>
    </form>
  )
}
```

### Loading State

```tsx
'use client'
import { useFormStatus } from 'react-dom'

function SubmitButton() {
  const { pending } = useFormStatus()
  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Saving...' : 'Add Task'}
    </button>
  )
}
```

---

## References

- [Next.js Server Actions Documentation](https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions-and-mutations)
- [React Form Actions RFC](https://github.com/reactjs/rfcs/pull/227)
- Phase 2 Specification: `phase-2-web/specs/spec.md` (Section: Clarifications CL-002)
- Phase 2 Research: `phase-2-web/specs/research.md`

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2025-12-29 | Lead Architect | Initial ADR created |
