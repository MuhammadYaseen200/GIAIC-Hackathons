# ADR-002: Better Auth Integration - Server-Side JWT vs. Client-Side Session

**Status**: Accepted
**Date**: 2025-12-12
**Context**: Feature 001-physical-ai-textbook
**Deciders**: System (Claude Sonnet 4.5), pending human approval

## Context and Problem Statement

User Story 3 (Personalization) and User Story 4 (Urdu Translation) require user authentication to:
1. Collect user background during signup (software/hardware experience levels)
2. Restrict personalization and translation features to logged-in users
3. Maintain user sessions across page navigations

Better Auth library supports multiple integration patterns. We need to decide between:
1. **Server-side JWT tokens**: FastAPI validates tokens, manages sessions in Neon database
2. **Client-side sessions**: Better Auth client library handles sessions in browser localStorage

This decision impacts security, user experience, and backend complexity.

## Decision Drivers

- **Security**: User credentials and session tokens must be protected
- **Statelessness**: Backend should minimize session state storage (Neon 0.5GB limit)
- **User experience**: Seamless authentication without excessive redirects
- **Mobile compatibility**: Solution must work on mobile browsers
- **Hackathon timeline**: Must implement authentication quickly (bonus feature, not base requirement)

## Considered Options

### Option A: Server-Side JWT Tokens

**Architecture**:
- **Signup/Signin flow**: Frontend sends credentials to FastAPI `/auth/signup` or `/auth/signin`
- **Token generation**: FastAPI generates JWT with user_id and profile data, signs with `AUTH_SECRET`
- **Storage**: JWT stored in browser localStorage (or httpOnly cookie for enhanced security)
- **Validation**: Every protected request (personalize, translate) includes JWT in `Authorization: Bearer <token>` header
- **Session management**: FastAPI validates JWT signature and expiration on each request

**Pros**:
- ✅ **Stateless**: No session storage in database (JWT contains all user data)
- ✅ **Scalability**: No database lookup required for authentication (just signature validation)
- ✅ **Standard pattern**: Industry-standard approach for API authentication
- ✅ **Fine-grained control**: FastAPI has full control over token expiration, refresh logic
- ✅ **Neon database savings**: No sessions table required (saves storage for 0.5GB limit)

**Cons**:
- ❌ **Token revocation complexity**: Revoking a JWT before expiration requires blacklist (adds state)
- ❌ **Initial implementation overhead**: Must implement JWT signing, validation, refresh logic
- ❌ **XSS vulnerability if using localStorage**: If JWT in localStorage, vulnerable to script injection (mitigated by httpOnly cookies)

### Option B: Client-Side Better Auth Sessions

**Architecture**:
- **Signup/Signin flow**: Better Auth client library sends credentials to Better Auth service
- **Session management**: Better Auth handles session tokens in browser
- **Backend integration**: FastAPI trusts Better Auth session validation via SDK
- **Storage**: Sessions managed by Better Auth (unclear if this uses localStorage or cookies)

**Pros**:
- ✅ **Faster implementation**: Better Auth SDK handles authentication logic
- ✅ **Reduced backend code**: No need to write JWT signing/validation
- ✅ **Session refresh built-in**: Better Auth handles token expiration automatically

**Cons**:
- ❌ **Third-party dependency**: Reliance on Better Auth service availability
- ❌ **Limited customization**: Constrained by Better Auth's architecture
- ❌ **Unclear database usage**: Better Auth may store sessions in Neon, consuming 0.5GB limit
- ❌ **Integration complexity**: FastAPI must integrate Better Auth SDK (unclear Python support)
- ❌ **Lock-in risk**: Migrating away from Better Auth requires rewrite

## Decision Outcome

**Chosen option**: **Option A - Server-Side JWT Tokens**

**Rationale**:
1. **Stateless aligns with constitution Principle V (RAG-Native)**: JWT approach avoids database sessions, preserving Neon 0.5GB limit for chat history (higher priority than session storage).
2. **Standard FastAPI pattern**: JWT authentication is well-documented in FastAPI tutorials. Implementation is ~100 lines of code (vs. uncertain Better Auth Python SDK integration).
3. **Full control over user profile**: User background data (software_level, hardware_level) stored in JWT payload, eliminating database lookup on personalization requests.
4. **Better Auth SDK uncertainty**: Better Auth documentation unclear on Python backend integration. Client-side library is JavaScript-focused. Safer to use standard JWT pattern.
5. **Hackathon risk mitigation**: JWT implementation is proven pattern. Better Auth integration could introduce unknown issues close to deadline.

### Consequences

**Positive**:
- No sessions table in Neon (saves ~100KB per 100 users)
- FastAPI `/personalize` and `/translate` endpoints validate JWT without database query
- User profile data (software_level, hardware_level) embedded in JWT claims
- Standard security pattern (easier for judges to evaluate during hackathon review)

**Negative**:
- Cannot revoke JWT before expiration (acceptable: set short expiration like 24 hours)
- Must implement JWT signing, validation, and refresh logic (acceptable: ~100 lines using `python-jose` library)
- localStorage vulnerability if not using httpOnly cookies (mitigation: use httpOnly cookies for production)

### Implementation Notes

**JWT payload structure**:
```python
{
  "sub": "user_id",  # Subject (user UUID)
  "email": "student@example.com",
  "software_level": "beginner",
  "hardware_level": "none",
  "robotics_background": false,
  "exp": 1735689600  # Expiration timestamp (24 hours)
}
```

**FastAPI authentication dependency**:
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt, JWTError

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, AUTH_SECRET, algorithms=["HS256"])
        return payload  # Contains user_id and profile
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Frontend token storage** (using httpOnly cookie for security):
```typescript
// After successful login, backend sets httpOnly cookie
// Frontend doesn't access token directly (XSS protection)

// For API requests, browser automatically includes cookie
fetch('https://api.example.com/personalize', {
  method: 'POST',
  credentials: 'include',  // Send cookies cross-origin
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ chapter_id: 'module1-week3' })
});
```

**Better Auth usage** (limited to UI library only):
- Use Better Auth React components for signup/signin forms (good UX)
- Forms submit to FastAPI `/auth/signup` and `/auth/signin` (not Better Auth service)
- FastAPI handles password hashing (bcrypt), JWT generation, Neon user storage
- Better Auth provides UI only, not authentication logic

## Alternative Considered: Hybrid Approach

Use Better Auth for signup/signin **UI components** but FastAPI for **authentication logic**.

**Why this is acceptable**:
- Better Auth React components provide polished forms (email validation, password strength, error messages)
- Forms POST to FastAPI endpoints (not Better Auth service)
- FastAPI controls authentication entirely
- No lock-in to Better Auth backend

**Decision**: Implement this hybrid approach. Use Better Auth client library for UI, FastAPI for backend logic.

## Links

- **Feature spec**: specs/001-physical-ai-textbook/spec.md (FR-013 to FR-017)
- **Implementation plan**: specs/001-physical-ai-textbook/plan.md (Phase 2.4)
- **Related ADRs**: ADR-001 (Deployment strategy), ADR-003 (RAG chunking strategy)
- **Reference**: FastAPI JWT tutorial: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
