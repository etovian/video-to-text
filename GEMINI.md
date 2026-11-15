# Workspace Rules: video-to-text

## Git Permissions & Environment Constraints
- **User Permission**: The user has explicitly granted full permission to create working branches, make commits, and push to GitHub.
- **IDE Sandbox Constraint**: On Windows, the Antigravity sandbox blocks write access to the `.git` directory and prevents network calls. Consequently, `git commit` and `git push` must run outside the sandbox (`BypassSandbox: true`), which requires the user to approve the IDE's system security prompt.
- **Commit Frequency**: To minimize IDE approval prompts, the assistant must keep commits to **one commit per completed task** (avoiding intermediate micro-commits).
- **Branching & Remote**: Development occurs on feature branches (`feat/*`). Merges into `main` occur after full task verification.
