# Sourced by deploy_*_lambda.sh. CI (CodePipeline) owns Lambda CODE; these scripts own infrastructure
# (layer, env/secrets, memory/timeout, schedule, first-time creation). Decided 2026-09-24 (Gabe, option 1):
# a local deploy may ship code only when every packaged file matches origin/main exactly, so production
# code always equals main. Emergency override: ALLOW_LOCAL_CODE=1 (e.g. CI itself is broken).
#   usage: code_guard <modules-file> <extra paths...>   -> sets CODE_OK=1 or 0 and prints why
code_guard() {
  local list="$1"; shift
  local files=("$list" "$@")
  while IFS= read -r m; do files+=("src/lib/$m"); done < <(grep -v '^[[:space:]]*#' "$list" | grep .)
  CODE_OK=0
  if [ "${ALLOW_LOCAL_CODE:-0}" = 1 ]; then
    echo ">> ⚠ ALLOW_LOCAL_CODE=1 -- shipping the working tree's code (bypassing CI). Commit + push it after."
    CODE_OK=1; return
  fi
  if ! git fetch -q origin main 2>/dev/null; then
    echo ">> code guard: cannot reach origin -- infra-only deploy (code left to CI)"; return
  fi
  if git diff --quiet origin/main -- "${files[@]}" && [ -z "$(git ls-files --others --exclude-standard -- "${files[@]}")" ]; then
    echo ">> code guard: packaged files match origin/main -- code deploy allowed (identical to what CI ships)"
    CODE_OK=1
  else
    echo ">> code guard: packaged files differ from origin/main -- INFRA-ONLY deploy. Code ships through CI:"
    echo "   commit + push to main; the pipeline redeploys. Differing files:"
    git diff --name-only origin/main -- "${files[@]}" | sed 's/^/     /'
  fi
}
