# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - heading "Todo App" [level=2] [ref=e4]
    - main [ref=e5]:
      - generic [ref=e8]:
        - generic [ref=e9]:
          - heading "Create Account" [level=1] [ref=e10]
          - paragraph [ref=e11]: Get started with your todo list
        - generic [ref=e12]:
          - alert [ref=e13]: Account created successfully! Please sign in.
          - generic [ref=e14]:
            - generic [ref=e15]: Email
            - textbox "Email" [ref=e16]:
              - /placeholder: you@example.com
          - generic [ref=e17]:
            - generic [ref=e18]: Password
            - textbox "Password" [ref=e19]:
              - /placeholder: At least 8 characters
          - button "Create Account" [ref=e20] [cursor=pointer]
        - paragraph [ref=e22]:
          - text: Already have an account?
          - link "Sign in" [ref=e23] [cursor=pointer]:
            - /url: /login
  - button "Open Next.js Dev Tools" [ref=e29] [cursor=pointer]:
    - img [ref=e30]
  - alert [ref=e33]
```