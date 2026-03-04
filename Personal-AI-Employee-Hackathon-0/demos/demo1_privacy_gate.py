"""Demo 1: Privacy Gate — live redaction of sensitive data."""
from watchers.privacy_gate import run_privacy_gate

tests = [
    ("Normal email",    "Can we meet Tuesday?"),
    ("OTP in message",  "Your OTP is 847291, valid for 5 minutes"),
    ("Card number",     "My card 4532 1234 5678 9010 was declined"),
    ("Password",        "Reset password: MyP@ssw0rd123"),
    ("PIN",             "ATM PIN is 4821, please don't share"),
    ("Clean business",  "Please review the attached proposal by EOD"),
]

print("\n🔒 Privacy Gate — Live Demo")
print("=" * 50)
for label, body in tests:
    result = run_privacy_gate(body, "text", None)
    flagged = result.media_blocked or result.redaction_applied
    status = "🔴 REDACTED" if flagged else "✅ PASSED"
    print(f"\n{status}  {label}")
    print(f"  Input:  {body}")
    if flagged:
        print(f"  Reason: {result.alert_message}")
        print(f"  Output: {result.body}")
    else:
        print(f"  Output: {result.body}")
print("\n" + "=" * 50)
print("Privacy Gate demo complete.\n")
