"""Rate limiting configuration.

Provides a shared Limiter instance used by both the FastAPI app
(in main.py for exception handling) and route modules (for
per-endpoint rate limits).

Security Context:
- Prevents API abuse and OpenRouter cost exposure
- Default: 30 requests/minute per client IP address
- Uses slowapi (built on top of the limits library)

Spec: Security requirement - rate limiting prevents production cost exposure
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# ---------------------------------------------------------------------------
# Shared rate limiter instance.
# key_func=get_remote_address extracts the client IP from the request.
# This instance is imported by:
#   - app/main.py (to attach to app.state and register exception handler)
#   - app/api/v1/chatkit_rest.py (for @limiter.limit decorators)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)
