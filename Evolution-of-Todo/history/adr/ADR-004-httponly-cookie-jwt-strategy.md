# ADR-004: HTTP-Only Cookie Strategy for JWT Authentication

**Status**: Accepted
**Date**: 2025-12-29
**Deciders**: Lead Architect, UX Frontend Developer
**Applies To**: Phase II (Full-Stack Web Application)
**Supersedes**: N/A
**Related**: CL-001 (Clarification)

---

## Context

Phase II introduces user authentication with JWT tokens. A critical decision is where to store the JWT token on the client side:

**Problem Statement**: Single Page Applications (SPAs) commonly store JWT tokens in localStorage or sessionStorage. However, this approach is vulnerable to Cross-Site Scripting (XSS) attacks, where malicious scripts can access and exfiltrate tokens.

**Constraints**:
1. Backend (FastAPI) must remain stateless, expecting `Authorization: Bearer <token>` headers
2. Frontend (Next.js) must securely store tokens across page refreshes
3. Security is paramount - XSS attack vectors must be mitigated
4. Solution must work with Server-Side Rendering (SSR) and Server Actions

**Technical Context**:
- Next.js 15+ App Router with Server Components and Server Actions
- FastAPI backend with standard JWT validation middleware
- Multi-tenant application with user data isolation

---

## Decision

**Use HTTP-only cookies for JWT storage, with Next.js Middleware extracting the token and injecting the `Authorization: Bearer` header for backend requests.**

### Implementation Pattern

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Browser       │    │   Next.js       │    │   FastAPI       │
│                 │    │   Middleware    │    │   Backend       │
│ Cookie: auth=   │───▶│ Extract cookie  │───▶│ Validate Bearer │
│ <jwt>           │    │ Add: Bearer     │    │ Extract user_id │
│ (httpOnly)      │    │ header          │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Components**:
1. **Login Server Action**: Sets `auth-token` cookie with `httpOnly: true, secure: true, sameSite: 'lax'`
2. **Next.js Middleware** (`middleware.ts`): Reads cookie, adds `Authorization: Bearer <token>` header
3. **FastAPI Dependency**: Validates Bearer token from header (unchanged from standard pattern)

---

## Consequences

### Positive

| Benefit | Description |
|---------|-------------|
| XSS Protection | JavaScript cannot access httpOnly cookies, eliminating token theft via XSS |
| Backend Statelessness | Backend validates standard Bearer tokens, unaware of cookie mechanism |
| SSR Compatibility | Server Actions can access cookies via `next/headers` |
| Automatic Transmission | Browser automatically sends cookies on same-origin requests |
| Session Persistence | Token survives page refreshes and browser restarts (based on `maxAge`) |

### Negative

| Drawback | Mitigation |
|----------|------------|
| CSRF Vulnerability | Use `sameSite: 'lax'` or `'strict'`; mutations via Server Actions (POST) |
| Cookie Size Limit | JWTs should be minimal; store only `sub`, `iat`, `exp` claims |
| Cross-Domain Complexity | Next.js API proxy eliminates CORS; frontend and API share origin |
| Middleware Overhead | Minimal; runs on Edge Runtime, fast extraction |

### Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Token leakage via MITM | Low | High | `secure: true` enforces HTTPS |
| Token replay | Medium | Medium | Short expiration (24h), refresh flow in Phase III |
| Cookie parsing errors | Low | Medium | Robust error handling in middleware |

---

## Alternatives Considered

### Alternative 1: localStorage Storage

**Approach**: Store JWT in localStorage, send via `Authorization` header from client.

**Pros**:
- Simple implementation
- Works with any backend

**Cons**:
- Vulnerable to XSS attacks (JavaScript can access localStorage)
- Requires custom header management on every fetch

**Rejected Because**: Security is a primary concern; XSS vulnerability is unacceptable.

### Alternative 2: Server-Side Session (Traditional)

**Approach**: Store session ID in cookie, maintain session state on server.

**Pros**:
- No token in client at all
- Easy session invalidation

**Cons**:
- Backend becomes stateful (violates architecture principles)
- Requires session store (Redis, database)
- Scaling complexity

**Rejected Because**: Contradicts stateless API design; adds infrastructure dependency.

### Alternative 3: Token in httpOnly Cookie Only (No Header Injection)

**Approach**: Backend reads JWT directly from cookie.

**Pros**:
- Simpler middleware

**Cons**:
- Backend must be cookie-aware
- Harder to test with tools like Postman
- Less standard for REST APIs

**Rejected Because**: Keeps backend coupled to cookie mechanism; reduces testability.

---

## Implementation Notes

### Frontend Middleware

```typescript
// frontend/middleware.ts
export function middleware(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith('/api/')) {
    const token = request.cookies.get('auth-token')?.value
    const headers = new Headers(request.headers)
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
    return NextResponse.next({ request: { headers } })
  }
  return NextResponse.next()
}
```

### Cookie Configuration

```typescript
// When setting cookie on login
cookieStore.set('auth-token', token, {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax',
  maxAge: 60 * 60 * 24, // 24 hours
  path: '/',
})
```

---

## References

- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [Next.js Middleware Documentation](https://nextjs.org/docs/app/building-your-application/routing/middleware)
- Phase 2 Specification: `phase-2-web/specs/spec.md` (Section: Clarifications CL-001)
- Phase 2 Architecture: `phase-2-web/specs/architecture.md`

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2025-12-29 | Lead Architect | Initial ADR created |
