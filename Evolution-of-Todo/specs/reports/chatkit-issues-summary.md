# ChatKit Frontend Issues - Quick Reference

**Date**: 2026-01-12
**Full Report**: See `chatkit-frontend-analysis.md`

---

## Critical Issues (Fix Immediately)

### 1. Dead Code - Duplicate Chat Implementation
**Files to Delete**:
```
components/chat/ChatContainer.tsx
components/chat/Message.tsx
components/chat/MessageList.tsx
components/chat/MessageInput.tsx
components/chat/ToolCallBadge.tsx
components/chat/ToolCallIndicator.tsx
components/chat/LoadingIndicator.tsx
app/actions/chat.ts
```

**Reason**: These implement a custom React chat that conflicts with OpenAI ChatKit web component.

**Action**: Delete or move to `components/chat/_archive/` with README explaining deprecation.

---

### 2. TypeScript Import Errors
**File**: `components/chat/ChatKit.tsx:4`

**Current** (fails):
```typescript
import type { OpenAIChatKit, ChatKitOptions } from "@openai/chatkit"
```

**Fix**:
```typescript
import type { OpenAIChatKit, ChatKitOptions } from "@openai/chatkit/types"
```

**Reason**: Package types are in `/types/` subdirectory, not root exports.

---

### 3. Missing Environment Validation
**File**: `app/dashboard/chat/page.tsx:6`

**Current**:
```typescript
const CHATKIT_DOMAIN_KEY = process.env.NEXT_PUBLIC_CHATKIT_KEY || ""
```

**Issue**: Silent failure if key is missing (empty string passed to ChatKit)

**Fix**:
```typescript
const CHATKIT_DOMAIN_KEY = process.env.NEXT_PUBLIC_CHATKIT_KEY

if (!CHATKIT_DOMAIN_KEY) {
  throw new Error("NEXT_PUBLIC_CHATKIT_KEY environment variable is required")
}
```

---

### 4. Insecure CORS Headers
**Files**:
- `app/api/chatkit/route.ts:46,100`
- `app/api/chatkit/[...path]/route.ts:49,100`

**Current**:
```typescript
"Access-Control-Allow-Origin": "*"
```

**Issue**: Allows ANY origin to make requests (security risk)

**Fix**:
```typescript
"Access-Control-Allow-Origin": "https://cdn.platform.openai.com"
```

---

## High Priority Issues

### 5. Missing Error Handling in Proxy
**Files**:
- `app/api/chatkit/route.ts:11-50`
- `app/api/chatkit/[...path]/route.ts:14-54`

**Issue**: No try-catch around fetch() or cookie extraction

**Fix**: Add error handling:
```typescript
async function proxyRequest(request: NextRequest, path: string) {
  try {
    const cookieStore = await cookies()
    const token = cookieStore.get("auth-token")?.value
    // ... rest of logic
  } catch (error) {
    console.error("Proxy error:", error)
    return new NextResponse(
      JSON.stringify({ error: "Proxy request failed" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    )
  }
}
```

---

### 6. Duplicate Proxy Logic
**Issue**: Same proxy logic duplicated in two route files

**Fix**: Extract to shared utility:
```typescript
// lib/chatkit-proxy.ts
export async function proxyToChatKitBackend(
  request: NextRequest,
  path: string = ""
): Promise<NextResponse> {
  // Shared proxy logic
}

// Then use in both route files:
import { proxyToChatKitBackend } from "@/lib/chatkit-proxy"

export async function POST(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params
  return proxyToChatKitBackend(request, path?.join("/") || "")
}
```

---

### 7. Redundant Custom Fetch
**File**: `components/chat/ChatKit.tsx:56-62`

**Issue**: Custom fetch with `credentials: "include"` is unnecessary

**Reason**:
- `/api/chatkit` is same-origin (browser auto-includes cookies)
- Proxy already extracts cookies server-side

**Fix**: Remove custom fetch function (use default):
```typescript
// DELETE THIS:
fetch: async (input: RequestInfo | URL, init?: RequestInit) => {
  const response = await fetch(input, {
    ...init,
    credentials: "include",
  })
  return response
},
```

---

## Medium Priority Issues

### 8. Duplicate Environment Variables
**File**: `.env.local`

**Issue**: Two variables for same backend URL:
```bash
NEXT_PUBLIC_API_URL="http://localhost:8000"  # Used in dead code
BACKEND_URL="http://localhost:8000"          # Used in proxy
```

**Fix**: Remove `NEXT_PUBLIC_API_URL` (only used in deleted `chat.ts`)

---

### 9. Missing Error Boundary
**File**: `app/dashboard/chat/page.tsx`

**Issue**: No error boundary - ChatKit failures crash entire page

**Fix**: Add error boundary:
```typescript
// components/chat/ChatKitErrorBoundary.tsx
export class ChatKitErrorBoundary extends React.Component {
  componentDidCatch(error: Error) {
    console.error("ChatKit error:", error)
  }

  render() {
    if (this.state.hasError) {
      return <div>Failed to load chat. Please refresh.</div>
    }
    return this.props.children
  }
}
```

---

### 10. Missing Event Handlers
**File**: `components/chat/ChatKit.tsx:110-126`

**Currently Handles**:
- `chatkit.ready`
- `chatkit.error`
- `chatkit.thread.change`

**Missing**:
- `chatkit.response.start` / `chatkit.response.end` - for loading indicators
- `chatkit.tool.change` - for analytics
- `chatkit.log` - for debugging
- `chatkit.effect` - for client-side effects

**Fix**: Add comprehensive event logging for production monitoring

---

## Quick Wins

### 11. Add DOM Type Augmentation
**File**: `tsconfig.json`

**Add**:
```json
{
  "compilerOptions": {
    "types": ["@openai/chatkit/types/dom-augment"]
  }
}
```

This registers `<openai-chatkit>` as valid HTML element.

---

### 12. Add TypeScript Strict Null Checks
**File**: `components/chat/ChatKit.tsx:60`

**Current**:
```typescript
const { path } = await params
return proxyRequest(request, path?.join("/") || "")
```

**Issue**: `path` could be undefined (TypeScript allows it)

**Fix**: Add explicit check:
```typescript
const { path } = await params
if (!path) {
  return new NextResponse("Invalid path", { status: 400 })
}
return proxyRequest(request, path.join("/"))
```

---

## Testing Checklist

After fixes, verify:

- [ ] `npm run build` succeeds without errors
- [ ] `npx tsc --noEmit` passes without type errors
- [ ] ChatKit loads in browser without console errors
- [ ] Authentication works (cookie forwarded correctly)
- [ ] Tool calls (add_task, list_tasks) execute successfully
- [ ] Error states display correctly (backend down, invalid token)
- [ ] Mobile viewport works (responsive design)

---

## Estimated Effort

| Priority | Tasks | Effort |
|----------|-------|--------|
| Critical | 4 issues | 2-4 hours |
| High | 3 issues | 4-6 hours |
| Medium | 3 issues | 4-6 hours |
| **Total** | **10 issues** | **10-16 hours** |

---

## Risk Assessment

**Current State**: 🟡 **MEDIUM RISK**

**Risks**:
1. Dead code confuses developers (may accidentally use wrong implementation)
2. Type errors prevent TypeScript compilation in strict mode
3. Missing error handling causes silent failures
4. CORS headers too permissive (potential security issue)

**After Fixes**: 🟢 **LOW RISK**

Production-ready with proper error handling, type safety, and security.

---

**Next Steps**:
1. Review this summary with team
2. Prioritize fixes based on deployment timeline
3. Assign tasks to developers
4. Test thoroughly before merging to main branch

**Full Details**: See `chatkit-frontend-analysis.md` for complete analysis with code examples and architecture diagrams.
