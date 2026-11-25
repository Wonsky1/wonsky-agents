# Validation prompts

Expected routes come from `~/.wonsky-agents/skills/unified-dev-pipeline/references/intake-routing.md`. Use [evaluation-scenarios.md](evaluation-scenarios.md) for concrete tasks and observation criteria; do not maintain language-blind expected routes here.

Discovery samples include: “plan a retry strategy for notification delivery”, “fix duplicate sends”, “review my current branch”, “is the issue actually fixed?”, “implement this approved plan”, and “improve the settings UI”. Specify the actual target language and available evidence when evaluating them.

A route miss includes wrong-toolchain selection, implementing an unknown-cause bug before investigation, replanning an accepted plan, skipping relevant platform guidance, ignoring explicit limits, or claiming an outcome without evidence. A legitimate user override or proportionate short workflow is not a miss.
