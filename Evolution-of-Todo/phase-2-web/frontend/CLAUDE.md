# Frontend Implementation Guide

## Overview

Next.js 15+ frontend for the Evolution of Todo application (Phase 2).

## Tech Stack

- **Framework**: Next.js 15+ (App Router)
- **Language**: TypeScript 5+
- **Styling**: Tailwind CSS
- **Package Manager**: pnpm

## Directory Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Landing (redirect to dashboard)
│   ├── globals.css
│   ├── actions/
│   │   ├── auth.ts             # Server Actions: login, logout, register
│   │   └── tasks.ts            # Server Actions: CRUD
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   └── (dashboard)/
│       ├── layout.tsx          # Auth guard layout
│       └── page.tsx            # Task list dashboard
├── components/
│   ├── ui/
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Card.tsx
│   │   └── Modal.tsx
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   └── RegisterForm.tsx
│   └── tasks/
│       ├── TaskList.tsx
│       ├── TaskItem.tsx
│       ├── TaskForm.tsx
│       └── DeleteConfirmDialog.tsx
├── lib/
│   ├── api.ts                  # Fetch wrapper
│   └── utils.ts
├── types/
│   └── index.ts                # TypeScript interfaces
├── middleware.ts               # Cookie -> Header extraction
├── next.config.js              # API proxy rewrites
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

## Commands

```bash
# Install dependencies
pnpm install

# Run development server
pnpm dev

# Build for production
pnpm build

# Type check
pnpm tsc --noEmit

# Lint
pnpm lint
```

## Architecture Decisions

| Decision | Reference |
|----------|-----------|
| JWT in httpOnly cookie | ADR-004 |
| Server Actions for mutations | ADR-005 |
| API proxy via next.config.js | ADR-005 |

## Authentication Flow

1. User submits login form
2. Server Action calls backend `/api/v1/auth/login`
3. Server Action sets `auth-token` httpOnly cookie
4. Middleware reads cookie and injects `Authorization` header
5. Protected layouts check cookie existence

## Data Fetching Patterns

### Server Actions (mutations)
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
      description: formData.get('description'),
    }),
  })

  revalidatePath('/dashboard')
  return response.json()
}
```

### Route Handlers (API proxy)
```javascript
// next.config.js
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.BACKEND_URL}/api/:path*`,
      },
    ]
  },
}
```

## Response Format

All API responses follow this format:

```typescript
interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
  }
}
```
