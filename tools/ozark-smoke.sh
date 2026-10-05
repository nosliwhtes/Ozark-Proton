#!/usr/bin/env bash
# Ozark smoke test: launch each game through Steam, let it run, close it, scan the Proton log.
#
#   tools/ozark-smoke.sh                 # every installed Proton game except anti-cheat skips
#   tools/ozark-smoke.sh 1313140 2406770 # just these appids
#   WAIT=120 tools/ozark-smoke.sh        # seconds to let each game run (default 90)
#
# Steam must be running. Each game uses whatever Proton Steam has mapped for it;
# the report shows which build actually ran. Report: ~/ozark-logs/smoke-<timestamp>.md
set -uo pipefail

STEAM="${STEAM_ROOT:-$HOME/.steam/debian-installation}"
APPS="$STEAM/steamapps"
LOGDIR="$HOME/ozark-logs"
FLAG="$HOME/.config/ozark/test-mode"
WAIT="${WAIT:-90}"
BOOT_TIMEOUT="${BOOT_TIMEOUT:-120}"

# Kernel anti-cheat / EAC-BattlEye titles: launching them offline proves nothing and
# repeated start/kill can flag the account. See ANTICHEAT.md.
SKIP=(553850 2479810 1144200)
# Steam runtimes / Proton builds / redistributables are not games.
NOT_GAMES=(228980 1070560 1391110 1628350 4183110 1493710 2180100 4628710)

# Every library's steamapps dir, primary first. Secondary libraries are listed
# in libraryfolders.vdf; games installed there stay invisible if only the
# primary library is scanned.
LIB_APPS=("$APPS")
if [[ -f "$APPS/libraryfolders.vdf" ]]; then
  while IFS= read -r lib; do
    [[ -d "$lib/steamapps" && "$lib/steamapps" != "$APPS" ]] && LIB_APPS+=("$lib/steamapps")
  done < <(grep -Po '"path"\s+"\K[^"]+' "$APPS/libraryfolders.vdf" | sed 's/\\\\/\\/g')
fi

mkdir -p "$LOGDIR" "$(dirname "$FLAG")"
REPORT="$LOGDIR/smoke-$(date +%Y%m%d-%H%M%S).md"

# A flag that already exists belongs to whoever set it. This run only owns
# a flag it creates itself (see the touch further down).
FLAG_PREEXISTING=0
[[ -e "$FLAG" ]] && FLAG_PREEXISTING=1
cleanup() { ((FLAG_PREEXISTING)) || rm -f "$FLAG"; }
trap cleanup EXIT
# INT and TERM have to leave, not just clean up: under one shared trap bash
# runs cleanup and then resumes the script, so Ctrl-C never stopped a run.
# The game runs under Steam, not this script, so it survives our exit unless
# we stop it first. A second INT or TERM during that stop exits at once.
ACTIVE_ID=""
on_signal() {
  trap "cleanup; exit $1" INT TERM
  [[ -n "$ACTIVE_ID" ]] && stop_game "$ACTIVE_ID"
  cleanup; exit "$1"
}
trap 'on_signal 130' INT
trap 'on_signal 143' TERM

pgrep -x steam >/dev/null || { echo "Steam is not running." >&2; exit 2; }

in_list() { local x="$1"; shift; for y in "$@"; do [[ "$x" == "$y" ]] && return 0; done; return 1; }
name_of() { local a; for a in "${LIB_APPS[@]}"; do grep -Po '"name"\s+"\K[^"]+' "$a/appmanifest_$1.acf" 2>/dev/null && return 0; done; echo "?"; }
# Proton build Steam has mapped for an appid (per-game mapping, else the global "0" default).
tool_of() {
  python3 - "$1" "$STEAM/config/config.vdf" <<'PY' 2>/dev/null || echo "?"
import re, sys
appid, path = sys.argv[1], sys.argv[2]
txt = open(path, encoding="utf-8", errors="replace").read()
m = re.search(r'"CompatToolMapping"\s*\{(.*?)\n\t{4}\}', txt, re.S)
blk = m.group(1) if m else ""
maps = dict(re.findall(r'"(\d+)"\s*\{\s*"name"\s*"([^"]*)"', blk))
print(maps.get(appid) or maps.get("0") or "?")
PY
}

if (($#)); then
  IDS=("$@")
else
  IDS=()
  for a in "${LIB_APPS[@]}"; do
    for m in "$a"/appmanifest_*.acf; do
      [[ -e "$m" ]] || continue
      id=$(grep -Po '"appid"\s+"\K\d+' "$m")
      [[ -d "$a/compatdata/$id" ]] || continue
      in_list "$id" "${NOT_GAMES[@]}" && continue
      in_list "$id" "${IDS[@]}" && continue
      IDS+=("$id")
    done
  done
fi

game_pids() { pgrep -f "AppId=$1( |$)" ; }

stop_game() {
  local id="$1" p
  for p in $(game_pids "$id"); do pkill -TERM -P "$p" 2>/dev/null; kill -TERM "$p" 2>/dev/null; done
  for _ in $(seq 1 20); do game_pids "$id" >/dev/null || return 0; sleep 1; done
  for p in $(game_pids "$id"); do pkill -KILL -P "$p" 2>/dev/null; kill -KILL "$p" 2>/dev/null; done
  sleep 3
}

touch "$FLAG"
{
  echo "# Ozark smoke test — $(date '+%F %T')"
  echo
  echo "Run window: ${WAIT}s per game. PASS = still running at the end of the window and no fatal errors in the log."
  echo
  echo "| AppID | Game | Proton | Result | Notes |"
  echo "|---|---|---|---|---|"
} > "$REPORT"

pass=0; fail=0; skip=0
for id in "${IDS[@]}"; do
  name=$(name_of "$id")
  if in_list "$id" "${SKIP[@]}"; then
    echo "| $id | $name | — | SKIP | anti-cheat (see ANTICHEAT.md) |" >> "$REPORT"; skip=$((skip+1)); continue
  fi
  log="$LOGDIR/steam-$id.log"; rm -f "$log"
  echo ">> $id $name"
  ACTIVE_ID="$id"
  xdg-open "steam://rungameid/$id" >/dev/null 2>&1 || steam "steam://rungameid/$id" >/dev/null 2>&1 &

  started=0
  for _ in $(seq 1 "$BOOT_TIMEOUT"); do game_pids "$id" >/dev/null && { started=1; break; }; sleep 1; done
  if ((started == 0)); then
    ACTIVE_ID=""
    echo "| $id | $name | ? | FAIL | never started (${BOOT_TIMEOUT}s) |" >> "$REPORT"; fail=$((fail+1)); continue
  fi

  alive=1
  for _ in $(seq 1 "$WAIT"); do game_pids "$id" >/dev/null || { alive=0; break; }; sleep 1; done
  stop_game "$id"
  ACTIVE_ID=""

  proton=$(tool_of "$id"); notes=(); log_ok=0
  if [[ -f "$log" ]]; then
    log_ok=1
    logged=$(grep -m1 -Po '^Proton: \K\S+' "$log") && proton="$logged"
    grep -qE 'Unhandled (exception|page fault)|wine: Unhandled|err:seh:.*unhandled' "$log" && notes+=("unhandled exception")
    grep -qE 'VK_ERROR_DEVICE_LOST|DXGI_ERROR_DEVICE_(REMOVED|HUNG)' "$log" && notes+=("GPU device lost")
    grep -qE 'err:module:import_dll' "$log" && notes+=("missing DLL")
  else
    # Logging comes from Ozark's user_settings.py test mode; other builds write no log.
    notes+=("no log (build has no Ozark test mode); liveness only")
  fi
  ((alive == 0)) && notes+=("exited before ${WAIT}s")

  if ((alive == 1)) && ((log_ok == 1)) && ! printf '%s\n' "${notes[@]}" | grep -qE 'unhandled|device lost'; then
    res=PASS; pass=$((pass+1))
  else
    res=FAIL; fail=$((fail+1))
  fi
  n=$(IFS='; '; echo "${notes[*]:-}")
  echo "| $id | $name | $proton | $res | ${n:-—} |" >> "$REPORT"
  sleep 5
done

{ echo; echo "**$pass pass · $fail fail · $skip skipped.** Logs: \`$LOGDIR/steam-<appid>.log\`"; } >> "$REPORT"
echo "Report: $REPORT"
((fail == 0))
