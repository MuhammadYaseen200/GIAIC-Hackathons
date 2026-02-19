# UI Actionable Fixes - Quick Reference

**Date**: 2026-02-07
**Priority**: P0-P2 Issues with Code Examples

---

## P0: Critical Blockers

### 1. Mobile Navigation Overflow

**Current Code** (`app/dashboard/layout.tsx` line 33-53):
```tsx
<div className="flex items-center gap-6">
  <h1 className="text-xl font-bold text-gray-900">Todo App</h1>
  <Link href="/dashboard">Tasks</Link>
  <Link href="/dashboard/chat">Chat</Link>
</div>
```

**Problem**: On mobile (375px width), "Todo App" + "Tasks" + "Chat" + spacing = ~300px. Add Sign Out button = overflow.

**Solution**: Add responsive hamburger menu

```tsx
// Add this component to components/ui/MobileNav.tsx
'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Menu, X } from 'lucide-react'

export function MobileNav({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      {/* Mobile menu button */}
      <button
        className="md:hidden"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle menu"
        aria-expanded={isOpen}
      >
        {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {/* Desktop nav - hidden on mobile */}
      <div className="hidden md:flex items-center gap-6">
        {children}
      </div>

      {/* Mobile dropdown */}
      {isOpen && (
        <div className="absolute top-16 left-0 right-0 bg-white shadow-lg md:hidden">
          <nav className="flex flex-col p-4 space-y-2">
            {children}
          </nav>
        </div>
      )}
    </>
  )
}
```

**Update**: Modify `app/dashboard/layout.tsx`:
```tsx
import { MobileNav } from '@/components/ui/MobileNav'

// Replace line 33-53 with:
<MobileNav>
  <h1 className="text-xl font-bold text-gray-900">Todo App</h1>
  <Link href="/dashboard">Tasks</Link>
  <Link href="/dashboard/chat">Chat</Link>
</MobileNav>
```

---

### 2. Active Link Indicator Missing

**Current Code** (`app/dashboard/layout.tsx` line 41-52):
```tsx
<Link
  href="/dashboard"
  className="text-sm font-medium text-gray-700 hover:text-gray-900"
>
  Tasks
</Link>
```

**Problem**: User can't tell which page they're on.

**Solution**: Add active state detection

```tsx
'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  const pathname = usePathname()
  const isActive = pathname === href

  return (
    <Link
      href={href}
      aria-current={isActive ? 'page' : undefined}
      className={`text-sm font-medium transition-colors ${
        isActive
          ? 'text-blue-600 font-bold border-b-2 border-blue-600'
          : 'text-gray-700 hover:text-gray-900'
      }`}
    >
      {children}
    </Link>
  )
}
```

**Update**: Replace `<Link>` tags with `<NavLink>` in dashboard layout.

---

## P1: High Priority

### 3. State Persistence Missing

**Problem**: Filter/search state lost on page refresh.

**Solution**: Add localStorage persistence to TaskToolbar

```tsx
// components/tasks/TaskToolbar.tsx
'use client'

import { useState, useEffect } from 'react'

export default function TaskToolbar({ tasks, onFilteredTasksChange }) {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  // Restore from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('task-filters')
    if (saved) {
      const { search, status } = JSON.parse(saved)
      setSearchTerm(search || '')
      setStatusFilter(status || 'all')
    }
  }, [])

  // Persist to localStorage on change
  useEffect(() => {
    localStorage.setItem('task-filters', JSON.stringify({
      search: searchTerm,
      status: statusFilter
    }))
  }, [searchTerm, statusFilter])

  // ... rest of component
}
```

**Additional Persistence Needs**:
- Language preference: `localStorage.getItem('user-language')`
- Theme preference: `localStorage.getItem('user-theme')`
- Last visited page: `sessionStorage.getItem('last-page')`

---

### 4. Password Visibility Toggle Missing

**Problem**: Users can't verify password during login.

**Solution**: Add toggle button to Input component

```tsx
// components/ui/Input.tsx
'use client'

import { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'

export default function Input({ type, ...props }: InputProps) {
  const [showPassword, setShowPassword] = useState(false)

  // Only show toggle for password fields
  if (type === 'password') {
    return (
      <div className="relative">
        <input
          type={showPassword ? 'text' : 'password'}
          {...props}
        />
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="absolute right-3 top-1/2 -translate-y-1/2"
          aria-label={showPassword ? 'Hide password' : 'Show password'}
        >
          {showPassword ? (
            <EyeOff className="w-5 h-5 text-gray-400" />
          ) : (
            <Eye className="w-5 h-5 text-gray-400" />
          )}
        </button>
      </div>
    )
  }

  // Regular input
  return <input type={type} {...props} />
}
```

---

### 5. RTL Support for Urdu (Foundation)

**Step 1**: Install next-intl

```bash
cd phase-3-chatbot/frontend
pnpm add next-intl
```

**Step 2**: Update `app/layout.tsx`

```tsx
import { NextIntlClientProvider } from 'next-intl'
import { getLocale, getMessages } from 'next-intl/server'

export default async function RootLayout({ children }) {
  const locale = await getLocale()
  const messages = await getMessages()

  return (
    <html lang={locale} dir={locale === 'ur' ? 'rtl' : 'ltr'}>
      <body>
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  )
}
```

**Step 3**: Create translation files

```
messages/
  en.json
  ur.json
```

**Step 4**: Use logical properties in Tailwind

```tsx
// Instead of:
className="ml-4 mr-2"

// Use:
className="ms-4 me-2"  // ms = margin-start (left in LTR, right in RTL)
```

**Step 5**: Update flex layouts

```tsx
// Instead of:
className="flex justify-start"

// Use:
className="flex justify-start rtl:justify-end"
```

---

## P2: Medium Priority

### 6. Delete Dialog Backdrop Click

**Current Code** (`components/tasks/TaskItem.tsx` line 284):
```tsx
<div
  className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
  role="dialog"
>
```

**Problem**: Clicking backdrop doesn't close dialog (only Cancel button works).

**Solution**: Add click handler

```tsx
<div
  className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
  role="dialog"
  onClick={() => setShowDeleteDialog(false)}
>
  <div
    className="bg-white rounded-lg shadow-xl max-w-md w-full p-6"
    onClick={(e) => e.stopPropagation()}  // Prevent close when clicking dialog
  >
    {/* Dialog content */}
  </div>
</div>
```

---

### 7. Keyboard Shortcuts

**Install Library**:
```bash
pnpm add react-hotkeys-hook
```

**Add Global Shortcuts** (`app/dashboard/layout.tsx`):
```tsx
'use client'

import { useHotkeys } from 'react-hotkeys-hook'
import { useRouter } from 'next/navigation'

export default function DashboardLayout({ children }) {
  const router = useRouter()

  // Cmd/Ctrl + K: Go to tasks
  useHotkeys('mod+k', () => router.push('/dashboard'))

  // Cmd/Ctrl + J: Go to chat
  useHotkeys('mod+j', () => router.push('/dashboard/chat'))

  // Cmd/Ctrl + N: New task (focus form)
  useHotkeys('mod+n', () => {
    document.getElementById('new-task-title')?.focus()
  })

  return (
    <div>
      {/* Show shortcuts hint */}
      <div className="text-xs text-gray-400 p-2 border-t">
        Shortcuts: Ctrl+K (Tasks) | Ctrl+J (Chat) | Ctrl+N (New Task)
      </div>
      {children}
    </div>
  )
}
```

---

### 8. User Email Display in Navigation

**Problem**: User doesn't see who they're logged in as.

**Solution**: Add user info to navigation

```tsx
// app/dashboard/layout.tsx
import { cookies } from 'next/headers'
import { jwtDecode } from 'jwt-decode'

export default async function DashboardLayout({ children }) {
  const cookieStore = await cookies()
  const token = cookieStore.get('auth-token')?.value

  // Decode JWT to get user email (if token contains it)
  const user = token ? jwtDecode(token) : null

  return (
    <nav>
      {/* ... existing nav items ... */}

      {/* User info */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600 hidden sm:inline">
          {user?.email || 'User'}
        </span>
        <form action={logout}>
          <button>Sign Out</button>
        </form>
      </div>
    </nav>
  )
}
```

**Alternative**: Fetch user info from API

```tsx
// app/actions/auth.ts
export async function getCurrentUser() {
  const cookieStore = await cookies()
  const token = cookieStore.get('auth-token')?.value

  if (!token) return null

  const response = await fetch(`${process.env.BACKEND_URL}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${token}` }
  })

  return response.json()
}
```

---

## Quick Wins (< 30 min each)

### 9. Add Loading Skeleton to Task List

```tsx
// components/tasks/TaskList.tsx
import { Skeleton } from '@/components/ui/Skeleton'

export function TaskList({ tasks, filteredTasks, isLoading }) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    )
  }

  // ... existing code
}
```

---

### 10. Improve Focus Trap in Modals

**Install Library**:
```bash
pnpm add focus-trap-react
```

**Update Delete Dialog** (`components/tasks/TaskItem.tsx`):
```tsx
import FocusTrap from 'focus-trap-react'

{showDeleteDialog && (
  <FocusTrap>
    <div className="fixed inset-0 z-50 ...">
      {/* Dialog content */}
    </div>
  </FocusTrap>
)}
```

---

### 11. Add Skip Links for Accessibility

```tsx
// app/dashboard/layout.tsx
<nav>
  <a
    href="#main-content"
    className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded"
  >
    Skip to main content
  </a>
  {/* ... rest of nav ... */}
</nav>

<main id="main-content">
  {children}
</main>
```

---

### 12. Debounce Search Input

```tsx
// components/tasks/TaskToolbar.tsx
import { useState, useEffect } from 'react'
import { useDebouncedCallback } from 'use-debounce'

function TaskToolbar({ tasks, onFilteredTasksChange }) {
  const [searchInput, setSearchInput] = useState('')

  // Debounce filter update by 300ms
  const debouncedFilter = useDebouncedCallback((value) => {
    const filtered = tasks.filter(task =>
      task.title.toLowerCase().includes(value.toLowerCase())
    )
    onFilteredTasksChange(filtered)
  }, 300)

  useEffect(() => {
    debouncedFilter(searchInput)
  }, [searchInput])

  return (
    <input
      value={searchInput}
      onChange={(e) => setSearchInput(e.target.value)}
      placeholder="Search tasks..."
    />
  )
}
```

---

## Testing Checklist

After implementing fixes, verify:

- [ ] Mobile navigation works on 375px viewport
- [ ] Active link indicator shows current page
- [ ] Filter state persists after page refresh
- [ ] Password visibility toggle works
- [ ] RTL layout works for Urdu text
- [ ] Delete dialog closes on backdrop click
- [ ] Keyboard shortcuts work (Ctrl+K, Ctrl+J, Ctrl+N)
- [ ] User email displays in navigation
- [ ] Loading skeletons show during data fetch
- [ ] Focus trap works in delete dialog
- [ ] Skip links appear on Tab press
- [ ] Search input doesn't lag during typing

---

## Files to Create

1. `components/ui/MobileNav.tsx` - Mobile navigation component
2. `components/ui/NavLink.tsx` - Active link indicator component
3. `messages/en.json` - English translations
4. `messages/ur.json` - Urdu translations
5. `middleware.ts` - Update for i18n routing
6. `next.config.ts` - Update for next-intl

---

## Files to Modify

1. `app/dashboard/layout.tsx` - Add mobile nav, user email, shortcuts
2. `app/layout.tsx` - Add i18n provider, RTL support
3. `components/ui/Input.tsx` - Add password visibility toggle
4. `components/tasks/TaskToolbar.tsx` - Add state persistence, debounce
5. `components/tasks/TaskItem.tsx` - Add backdrop click, focus trap
6. `components/tasks/TaskList.tsx` - Add loading skeleton
7. `package.json` - Add dependencies:
   - next-intl
   - react-hotkeys-hook
   - focus-trap-react
   - use-debounce

---

## Estimated Implementation Time

| Fix | Priority | Time | Difficulty |
|-----|----------|------|------------|
| Mobile Navigation | P0 | 2 hours | Medium |
| Active Link Indicator | P0 | 30 min | Easy |
| State Persistence | P1 | 1 hour | Easy |
| Password Toggle | P1 | 30 min | Easy |
| RTL Foundation | P1 | 4 hours | Hard |
| Backdrop Click | P2 | 15 min | Easy |
| Keyboard Shortcuts | P2 | 1 hour | Medium |
| User Email Display | P2 | 1 hour | Medium |
| Loading Skeletons | Quick Win | 30 min | Easy |
| Focus Trap | Quick Win | 30 min | Easy |
| Skip Links | Quick Win | 15 min | Easy |
| Search Debounce | Quick Win | 30 min | Easy |

**Total Estimated Time**: 12 hours

**Recommended Sprint**: 2-3 days for 1 developer

---

**Next Steps**:
1. Create GitHub issues for each P0-P2 item
2. Assign to sprint backlog
3. Implement in priority order
4. Test on real devices (mobile, tablet)
5. Run Playwright E2E tests
6. Deploy to staging for QA review
