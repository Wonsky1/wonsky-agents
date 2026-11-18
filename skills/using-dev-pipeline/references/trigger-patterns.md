# Trigger Patterns

Use this file when refining the bootstrap routing behavior or checking whether the descriptions are broad enough.

## Requests that should activate `wa-using-dev-pipeline`

- "help me build this feature"
- "fix this bug"
- "why is this test failing"
- "review my changes"
- "is this actually fixed"
- "what architecture should we use here"
- "make a plan for this refactor"
- "add tests for this"
- "can you improve this code"
- "what should happen with this branch"
- "brainstorm ideas for this feature"
- "let's design this service"

## Route hints

- Feature, refactor, implementation request → `wa-dev-pipeline`
- Bug, regression, flaky test, unexpected behavior → `wa-systematic-debugging`
- Existing approved plan → `wa-executing-plans` or `wa-subagent-driven-development`
- Review request → `wa-requesting-code-review`
- Review comments received → `wa-receiving-code-review`
- "done/fixed/passing?" → `wa-verification-before-completion`
- Post-verification merge/PR/cleanup request → `wa-finishing-a-development-branch`
- Creative / exploratory work → `wa-brainstorming`

## Fail-safe rule

If a request is software-related and no specialist route is obviously a better fit, route to `wa-dev-pipeline`.
