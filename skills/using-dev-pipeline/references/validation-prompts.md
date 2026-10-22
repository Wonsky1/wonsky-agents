# Validation Prompts

Use these prompts to check whether the local workflow tends to route through `using-dev-pipeline` and `dev-pipeline` instead of bypassing them.

## Entry-point prompts

- `plan a retry strategy for notification delivery`
- `fix duplicate sends in the notifier`
- `review my current branch`
- `is the notifier issue actually fixed`
- `help me refactor this service`
- `how should we structure this change`
- `implement this approved plan`
- `add tests for throttling logic`
- `brainstorm the auth flow`
- `what's the best architecture for this`

## Expected first route

- planning / design / refactor / implementation → `using-dev-pipeline` then `dev-pipeline`
- bug / failure / regression → `using-dev-pipeline` then `systematic-debugging`
- review → `using-dev-pipeline` then `requesting-code-review`
- completion claim → `using-dev-pipeline` then `verification-before-completion`
- creative work → `using-dev-pipeline` then `brainstorming`

## What counts as a miss

- Direct code changes without routing
- File inspection before route selection
- Jumping to implementation on an unknown-cause bug
- Claiming "fixed" or "done" without verification
- Skipping brainstorming for creative feature work
