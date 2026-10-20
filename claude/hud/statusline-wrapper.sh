#!/usr/bin/env bash
# Combines ponytail's mode badge with the OMC HUD on one statusline.
dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
input=$(cat)

for f in "$dir"/plugins/cache/ponytail/ponytail/*/hooks/ponytail-statusline.sh; do
  if [ -f "$f" ]; then
    bash "$f"
    printf ' '
  fi
  break
done

printf '%s' "$input" | node "$dir/hud/omc-hud.mjs"
