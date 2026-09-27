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

mkdir -p "$LOGDIR" "$(dirname "$FLAG")"
REPORT="$LOGDIR/smoke-$(date +%Y%m%d-%H%M%S).md"

cleanup() { rm -f "$FLAG"; }
trap cleanup EXIT INT TERM

pgrep -x steam >/dev/null || { echo "Steam is not running." >&2; exit 2; }

in_list() { local x="$1"; shift; for y in "$@"; do [[ "$x" == "$y" ]] && return 0; done; return 1; }
name_of() { grep -Po '"name"\s+"\K[^"]+' "$APPS/appmanifest_$1.acf" 2>/dev/null || echo "?"; }

if (($#)); then
  IDS=("$@")
else
  IDS=()
  for m in "$APPS"/appmanifest_*.acf; do
    id=$(grep -Po '"appid"\s+"\K\d+' "$m")
    [[ -d "$APPS/compatdata/$id" ]] || continue
    in_list "$id" "${NOT_GAMES[@]}" && continue
    IDS+=("$id")
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
  xdg-open "steam://rungameid/$id" >/dev/null 2>&1 || steam "steam://rungameid/$id" >/dev/null 2>&1 &

  started=0
  for _ in $(seq 1 "$BOOT_TIMEOUT"); do game_pids "$id" >/dev/null && { started=1; break; }; sleep 1; done
  if ((started == 0)); then
    echo "| $id | $name | ? | FAIL | never started (${BOOT_TIMEOUT}s) |" >> "$REPORT"; fail=$((fail+1)); continue
  fi

  alive=1
  for _ in $(seq 1 "$WAIT"); do game_pids "$id" >/dev/null || { alive=0; break; }; sleep 1; done
  stop_game "$id"

  proton="?"; notes=()
  if [[ -f "$log" ]]; then
    proton=$(grep -m1 -Po '^Proton: \K\S+' "$log" || echo "?")
    grep -qE 'Unhandled (exception|page fault)|wine: Unhandled|err:seh:.*unhandled' "$log" && notes+=("unhandled exception")
    grep -qE 'VK_ERROR_DEVICE_LOST|DXGI_ERROR_DEVICE_(REMOVED|HUNG)' "$log" && notes+=("GPU device lost")
    grep -qE 'err:module:import_dll' "$log" && notes+=("missing DLL")
  else
    notes+=("no Proton log (native/non-Proton launch?)")
  fi
  ((alive == 0)) && notes+=("exited before ${WAIT}s")

  if ((alive == 1)) && ! printf '%s\n' "${notes[@]}" | grep -qE 'unhandled|device lost'; then
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
