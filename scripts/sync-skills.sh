#!/usr/bin/env bash
# Select installed agent runtimes and sync complete skills from the canonical store.
set -euo pipefail

ROOT="${WONSKY_AGENTS_HOME:-$HOME/.wonsky-agents}"
SOURCE="$ROOT/skills"
DRY_RUN=0
ALL=0
TARGET_FILTER=""

usage() {
  cat <<'USAGE'
Usage: sync-skills.sh [--dry-run] [--all] [--targets cursor,claude,codex,antigravity,agents]

With no target option, detects installed/configured agent runtimes and opens a
multiple-selection list (macOS dialog when available, terminal prompt otherwise).
USAGE
}

while (($#)); do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --all) ALL=1 ;;
    --targets)
      (($# >= 2)) || { echo "error: --targets needs a comma-separated value" >&2; exit 2; }
      TARGET_FILTER="$2"; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "error: unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

[[ -d "$SOURCE" ]] || { echo "error: canonical skills directory not found: $SOURCE" >&2; exit 1; }

labels=()
keys=()
paths=()
add_target() {
  labels+=("$1")
  keys+=("$2")
  paths+=("$3")
}
app_exists() {
  [[ -d "/Applications/$1.app" || -d "$HOME/Applications/$1.app" ]]
}

# A runtime is offered when its skill/config folder or application is present.
if [[ -d "$HOME/.cursor" ]] || app_exists Cursor; then
  add_target "Cursor" cursor "$HOME/.cursor/skills"
fi
if [[ -d "$HOME/.claude" ]] || app_exists Claude; then
  add_target "Claude Code" claude "$HOME/.claude/skills"
fi
if [[ -d "$HOME/.codex" ]] || app_exists Codex; then
  add_target "Codex" codex "$HOME/.codex/skills"
fi
if [[ -d "$HOME/.gemini/config" ]] || app_exists Antigravity; then
  add_target "Antigravity" antigravity "$HOME/.gemini/config/skills"
fi
if [[ -d "$HOME/.agents" ]]; then
  add_target "Agents standard (~/.agents)" agents "$HOME/.agents/skills"
fi

((${#labels[@]})) || { echo "No supported agent runtimes detected." >&2; exit 1; }

selected=()
if [[ -n "$TARGET_FILTER" ]]; then
  IFS=',' read -r -a requested <<< "$TARGET_FILTER"
  for request in "${requested[@]}"; do
    found=0
    for i in "${!keys[@]}"; do
      if [[ "${keys[$i]}" == "$request" ]]; then selected+=("$request"); found=1; break; fi
    done
    ((found)) || { echo "error: target '$request' is not detected; available: ${keys[*]}" >&2; exit 2; }
  done
elif (( ALL )); then
  selected=("${keys[@]}")
elif (( DRY_RUN )); then
  echo "Detected runtimes: ${labels[*]}"
  echo "Dry run only. Use --all or --targets to preview specific destinations without a dialog."
  exit 0
elif [[ -t 0 && -t 1 ]] && command -v osascript >/dev/null 2>&1; then
  apple_list="{" 
  for label in "${labels[@]}"; do
    escaped=${label//\\/\\\\}; escaped=${escaped//\"/\\\"}
    apple_list+="\"$escaped\","
  done
  apple_list="${apple_list%,}}"
  choice=$(osascript -e "choose from list $apple_list with prompt \"Select where to sync skills\" with title \"Wonsky Skills\" with multiple selections allowed" 2>/dev/null || true)
  [[ "$choice" != "false" && -n "$choice" ]] || { echo "No runtimes selected."; exit 0; }
  IFS=',' read -r -a chosen_labels <<< "$choice"
  for chosen in "${chosen_labels[@]}"; do
    chosen=${chosen# }
    for i in "${!labels[@]}"; do [[ "${labels[$i]}" == "$chosen" ]] && selected+=("${keys[$i]}"); done
  done
else
  echo "Detected runtimes (enter numbers separated by spaces; empty cancels):"
  for i in "${!labels[@]}"; do printf '  [%d] %s\n' "$((i+1))" "${labels[$i]}"; done
  read -r -p '> ' answer
  [[ -n "$answer" ]] || { echo "No runtimes selected."; exit 0; }
  for n in $answer; do
    [[ "$n" =~ ^[0-9]+$ ]] && (( n >= 1 && n <= ${#labels[@]} )) || { echo "error: invalid selection '$n'" >&2; exit 2; }
    selected+=("${keys[$((n-1))]}")
  done
fi

((${#selected[@]})) || { echo "No runtimes selected."; exit 0; }

skill_count=0
for src in "$SOURCE"/*/; do [[ -f "$src/SKILL.md" ]] && ((skill_count+=1)); done
copies=0
for key in "${selected[@]}"; do
  for i in "${!keys[@]}"; do
    [[ "${keys[$i]}" == "$key" ]] || continue
    target=${paths[$i]}
    echo "→ ${labels[$i]}: $target"
    for src in "$SOURCE"/*/; do
      [[ -f "$src/SKILL.md" ]] || continue
      name=$(basename "$src")
      if (( DRY_RUN )); then
        echo "  would sync $name"
      else
        mkdir -p "$target/$name"
        rsync -a --delete --exclude='.DS_Store' "$src/" "$target/$name/"
      fi
    done
    ((copies+=1))
    break
  done
done
if (( DRY_RUN )); then
  echo "dry run complete; $skill_count skills × $copies selected runtimes; no files changed."
else
  echo "synced $skill_count skills to $copies selected runtimes."
fi
