# Page snapshot

```yaml
- generic [ref=e2]:
  - heading "Todo App" [level=2] [ref=e4]
  - main [ref=e5]:
    - generic [ref=e8]:
      - generic [ref=e9]:
        - heading "Sign In" [level=1] [ref=e10]
        - paragraph [ref=e11]: Welcome back! Please sign in to continue
      - generic [ref=e12]:
        - generic [ref=e13]:
          - generic [ref=e14]: Email
          - textbox "Email" [ref=e15]:
            - /placeholder: you@example.com
        - generic [ref=e16]:
          - generic [ref=e17]: Password
          - textbox "Password" [ref=e18]:
            - /placeholder: Enter your password
        - button "Sign In" [ref=e19] [cursor=pointer]
      - paragraph [ref=e21]:
        - text: Don't have an account?
        - link "Create account" [ref=e22] [cursor=pointer]:
          - /url: /register
```