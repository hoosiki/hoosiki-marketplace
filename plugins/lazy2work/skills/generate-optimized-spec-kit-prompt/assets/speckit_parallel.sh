#!/usr/bin/env bash
# speckit_parallel.sh — workmux 기반 SpecKit 2-Phase 병렬 드라이버
#
#   Phase 1 (spec) : 전 feature 병렬 → 01_specify + 02_clarify + commit → 순차 merge
#   Phase 2 (build): 웨이브별 병렬  → 03_plan ~ 08_converge + commit    → 웨이브마다 순차 merge
#
# 병렬 안전 경계선은 /speckit.plan 이다 — plan만이 코드베이스를 읽는다.
# 따라서 specify·clarify는 전부 동시에 돌려도 되지만, plan 이후는 의존성 웨이브 단위로만 묶는다.
#
# Usage:
#   ./utilities/speckit_parallel.sh waves                     # 웨이브 목록 출력
#   ./utilities/speckit_parallel.sh spec [--dry-run]          # Phase 1 — 전 feature 병렬
#   ./utilities/speckit_parallel.sh build [--dry-run]         # Phase 2 — 전 웨이브 순차 진행
#   ./utilities/speckit_parallel.sh build --wave w1-core-domain
#   ./utilities/speckit_parallel.sh build --from-wave w2-channels   # 해당 웨이브부터 끝까지
#   ./utilities/speckit_parallel.sh merge spec                # 병렬 실행 후 병합만 다시 시도
#   ./utilities/speckit_parallel.sh merge build --wave w1-core-domain
#
# Options:
#   --prompts <path>   .speckit-prompts/<project> 경로 (기본: 자동 탐지 / SPECKIT_PROMPTS_DIR)
#   --wave <name>      해당 웨이브만
#   --from-wave <name> 해당 웨이브부터 끝까지
#   --max-concurrent N 동시 worktree 수 (기본: 4, env MAX_CONCURRENT)
#   --base <branch>    분기 기준 브랜치 (기본: .workmux.yaml의 base_branch / main)
#   --no-merge         병렬 실행만 하고 병합은 생략
#   --dry-run          workmux --dry-run 으로 계획만 출력
#
# 브랜치 이름이 단계 전달 채널이다 (tmux pane은 드라이버 env를 상속하지 않는다):
#   spec/NNN-<slug>                  → Phase 1
#   build/<wave-name>/NNN-<slug>     → Phase 2
#
# ⚠️ 사전 준비 (한 번):
#   git rm --cached .specify/feature.json && echo '.specify/feature.json' >> .gitignore
#   echo '.speckit-logs/' >> .gitignore
#   .workmux.yaml 에 layouts.speckit (단일 pane) + base_branch 명시
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

MERGE_PHASE=""
if [ "$CMD" = "merge" ]; then
	MERGE_PHASE="${1:-}"
	[ -n "$MERGE_PHASE" ] || die "merge 는 phase 가 필요합니다: $0 merge <spec|build> [--wave NAME]"
	shift
fi

PROMPTS_DIR="${SPECKIT_PROMPTS_DIR:-}"
ONLY_WAVE=""
FROM_WAVE=""
MAX_CONCURRENT="${MAX_CONCURRENT:-4}"
BASE_BRANCH=""
NO_MERGE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
	case "$1" in
	--prompts) PROMPTS_DIR="$2"; shift 2 ;;
	--wave) ONLY_WAVE="$2"; shift 2 ;;
	--from-wave) FROM_WAVE="$2"; shift 2 ;;
	--max-concurrent) MAX_CONCURRENT="$2"; shift 2 ;;
	--base) BASE_BRANCH="$2"; shift 2 ;;
	--no-merge) NO_MERGE=true; shift ;;
	--dry-run) DRY_RUN=true; shift ;;
	-h | --help) sed -n '2,40p' "$0"; exit 0 ;;
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

# waves.json 조회 헬퍼
waves_query() { python3 - "$WAVES_FILE" "$@" <<-'PYEOF'
	import json, sys
	path, mode = sys.argv[1], sys.argv[2]
	with open(path, encoding="utf-8") as fh:
	    data = json.load(fh)
	waves = data.get("waves", [])
	if mode == "names":
	    print("\n".join(w["name"] for w in waves))
	elif mode == "table":
	    for i, w in enumerate(waves):
	        feats = w.get("features", [])
	        print(f'{i}\t{w["name"]}\t{w.get("title", "")}\t{len(feats)}\t{" ".join(feats)}')
	elif mode == "features":
	    target = sys.argv[3]
	    for w in waves:
	        if w["name"] == target:
	            print("\n".join(w.get("features", [])))
	            break
	    else:
	        sys.exit(3)
	elif mode == "all-features":
	    print("\n".join(f["id"] for f in data.get("features", [])))
	elif mode == "project":
	    print(data.get("project", ""))
PYEOF
}

PROJECT_NAME="$(waves_query project)"
read_lines < <(waves_query names)
ALL_WAVES=(${LINES[@]+"${LINES[@]}"})
[ "${#ALL_WAVES[@]}" -gt 0 ] || die "waves.json 에 웨이브가 정의되어 있지 않습니다"

RUN_ROOT="$PROJECT_DIR/.speckit-logs/parallel"

# ──────────────────────────────────────────────
# waves 명령
# ──────────────────────────────────────────────
if [ "$CMD" = "waves" ]; then
	head_ "Waves — $PROJECT_NAME"
	waves_query table | while IFS=$'\t' read -r idx name title count feats; do
		echo -e "  ${BOLD}${name}${NC}  (${count})  ${title}"
		for f in $feats; do echo "      - $f"; done
	done
	echo ""
	log "프롬프트: $PROMPTS_DIR"
	exit 0
fi

# ──────────────────────────────────────────────
# Preflight
# ──────────────────────────────────────────────
preflight() {
	command -v workmux >/dev/null 2>&1 || die "workmux 가 필요합니다: brew install raine/workmux/workmux"
	command -v tmux >/dev/null 2>&1 || die "tmux 가 필요합니다"

	[ -f "$PROJECT_DIR/.workmux.yaml" ] || die ".workmux.yaml 이 없습니다 (프로젝트 루트에 필요)"
	grep -qE '^[[:space:]]*speckit:' "$PROJECT_DIR/.workmux.yaml" \
		|| die ".workmux.yaml 에 layouts.speckit (단일 pane) 레이아웃이 없습니다"

	[ -x "$PROJECT_DIR/utilities/wm_stage_runner.sh" ] \
		|| die "utilities/wm_stage_runner.sh 가 없거나 실행 권한이 없습니다 (chmod +x)"

	if git ls-files --error-unmatch .specify/feature.json >/dev/null 2>&1; then
		die ".specify/feature.json 이 git 에 추적 중입니다 — worktree 마다 덮어써서 병합이 전부 충돌합니다.
    git rm --cached .specify/feature.json && echo '.specify/feature.json' >> .gitignore"
	fi

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
# 한 그룹(전 feature 또는 한 웨이브)을 병렬 실행
# ──────────────────────────────────────────────
run_group() {
	local phase="$1" wave="$2"
	shift 2
	local -a feats=("$@")
	local branch_prefix run_dir matrix

	if [ "$phase" = "spec" ]; then
		branch_prefix="spec"
		run_dir="$RUN_ROOT/spec"
	else
		branch_prefix="build/$wave"
		run_dir="$RUN_ROOT/build/$wave"
	fi

	mkdir -p "$run_dir"
	rm -f "$run_dir"/*.status

	matrix="feature:$(IFS=,; echo "${feats[*]}")"

	log "${#feats[@]}개 병렬 실행 (max-concurrent=$MAX_CONCURRENT, base=$BASE_BRANCH)"
	printf '   %s\n' "${feats[@]}"

	local -a extra=()
	# spec 단계는 소스 코드를 건드리지 않는다 → 의존성 설치·파일 복사가 불필요
	[ "$phase" = "spec" ] && extra+=(--no-hooks --no-file-ops)
	$DRY_RUN && extra+=(--dry-run)

	workmux add "$branch_prefix" \
		--foreach "$matrix" \
		--branch-template "$branch_prefix/{{ feature }}" \
		--base "$BASE_BRANCH" \
		--layout speckit \
		--background \
		--wait \
		--max-concurrent "$MAX_CONCURRENT" \
		${extra[@]+"${extra[@]}"}
}

# ──────────────────────────────────────────────
# 성공한 것만 순차 병합 (동시 병합 금지 — main의 index가 레이스한다)
# ──────────────────────────────────────────────
merge_group() {
	local phase="$1" wave="$2"
	shift 2
	local -a feats=("$@")
	local branch_prefix run_dir
	local -a good=() bad=()

	if [ "$phase" = "spec" ]; then
		branch_prefix="spec"
		run_dir="$RUN_ROOT/spec"
	else
		branch_prefix="build/$wave"
		run_dir="$RUN_ROOT/build/$wave"
	fi

	for f in "${feats[@]}"; do
		# dry-run 은 상태 파일을 만들지 않는다 — 병합 계획만 보여준다
		if $DRY_RUN || [ "$(cat "$run_dir/$f.status" 2>/dev/null || true)" = "OK" ]; then
			good+=("$f")
		else
			bad+=("$f")
		fi
	done

	if [ "${#bad[@]}" -gt 0 ]; then
		warn "실행 실패 (병합 제외): ${bad[*]}"
		warn "  로그: $run_dir/"
	fi

	for f in ${good[@]+"${good[@]}"}; do
		log "merge ${branch_prefix}/$f"
		if $DRY_RUN; then
			echo "  [DRY-RUN] workmux merge ${branch_prefix}/$f --rebase"
			continue
		fi
		if ! workmux merge "${branch_prefix}/$f" --rebase; then
			warn "[$f] 병합 실패 (rebase 충돌 또는 pre_merge 게이트) — worktree 보존"
			bad+=("$f")
		fi
	done

	[ "${#bad[@]}" -eq 0 ]
}

# ──────────────────────────────────────────────
# merge 전용 명령
# ──────────────────────────────────────────────
if [ "$CMD" = "merge" ]; then
	preflight
	if [ "$MERGE_PHASE" = "spec" ]; then
		read_lines < <(waves_query all-features)
		feats=(${LINES[@]+"${LINES[@]}"})
		head_ "Merge — Phase 1 (spec)"
		merge_group spec "" "${feats[@]}" || die "일부 병합 실패"
	else
		[ -n "$ONLY_WAVE" ] || die "merge build 는 --wave NAME 이 필요합니다"
		read_lines < <(waves_query features "$ONLY_WAVE")
		feats=(${LINES[@]+"${LINES[@]}"})
		[ "${#feats[@]}" -gt 0 ] || die "웨이브가 없거나 비어 있습니다: $ONLY_WAVE"
		head_ "Merge — Phase 2 / $ONLY_WAVE"
		merge_group build "$ONLY_WAVE" "${feats[@]}" || die "일부 병합 실패"
	fi
	ok "병합 완료"
	exit 0
fi

# ──────────────────────────────────────────────
# Phase 1 — spec (전 feature 병렬)
# ──────────────────────────────────────────────
if [ "$CMD" = "spec" ]; then
	preflight
	read_lines < <(waves_query all-features)
	ALL_FEATURES=(${LINES[@]+"${LINES[@]}"})
	[ "${#ALL_FEATURES[@]}" -gt 0 ] || die "waves.json 에 features 가 없습니다"

	head_ "Phase 1 (spec) — 01_specify + 02_clarify + commit"
	log "코드베이스 의존이 없으므로 ${#ALL_FEATURES[@]}개 feature 를 전부 병렬로 돌립니다"
	run_group spec "" "${ALL_FEATURES[@]}"

	if $NO_MERGE; then
		warn "--no-merge — 병합 생략. 확인 후 '$0 merge spec' 으로 병합하세요."
		exit 0
	fi

	head_ "Phase 1 병합 배리어 — 형제 spec.md 를 main 에 모읍니다"
	merge_group spec "" "${ALL_FEATURES[@]}" || die "Phase 1 병합 실패 — 수정 후 '$0 merge spec' 재시도"
	ok "Phase 1 완료 — 이제 모든 feature 의 spec.md 가 main 에 있습니다"
	workmux list || true
	exit 0
fi

# ──────────────────────────────────────────────
# Phase 2 — build (웨이브별 병렬 + 웨이브마다 병합 배리어)
# ──────────────────────────────────────────────
if [ "$CMD" = "build" ]; then
	preflight

	local_waves=()
	if [ -n "$ONLY_WAVE" ]; then
		local_waves=("$ONLY_WAVE")
	elif [ -n "$FROM_WAVE" ]; then
		started=false
		for w in "${ALL_WAVES[@]}"; do
			[ "$w" = "$FROM_WAVE" ] && started=true
			$started && local_waves+=("$w")
		done
		[ "${#local_waves[@]}" -gt 0 ] || die "웨이브를 찾지 못했습니다: $FROM_WAVE"
	else
		local_waves=("${ALL_WAVES[@]}")
	fi

	for wave in "${local_waves[@]}"; do
		read_lines < <(waves_query features "$wave")
		feats=(${LINES[@]+"${LINES[@]}"})
		[ "${#feats[@]}" -gt 0 ] || { warn "웨이브 '$wave' 에 feature 가 없습니다 — 건너뜁니다"; continue; }

		head_ "Phase 2 / $wave — 03_plan ~ 08_converge + commit"
		run_group build "$wave" "${feats[@]}"

		if $NO_MERGE; then
			warn "--no-merge — '$wave' 병합 생략. '$0 merge build --wave $wave' 로 병합하세요."
			continue
		fi

		log "웨이브 병합 배리어 — 다음 웨이브의 plan 이 이 결과물을 볼 수 있게 합니다"
		merge_group build "$wave" "${feats[@]}" || die "웨이브 '$wave' 병합 실패 — 중단. 수정 후 '$0 build --from-wave $wave' 재시도"
		ok "웨이브 '$wave' 완료"
	done

	echo ""
	ok "Phase 2 완료"
	workmux list || true
	exit 0
fi

die "알 수 없는 명령: $CMD (waves | spec | build | merge)"
