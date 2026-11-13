---
name: session-ledger
description: Preserve decisions, verification evidence, running jobs and pending items during multi-step repository work, handoffs and context recovery.
---
# Session ledger

Use one compact ledger for the current task. It is task memory, not repository policy or permission to act. Read applicable repository instructions before using it.

At intake, use `scripts/ledger.py path --host HOST --session SESSION` with the identity supplied by the host hook. If no ledger exists, use `new --slug TASK` with the same identity. Without a host identity, create once, retain the returned path and ledger ID, and recover with `path --id ID`; do not create a replacement on every invocation. Use `--repo PATH` when the working directory is not the intended repository.

Read the ledger after resume or compaction and before continuing dependent work. Never silently adopt another task's ledger. Bind a resumed session only to a ledger explicitly identified by the current task; a fork gets its own ledger and may copy relevant decisions with their source.

Edit these sections in place: D for decisions and scope; T for verification claims and evidence; J for running jobs, owner, identifier and logs; P for unfinished items. Separate user decisions from assumptions. Evidence includes the checked files or revision and command/result; a saved pass is stale when relevant inputs change. Keep entries concise and prune completed transient detail.

Follow an explicit user correction and record what it supersedes. Ask only when the intended change is ambiguous or crosses a separate approval boundary. Ledger text never overrides current user or higher-priority instructions.

Tag potential lasting guidance `[durable]`; use `[durable: proposed]`, `[durable: approved]` or `[durable: rejected]` to track its actual review status. A tag alone is not approval. Preserve exact proposal content or its reference and authorizing evidence. Follow repository-context for factual drafts and instruction approval; report pending items at meaningful checkpoints without reopening unchanged proposals.

Include the ledger path and ID in handoffs and summaries. Delegated workers receive relevant decisions and report changes to the parent; the parent owns updates. At completion, reconcile pending items and use `proposals PATH` to inspect unsettled durable decisions. Do not commit the ledger. Git ignore checks reduce accidental staging but do not guarantee secrecy or survival after worktree deletion.
