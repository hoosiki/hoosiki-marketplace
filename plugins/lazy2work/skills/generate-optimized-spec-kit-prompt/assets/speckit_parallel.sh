#!/usr/bin/env bash
# speckit_parallel.sh — SpecKit 2-Phase 병렬 드라이버 (수직 웨이브)
#
#   Phase 1 (spec) : 워킹트리 하나에서 issue 개수만큼 백그라운드 병렬 → 01_specify + 02_clarify
#                    worktree 도 workmux 도 쓰지 않는다. 끝나면 게이트 통과분을 한 번에 커밋.
#   Phase 2 (build): 웨이브(= 의존성 체인) 단위 worktree → 03_plan ~ 08_converge + commit
#                    스테이지 순서대로 진행하고, 한 스테이지 안의 웨이브들은 workmux 로 병렬 실행.
#
# 웨이브는 "수직" 이다 — depth 레벨이 아니라 의존성 체인 하나가 웨이브 하나다.
#   000 → 001 → 003 ┬→ 004 → 005 → 006      w0-foundation : 000 001 003   (trunk, 먼저 돌고 main 에 머지)
#                   ├→ 007 → 008 → 009      w1-…          : 004 005 006   ┐
#                   └→ 010 → 011 → 012      w2-…          : 007 008 009   ├ 병렬
#                                           w3-…          : 010 011 012   ┘
#   웨이브 안은 순차(같은 worktree), 웨이브끼리는 병렬. 스테이지 사이에만 병합 배리어가 있다.
#
# Usage:
#   ./utilities/speckit_parallel.sh waves                       # 스테이지/웨이브 계획 출력
#   ./utilities/speckit_parallel.sh spec [--dry-run]            # Phase 1 — 전 feature 백그라운드 병렬
#   ./utilities/speckit_parallel.sh build [--dry-run]           # Phase 2 — 전 스테이지 순차 진행
#   ./utilities/speckit_parallel.sh build --stage 1             # 해당 스테이지만
#   ./utilities/speckit_parallel.sh build --from-stage 1        # 해당 스테이지부터 끝까지
#   ./utilities/speckit_parallel.sh build --wave w2-channels    # 웨이브 하나만
#   ./utilities/speckit_parallel.sh merge --wave w2-channels    # 병합만 재시도
#   ./utilities/speckit_parallel.sh merge --stage 1
#
# Options:
#   --prompts <path>   .speckit-prompts/<project> 경로 (기본: 자동 탐지 / SPECKIT_PROMPTS_DIR)
#   --stage N          해당 스테이지만
#   --from-stage N     해당 스테이지부터 끝까지
#   --wave <name>      해당 웨이브만
#   --max-concurrent N 동시 실행 수. build 기본 4 (env MAX_CONCURRENT)
#   --spec-jobs N      Phase 1 동시 프로세스 수. 기본 0 = issue 개수만큼 전부 (env SPEC_JOBS)
#   --base <branch>    분기 기준 브랜치 (기본: .workmux.yaml의 base_branch / main)
#   --rebase           웨이브 병합 시 --rebase 사용 (기본: .workmux.yaml의 merge_strategy)
#   --no-merge         병렬 실행만 하고 병합은 생략
#   --no-commit        Phase 1 에서 게이트만 돌리고 커밋은 생략
#   --dry-run          실행 없이 계획만 출력
#
# Phase 2 는 브랜치 이름으로 웨이브를 전달한다 (tmux pane 은 드라이버 env 를 상속하지 않는다):
#   build/<wave-name>      → 그 웨이브의 feature 들을 waves.json 순서대로 03~08 실행
#
# ⚠️ 사전 준비 (한 번):
#   git rm --cached .specify/feature.json 2>/dev/null; echo '.specify/feature.json' >> .gitignore
#   echo '.speckit-logs/' >> .gitignore
#   .workmux.yaml 에 layouts.speckit (단일 pane) + base_branch 명시
#   .workmux.yaml 의 pre_merge 에 env SPECKIT_VERIFY_CMD="..." 명시 — 미지정 시 게이트가
#     `uv run pytest -q` 로 폴백하고 종료 코드 ≠ 0 을 전부 실패로 본다. 기존 실패가 있는
#     저장소는 이것 때문에 모든 웨이브 병합이 영구히 막힌다.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

log()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
die()  { echo -e "${RED}[FAIL]${NC} $*" >&2; exit 1; }
head_() {
	echo ""
	echo -e "${BOLD}${BLUE}══════ $* ══════${NC}"
}

# stdin 의 각 줄(빈 줄 제외)을 전역 배열 LINES 에 담는다.
# macOS 기본 bash 는 3.2 라 mapfile/readarray 가 없다.
LINES=()
read_lines() {
	LINES=()
	local _line
	while IFS= read -r _line; do
		[ -n "$_line" ] && LINES+=("$_line")
	done
}

# ──────────────────────────────────────────────
# Arguments
# ──────────────────────────────────────────────
CMD="${1:-}"
[ -n "$CMD" ] || die "사용법: $0 <waves|spec|build|merge> [OPTIONS]  ('$0 --help' 로 전체 옵션)"
shift

PROMPTS_DIR="${SPECKIT_PROMPTS_DIR:-}"
ONLY_WAVE=""
ONLY_STAGE=""
FROM_STAGE=""
MAX_CONCURRENT="${MAX_CONCURRENT:-4}"
SPEC_JOBS="${SPEC_JOBS:-0}"
BASE_BRANCH=""
USE_REBASE=false
NO_MERGE=false
NO_COMMIT=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
	case "$1" in
	--prompts) PROMPTS_DIR="$2"; shift 2 ;;
	--wave) ONLY_WAVE="$2"; shift 2 ;;
	--stage) ONLY_STAGE="$2"; shift 2 ;;
	--from-stage) FROM_STAGE="$2"; shift 2 ;;
	--max-concurrent) MAX_CONCURRENT="$2"; shift 2 ;;
	--spec-jobs) SPEC_JOBS="$2"; shift 2 ;;
	--base) BASE_BRANCH="$2"; shift 2 ;;
	--rebase) USE_REBASE=true; shift ;;
	--no-merge) NO_MERGE=true; shift ;;
	--no-commit) NO_COMMIT=true; shift ;;
	--dry-run) DRY_RUN=true; shift ;;
	-h | --help) sed -n '2,52p' "$0"; exit 0 ;;
	*) die "알 수 없는 옵션: $1" ;;
	esac
done

# ──────────────────────────────────────────────
# Prompts 디렉터리 / waves.json 확정
# ──────────────────────────────────────────────
if [ -z "$PROMPTS_DIR" ]; then
	read_lines < <(find "$PROJECT_DIR/.speckit-prompts" -maxdepth 2 -name waves.json -type f 2>/dev/null | sort)
	_candidates=(${LINES[@]+"${LINES[@]}"})
	case "${#_candidates[@]}" in
	0) die ".speckit-prompts/*/waves.json 을 찾지 못했습니다. --prompts 로 경로를 지정하세요." ;;
	1) PROMPTS_DIR="$(dirname "${_candidates[0]}")" ;;
	*)
		warn "waves.json 이 여러 개입니다:"
		printf '  %s\n' "${_candidates[@]}"
		die "--prompts 로 하나를 지정하세요."
		;;
	esac
fi
PROMPTS_DIR="$(cd "$PROMPTS_DIR" && pwd)" || die "프롬프트 경로를 열 수 없습니다: $PROMPTS_DIR"
WAVES_FILE="$PROMPTS_DIR/waves.json"
[ -f "$WAVES_FILE" ] || die "waves.json 이 없습니다: $WAVES_FILE"

command -v python3 >/dev/null 2>&1 || die "waves.json 파싱에 python3 가 필요합니다"

# waves.json 조회 헬퍼.
# stages 키가 없는 구버전 waves.json 도 받아준다 — wave.stage 로 묶고, 그것도 없으면
# 웨이브 하나당 스테이지 하나로 강등한다(= 전부 순차. 느리지만 절대 안전).
waves_query() { python3 - "$WAVES_FILE" "$@" <<-'PYEOF'
	import json, sys
	path, mode = sys.argv[1], sys.argv[2]
	with open(path, encoding="utf-8") as fh:
	    data = json.load(fh)
	waves = data.get("waves", [])
	by_name = {w["name"]: w for w in waves}

	def stages():
	    st = data.get("stages")
	    if st:
	        return [(s.get("index", i), s.get("kind", "branch"), list(s.get("waves", [])))
	                for i, s in enumerate(st)]
	    if any("stage" in w for w in waves):
	        buckets = {}
	        for w in waves:
	            buckets.setdefault(w.get("stage", 0), []).append(w["name"])
	        out = []
	        for i, key in enumerate(sorted(buckets)):
	            names = buckets[key]
	            kind = by_name[names[0]].get("kind", "branch") if len(names) == 1 else "branch"
	            out.append((i, kind, names))
	        return out
	    return [(i, w.get("kind", "trunk"), [w["name"]]) for i, w in enumerate(waves)]

	if mode == "names":
	    print("\n".join(w["name"] for w in waves))
	elif mode == "all-features":
	    print("\n".join(f["id"] for f in data.get("features", [])))
	elif mode == "project":
	    print(data.get("project", ""))
	elif mode == "features":
	    w = by_name.get(sys.argv[3])
	    if w is None:
	        sys.exit(3)
	    print("\n".join(w.get("features", [])))
	elif mode == "wave-field":
	    w = by_name.get(sys.argv[3])
	    if w is None:
	        sys.exit(3)
	    print(w.get(sys.argv[4], ""))
	elif mode == "stage-count":
	    print(len(stages()))
	elif mode == "stage-waves":
	    idx = int(sys.argv[3])
	    for i, _kind, names in stages():
	        if i == idx:
	            print("\n".join(names))
	            break
	    else:
	        sys.exit(3)
	elif mode == "stage-kind":
	    idx = int(sys.argv[3])
	    for i, kind, _names in stages():
	        if i == idx:
	            print(kind)
	            break
	    else:
	        sys.exit(3)
	elif mode == "stage-of-wave":
	    target = sys.argv[3]
	    for i, _kind, names in stages():
	        if target in names:
	            print(i)
	            break
	    else:
	        sys.exit(3)
	elif mode == "table":
	    for i, kind, names in stages():
	        for name in names:
	            w = by_name[name]
	            feats = w.get("features", [])
	            print(f'{i}\t{kind}\t{name}\t{w.get("title", "")}\t{len(feats)}\t{" ".join(feats)}')
	PYEOF
}

PROJECT_NAME="$(waves_query project)"
STAGE_COUNT="$(waves_query stage-count)"
[ "$STAGE_COUNT" -gt 0 ] || die "waves.json 에 웨이브가 정의되어 있지 않습니다"

RUN_ROOT="$PROJECT_DIR/.speckit-logs/parallel"

# ──────────────────────────────────────────────
# waves 명령
# ──────────────────────────────────────────────
if [ "$CMD" = "waves" ]; then
	head_ "Waves — $PROJECT_NAME  ($STAGE_COUNT stages)"
	prev_stage=""
	waves_query table | while IFS=$'\t' read -r stage kind name title count feats; do
		if [ "$stage" != "$prev_stage" ]; then
			if [ "$kind" = "trunk" ]; then
				echo -e "\n  ${BOLD}Stage $stage${NC} — trunk (순차 실행 후 main 에 자동 병합)"
			else
				echo -e "\n  ${BOLD}Stage $stage${NC} — branch (웨이브끼리 병렬)"
			fi
			prev_stage="$stage"
		fi
		echo -e "    ${BOLD}${name}${NC}  (${count})  ${title}"
		for f in $feats; do echo "        → $f"; done
	done
	echo ""
	log "웨이브 안은 순차, 웨이브끼리는 병렬. 스테이지 사이에만 병합 배리어가 있습니다."
	log "프롬프트: $PROMPTS_DIR"
	exit 0
fi

# ──────────────────────────────────────────────
# Preflight
# ──────────────────────────────────────────────
preflight_common() {
	[ -x "$PROJECT_DIR/utilities/speckit_pipeline.sh" ] \
		|| die "utilities/speckit_pipeline.sh 가 없거나 실행 권한이 없습니다 (chmod +x)"

	if git ls-files --error-unmatch .specify/feature.json >/dev/null 2>&1; then
		die ".specify/feature.json 이 git 에 추적 중입니다 — 프로세스마다 덮어써서 병합이 전부 충돌합니다.
    git rm --cached .specify/feature.json && echo '.specify/feature.json' >> .gitignore"
	fi

	# git extension 의 before_specify 훅은 specify 마다 브랜치를 만든다 → Phase 1 이 한 워킹트리에서
	# N개 브랜치를 만들려다 서로를 밀어낸다.
	if [ -f "$PROJECT_DIR/.specify/extensions.yml" ] \
		&& grep -q 'before_specify' "$PROJECT_DIR/.specify/extensions.yml" 2>/dev/null; then
		warn ".specify/extensions.yml 에 before_specify 훅이 있습니다 (git extension?)"
		warn "  → specify 마다 git 브랜치를 만들므로 한 워킹트리 병렬 실행과 충돌합니다. 비활성화하세요."
	fi
}

preflight_workmux() {
	command -v workmux >/dev/null 2>&1 || die "workmux 가 필요합니다: brew install raine/workmux/workmux"
	command -v tmux >/dev/null 2>&1 || die "tmux 가 필요합니다"

	[ -f "$PROJECT_DIR/.workmux.yaml" ] || die ".workmux.yaml 이 없습니다 (프로젝트 루트에 필요)"
	grep -qE '^[[:space:]]*speckit:' "$PROJECT_DIR/.workmux.yaml" \
		|| die ".workmux.yaml 에 layouts.speckit (단일 pane) 레이아웃이 없습니다"

	[ -x "$PROJECT_DIR/utilities/wm_stage_runner.sh" ] \
		|| die "utilities/wm_stage_runner.sh 가 없거나 실행 권한이 없습니다 (chmod +x)"

	if [ -z "$BASE_BRANCH" ]; then
		local line
		line="$(grep -m1 -E '^[[:space:]]*base_branch:' "$PROJECT_DIR/.workmux.yaml" || true)"
		line="${line#*base_branch:}"
		line="${line%%#*}"
		line="${line//[[:space:]]/}"
		line="${line//\"/}"
		line="${line//\'/}"
		BASE_BRANCH="${line:-main}"
	fi
	git rev-parse --verify "$BASE_BRANCH" >/dev/null 2>&1 \
		|| die "base 브랜치를 찾을 수 없습니다: $BASE_BRANCH (--base 로 지정)"

	if ! git diff --quiet || ! git diff --cached --quiet; then
		warn "작업 트리에 커밋되지 않은 변경이 있습니다 — 병합 단계에서 막힐 수 있습니다"
	fi
}

# ──────────────────────────────────────────────
# Phase 1 — spec: 한 워킹트리에서 백그라운드 N-병렬
#
# worktree 가 필요 없는 이유: specify/clarify 는 specs/<feature>/ 안에만 쓴다.
# 프로세스마다 SPECIFY_FEATURE_DIRECTORY 가 다르므로 서로의 디렉터리를 침범할 수 없다.
# git 인덱스만이 유일한 공유 자원이라 --no-commit 으로 에이전트의 git 접근을 막고,
# 전부 끝난 뒤 드라이버가 한 번만 커밋한다.
# ──────────────────────────────────────────────
run_spec_phase() {
	local -a feats=("$@")
	local run_dir="$RUN_ROOT/spec"
	local total="${#feats[@]}"
	local limit="$SPEC_JOBS"
	[ "$limit" -le 0 ] && limit="$total"

	mkdir -p "$run_dir"
	rm -f "$run_dir"/*.status

	log "${total}개 feature 를 백그라운드 병렬 실행 (동시 ${limit}개)"
	printf '   %s\n' "${feats[@]}"

	if $DRY_RUN; then
		echo ""
		for f in "${feats[@]}"; do
			echo "  [DRY-RUN] SPECIFY_FEATURE_DIRECTORY=specs/$f  speckit_pipeline.sh --phase spec --only ${f%%-*} --no-commit &"
		done
		return 0
	fi

	local f fnum
	for f in "${feats[@]}"; do
		# 동시 실행 수 제한 (bash 3.2 에는 wait -n 이 없다)
		while [ "$(jobs -rp | wc -l | tr -d ' ')" -ge "$limit" ]; do sleep 2; done

		fnum="${f%%-*}"
		mkdir -p "$run_dir/logs/$f"
		echo "RUNNING" >"$run_dir/$f.status"
		(
			# feature 마다 로그 루트를 분리한다 — 공유하면 .last_checkpoint 가 레이스한다
			if SPECKIT_LOG_ROOT="$run_dir/logs/$f" \
				bash "$PROJECT_DIR/utilities/speckit_pipeline.sh" "$PROMPTS_DIR" \
				--phase spec --only "$fnum" --no-commit \
				</dev/null >"$run_dir/$f.log" 2>&1; then
				echo "OK" >"$run_dir/$f.status"
			else
				echo "FAIL" >"$run_dir/$f.status"
			fi
		) &
		log "  ▶ $f (pid $!)"
	done

	wait || true
	echo ""

	local -a good=() bad=()
	for f in "${feats[@]}"; do
		if [ "$(cat "$run_dir/$f.status" 2>/dev/null || true)" = "OK" ]; then
			good+=("$f")
		else
			bad+=("$f")
		fi
	done

	ok "완료 ${#good[@]}/${total}"
	if [ "${#bad[@]}" -gt 0 ]; then
		warn "실패: ${bad[*]}"
		warn "  로그: $run_dir/<feature>.log"
	fi

	[ "${#bad[@]}" -eq 0 ]
}

# ──────────────────────────────────────────────
# Phase 2 — 한 스테이지의 웨이브들을 workmux 로 병렬 실행
# ──────────────────────────────────────────────
run_stage() {
	local stage_idx="$1"
	shift
	local -a waves=("$@")
	local run_dir="$RUN_ROOT/build"

	mkdir -p "$run_dir"
	local w
	for w in "${waves[@]}"; do rm -f "$run_dir/$w.status"; done

	local matrix
	matrix="wave:$(IFS=,; echo "${waves[*]}")"

	log "${#waves[@]}개 웨이브 병렬 실행 (max-concurrent=$MAX_CONCURRENT, base=$BASE_BRANCH)"
	for w in "${waves[@]}"; do
		echo "   $w  →  $(waves_query features "$w" | tr '\n' ' ')"
	done

	local -a extra=()
	$DRY_RUN && extra+=(--dry-run)

	workmux add build \
		--foreach "$matrix" \
		--branch-template "build/{{ wave }}" \
		--base "$BASE_BRANCH" \
		--layout speckit \
		--background \
		--wait \
		--max-concurrent "$MAX_CONCURRENT" \
		${extra[@]+"${extra[@]}"}
}

# ──────────────────────────────────────────────
# 성공한 웨이브만 순차 병합 (동시 병합 금지 — main 의 index 가 레이스한다)
# 병합 순서는 waves.json 순서 = 충돌이 재현 가능한 순서다.
# ──────────────────────────────────────────────
merge_waves() {
	local -a waves=("$@")
	local run_dir="$RUN_ROOT/build"
	local -a good=() bad=()
	local w

	for w in "${waves[@]}"; do
		if $DRY_RUN || [ "$(cat "$run_dir/$w.status" 2>/dev/null || true)" = "OK" ]; then
			good+=("$w")
		else
			bad+=("$w")
		fi
	done

	if [ "${#bad[@]}" -gt 0 ]; then
		warn "실행 실패 (병합 제외): ${bad[*]}"
		warn "  로그: $run_dir/"
	fi

	local -a merge_flags=()
	$USE_REBASE && merge_flags+=(--rebase)

	for w in ${good[@]+"${good[@]}"}; do
		log "merge build/$w"
		if $DRY_RUN; then
			echo "  [DRY-RUN] workmux merge build/$w ${merge_flags[*]-}"
			continue
		fi
		if ! workmux merge "build/$w" ${merge_flags[@]+"${merge_flags[@]}"}; then
			warn "[$w] 병합 실패 — worktree 보존. 원인은 셋 중 하나입니다:"
			warn "    1) git 충돌 — 확인: git merge-tree --write-tree $BASE_BRANCH build/$w"
			warn "    2) pre_merge 게이트 거부 — 미완료 태스크 또는 검증 명령 실패."
			warn "       워크트리에서 직접: WM_BRANCH_NAME=build/$w bash utilities/wm_pre_merge_gate.sh"
			warn "    3) 훅 자체가 실행되지 못함 — .workmux.yaml 의 pre_merge 가 'VAR=... cmd' 형태면"
			warn "       셸 없이 exec 될 때 죽습니다. 'env VAR=... cmd' 로 쓰세요."
			warn "    검증 명령이 원인이면 SPECKIT_VERIFY_CMD 가 이 저장소의 기준선에 맞는지 보세요"
			warn "    (기존에도 종료 코드 ≠ 0 이면 모든 웨이브가 영구히 막힙니다)"
			bad+=("$w")
		fi
	done

	[ "${#bad[@]}" -eq 0 ]
}

# 실행할 스테이지 목록을 STAGES 전역 배열에 담는다
STAGES=()
resolve_stages() {
	STAGES=()
	local i
	if [ -n "$ONLY_WAVE" ]; then
		waves_query wave-field "$ONLY_WAVE" name >/dev/null 2>&1 \
			|| die "waves.json 에 '$ONLY_WAVE' 웨이브가 없습니다"
		return 0 # 웨이브 단독 실행은 스테이지를 쓰지 않는다
	fi
	if [ -n "$ONLY_STAGE" ]; then
		STAGES=("$ONLY_STAGE")
		return 0
	fi
	i="${FROM_STAGE:-0}"
	while [ "$i" -lt "$STAGE_COUNT" ]; do
		STAGES+=("$i")
		i=$((i + 1))
	done
	[ "${#STAGES[@]}" -gt 0 ] || die "실행할 스테이지가 없습니다 (--from-stage $FROM_STAGE / 총 $STAGE_COUNT)"
}

# ──────────────────────────────────────────────
# merge 전용 명령
# ──────────────────────────────────────────────
if [ "$CMD" = "merge" ]; then
	preflight_common
	preflight_workmux
	if [ -n "$ONLY_WAVE" ]; then
		head_ "Merge — $ONLY_WAVE"
		merge_waves "$ONLY_WAVE" || die "병합 실패"
	elif [ -n "$ONLY_STAGE" ]; then
		read_lines < <(waves_query stage-waves "$ONLY_STAGE")
		stage_waves=(${LINES[@]+"${LINES[@]}"})
		[ "${#stage_waves[@]}" -gt 0 ] || die "스테이지 $ONLY_STAGE 를 찾지 못했습니다"
		head_ "Merge — Stage $ONLY_STAGE"
		merge_waves "${stage_waves[@]}" || die "일부 병합 실패"
	else
		die "merge 는 --wave NAME 또는 --stage N 이 필요합니다"
	fi
	ok "병합 완료"
	exit 0
fi

# ──────────────────────────────────────────────
# Phase 1 — spec
# ──────────────────────────────────────────────
if [ "$CMD" = "spec" ]; then
	preflight_common
	read_lines < <(waves_query all-features)
	ALL_FEATURES=(${LINES[@]+"${LINES[@]}"})
	[ "${#ALL_FEATURES[@]}" -gt 0 ] || die "waves.json 에 features 가 없습니다"

	head_ "Phase 1 (spec) — 01_specify + 02_clarify"
	log "코드베이스를 읽지 않는 단계라 worktree 없이 한 워킹트리에서 전부 동시에 돌립니다"

	spec_ok=true
	run_spec_phase "${ALL_FEATURES[@]}" || spec_ok=false

	if $DRY_RUN; then
		exit 0
	fi

	head_ "Spec 게이트 — spec.md 존재 + [NEEDS CLARIFICATION] 잔존 0건"
	gate_ok=true
	if [ -x "$PROJECT_DIR/utilities/wm_pre_merge_gate.sh" ]; then
		bash "$PROJECT_DIR/utilities/wm_pre_merge_gate.sh" --phase spec \
			--features "$(printf '%s ' "${ALL_FEATURES[@]}")" || gate_ok=false
	else
		warn "utilities/wm_pre_merge_gate.sh 가 없어 게이트를 건너뜁니다"
	fi

	if $NO_COMMIT; then
		warn "--no-commit — 커밋 생략. specs/ 를 검토한 뒤 직접 커밋하세요."
	else
		head_ "specs/ 커밋 (단일 커밋 — 병렬 프로세스는 git 을 만지지 않았습니다)"
		git add -A -- specs
		if git diff --cached --quiet; then
			warn "커밋할 spec 변경이 없습니다"
		else
			git commit -q -m "$(printf 'feat(specs): speckit specify+clarify for %d features\n\nGenerated by speckit_parallel.sh (Phase 1, background parallel)\n\nCo-Authored-By: Claude <noreply@anthropic.com>' "${#ALL_FEATURES[@]}")"
			ok "커밋 완료"
		fi
	fi

	if $spec_ok && $gate_ok; then
		ok "Phase 1 완료 — 모든 feature 의 spec.md 가 main 에 있습니다"
		log "다음: $0 build"
		exit 0
	fi
	die "Phase 1 미완 — 실패한 feature 를 고친 뒤 재실행하세요:
    ./utilities/speckit_pipeline.sh $PROMPTS_DIR --phase spec --only NNN"
fi

# ──────────────────────────────────────────────
# Phase 2 — build (스테이지 순차, 스테이지 안의 웨이브는 병렬)
# ──────────────────────────────────────────────
if [ "$CMD" = "build" ]; then
	preflight_common
	preflight_workmux
	resolve_stages

	# 웨이브 하나만 실행
	if [ -n "$ONLY_WAVE" ]; then
		stage_idx="$(waves_query stage-of-wave "$ONLY_WAVE")"
		head_ "Phase 2 / $ONLY_WAVE (stage $stage_idx) — 03_plan ~ 08_converge"
		run_stage "$stage_idx" "$ONLY_WAVE"
		if $NO_MERGE; then
			warn "--no-merge — '$0 merge --wave $ONLY_WAVE' 로 병합하세요."
			exit 0
		fi
		merge_waves "$ONLY_WAVE" || die "'$ONLY_WAVE' 병합 실패"
		ok "'$ONLY_WAVE' 완료"
		exit 0
	fi

	for stage in "${STAGES[@]}"; do
		read_lines < <(waves_query stage-waves "$stage")
		stage_waves=(${LINES[@]+"${LINES[@]}"})
		[ "${#stage_waves[@]}" -gt 0 ] || { warn "스테이지 $stage 가 비어 있습니다 — 건너뜁니다"; continue; }
		stage_kind="$(waves_query stage-kind "$stage")"

		if [ "$stage_kind" = "trunk" ]; then
			head_ "Stage $stage — trunk (순차 체인, 끝나면 main 에 자동 병합)"
		else
			head_ "Stage $stage — branch (${#stage_waves[@]}개 웨이브 병렬)"
		fi
		run_stage "$stage" "${stage_waves[@]}"

		if $NO_MERGE; then
			warn "--no-merge — 스테이지 $stage 병합 생략. '$0 merge --stage $stage' 로 병합하세요."
			continue
		fi

		log "스테이지 병합 배리어 — 다음 스테이지의 plan 이 이 결과물을 실제 코드로 보게 합니다"
		merge_waves "${stage_waves[@]}" \
			|| die "스테이지 $stage 병합 실패 — 중단. 수정 후 '$0 build --from-stage $stage' 재시도"
		ok "스테이지 $stage 완료"
	done

	echo ""
	ok "Phase 2 완료"
	workmux list || true
	exit 0
fi

die "알 수 없는 명령: $CMD (waves | spec | build | merge)"
