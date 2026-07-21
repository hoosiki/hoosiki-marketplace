#!/bin/bash
# speckit_pipeline.sh — SpecKit 8-Stage Pipeline Automation (Headless Mode)
#
# Usage:
#   ./utilities/speckit_pipeline.sh <PROMPTS_PATH>                 # <PROMPTS_PATH> 아래 전체 feature 순차 실행
#   ./utilities/speckit_pipeline.sh <PROMPTS_PATH> --from 003      # 003 feature부터 실행 (해당 feature 포함, 이후 전부)
#   ./utilities/speckit_pipeline.sh <PROMPTS_PATH> --from 003/06   # 003 feature의 06_analyze 단계부터 실행
#   ./utilities/speckit_pipeline.sh <PROMPTS_PATH> --only 002      # 002 feature만 실행
#   ./utilities/speckit_pipeline.sh <PROMPTS_PATH> --step 07       # 07_implement 단계만 실행
#   ./utilities/speckit_pipeline.sh <PROMPTS_PATH> --dry-run       # 실행 없이 계획만 출력
#   ./utilities/speckit_pipeline.sh <PROMPTS_PATH> --no-commit     # converge 후 커밋 생략
#   ./utilities/speckit_pipeline.sh <PROMPTS_PATH> --skip-clarify  # 02_clarify 단계 건너뛰기
#   ./utilities/speckit_pipeline.sh <PROMPTS_PATH> --resume        # 마지막 실패/중단 지점부터 재개
#
#   <PROMPTS_PATH>: 'NNN-<slug>' 형식의 feature 폴더들을 직접 담고 있는 (절대) 경로.
#                   예) /abs/path/to/.speckit-prompts/japanese-tutor
#                   생략 시 기본값은 <project>/.speckit-prompts.
#   --from 값: feature 번호(3, 03, 003 모두 동일하게 인식) 또는 'NNN/SS' (SS = 단계 번호, 예 003/06).
#   단계별 모델·effort (토큰 최적화 — 추론군=Opus+고effort, 실행군=Sonnet):
#     specify/clarify/checklist=opus-4-8/high · plan/analyze/converge=opus-4-8/xhigh · tasks/implement=sonnet-5/xhigh · commit=기본값.
#     env로 override: SPECIFY_MODEL/SPECIFY_EFFORT, CLARIFY_*, PLAN_*, CHECKLIST_*, TASKS_*, ANALYZE_*, IMPLEMENT_*, CONVERGE_* (예: PLAN_EFFORT=max ...).
#     ⚠️ xhigh는 Opus 4.7/4.8·Fable5·Mythos5만 정식 지원 — Sonnet 5+xhigh는 high로 폴백될 수 있음.
#
# Feature 폴더 구조 (각 feature 아래 8개 단계 파일 + commit):
#   NNN-<slug>/{01_specify,02_clarify,03_plan,04_checklist,05_tasks,06_analyze,07_implement,08_converge,09_commit}.md
#
# 8-Stage Pipeline:
#   01_specify → 02_clarify → 03_plan → 04_checklist → 05_tasks → 06_analyze → 07_implement → 08_converge → commit(git)
#
# 주의: claude -p는 슬래시 명령(/speckit.implement 등)을 지원하지 않으므로,
# 프롬프트 파일 내용을 직접 지시사항으로 전달합니다.
#
# 권한: 모든 claude -p 호출은 --permission-mode bypassPermissions + --dangerously-skip-permissions로
# 무인 실행된다(권한 확인·다이얼로그 생략). ⚠️ root/sudo로는 거부되며, 격리 환경(컨테이너/VM/dev container)
# 에서 실행할 것 — bypassPermissions는 프롬프트 인젝션·오작동에 대한 보호가 없다.
set -euo pipefail

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEFAULT_PROMPTS_DIR="$PROJECT_DIR/.speckit-prompts"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG_DIR="$PROJECT_DIR/.speckit-logs/$TIMESTAMP"
RESUME_FILE="$PROJECT_DIR/.speckit-logs/.last_checkpoint"
STEPS=("01_specify" "02_clarify" "03_plan" "04_checklist" "05_tasks" "06_analyze" "07_implement" "08_converge")
MAX_TURNS=1000
CLAUDE_BIN="${CLAUDE_BIN:-claude}"
# 단계별 모델·effort (토큰 최적화: 추론군=Opus+고effort·소출력 / 실행군=Sonnet·대출력).
# 근거: 추론군(specify/clarify/plan/checklist/analyze/converge)은 Opus+높은 effort로 설계·검증 품질을 확보하고,
#       실행군(tasks/implement)은 Sonnet+큰 출력으로 토큰/속도를 최적화한다.
#       converge는 gap 검증+재구현 판단이 품질에 직결되므로 Opus로 둔다.
# ⚠️ xhigh는 Opus 4.7/4.8·Fable5·Mythos5만 정식 지원 — Sonnet 5+xhigh는 high로 폴백될 수 있음.
# 각 값은 env로 override 가능. commit(do_git_commit)은 기본값 유지.
SPECIFY_MODEL="${SPECIFY_MODEL:-claude-opus-4-8}"
SPECIFY_EFFORT="${SPECIFY_EFFORT:-high}"
CLARIFY_MODEL="${CLARIFY_MODEL:-claude-opus-4-8}"
CLARIFY_EFFORT="${CLARIFY_EFFORT:-high}"
PLAN_MODEL="${PLAN_MODEL:-claude-opus-4-8}"
PLAN_EFFORT="${PLAN_EFFORT:-xhigh}"
CHECKLIST_MODEL="${CHECKLIST_MODEL:-claude-opus-4-8}"
CHECKLIST_EFFORT="${CHECKLIST_EFFORT:-high}"
TASKS_MODEL="${TASKS_MODEL:-claude-sonnet-5}"
TASKS_EFFORT="${TASKS_EFFORT:-xhigh}"
ANALYZE_MODEL="${ANALYZE_MODEL:-claude-opus-4-8}"
ANALYZE_EFFORT="${ANALYZE_EFFORT:-xhigh}"
IMPLEMENT_MODEL="${IMPLEMENT_MODEL:-claude-sonnet-5}"
IMPLEMENT_EFFORT="${IMPLEMENT_EFFORT:-xhigh}"
CONVERGE_MODEL="${CONVERGE_MODEL:-claude-opus-4-8}"
CONVERGE_EFFORT="${CONVERGE_EFFORT:-xhigh}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ──────────────────────────────────────────────
# Parse Arguments
# ──────────────────────────────────────────────
PROMPTS_INPUT=""
FROM_FEATURE=""
FROM_STEP=""
ONLY_FEATURE=""
ONLY_STEP=""
DRY_RUN=false
NO_COMMIT=false
SKIP_CLARIFY=false
RESUME=false

while [[ $# -gt 0 ]]; do
	case $1 in
	--from)
		if [[ "$2" == */* ]]; then
			FROM_FEATURE="${2%%/*}"
			FROM_STEP="${2##*/}"
		else
			FROM_FEATURE="$2"
			FROM_STEP=""
		fi
		shift 2
		;;
	--only)
		ONLY_FEATURE="$2"
		shift 2
		;;
	--step)
		ONLY_STEP="$2"
		shift 2
		;;
	--dry-run)
		DRY_RUN=true
		shift
		;;
	--no-commit)
		NO_COMMIT=true
		shift
		;;
	--skip-clarify)
		SKIP_CLARIFY=true
		shift
		;;
	--resume)
		RESUME=true
		shift
		;;
	--max-turns)
		MAX_TURNS="$2"
		shift 2
		;;
	-h | --help)
		cat <<-'HELPEOF'
			Usage: speckit_pipeline.sh <PROMPTS_PATH> [OPTIONS]

			Positional:
			  <PROMPTS_PATH>   'NNN-<slug>' feature 폴더들을 직접 담고 있는 (절대) 경로.
			                   예) /abs/path/to/.speckit-prompts/japanese-tutor
			                   생략 시 기본값 <project>/.speckit-prompts

			Options:
			  --from NNN       NNN feature부터 실행 (해당 feature 포함, 이후 전부). 3/03/003 동일 인식.
			  --from NNN/SS    NNN feature의 SS 단계부터 실행 (예: 003/06)
			  --only NNN       NNN feature만 실행
			  --step NN        NN 단계만 실행 (01~08)
			  --dry-run        실행 없이 계획만 출력
			  --no-commit      converge 후 커밋 생략
			  --skip-clarify   02_clarify 건너뛰기
			  --resume         마지막 실패/중단 지점부터 재개
			  --max-turns N    Claude 최대 턴 수 (기본: 1000)
			  (env) 단계별 모델/effort override: SPECIFY_MODEL/SPECIFY_EFFORT, CLARIFY_*, PLAN_*, CHECKLIST_*, TASKS_*, ANALYZE_*, IMPLEMENT_*, CONVERGE_*
			        기본: specify·clarify·checklist=opus-4-8/high, plan·analyze·converge=opus-4-8/xhigh, tasks·implement=sonnet-5/xhigh
			        ⚠️ xhigh는 Opus 4.7/4.8 계열만 정식 지원 — Sonnet 5+xhigh는 high로 폴백 가능

			Feature 폴더: NNN-<slug>/{01_specify..09_commit}.md
			Pipeline: 01_specify → 02_clarify → 03_plan → 04_checklist → 05_tasks → 06_analyze → 07_implement → 08_converge → commit

			Examples:
			  ./utilities/speckit_pipeline.sh /abs/.speckit-prompts/japanese-tutor
			  ./utilities/speckit_pipeline.sh /abs/.speckit-prompts/japanese-tutor --only 000
			  ./utilities/speckit_pipeline.sh /abs/.speckit-prompts/japanese-tutor --from 004 --skip-clarify
			  ./utilities/speckit_pipeline.sh /abs/.speckit-prompts/japanese-tutor --from 002/06
			  ./utilities/speckit_pipeline.sh /abs/.speckit-prompts/japanese-tutor --resume
			  ./utilities/speckit_pipeline.sh /abs/.speckit-prompts/japanese-tutor --dry-run
		HELPEOF
		exit 0
		;;
	-*)
		echo "Unknown option: $1"
		exit 1
		;;
	*)
		if [ -n "$PROMPTS_INPUT" ]; then
			echo "Unexpected extra argument: '$1' (PROMPTS_PATH already set to '$PROMPTS_INPUT')"
			exit 1
		fi
		PROMPTS_INPUT="$1"
		shift
		;;
	esac
done

# --from 의 단계 부분 정규화 (06 또는 06_analyze 모두 허용 → 06)
[ -n "$FROM_STEP" ] && FROM_STEP="${FROM_STEP%%_*}"

# Prompts 디렉터리 확정: 위치 인자(절대경로) 우선, 없으면 기본값
if [ -n "$PROMPTS_INPUT" ]; then
	PROMPTS_DIR="$(cd "$PROMPTS_INPUT" 2>/dev/null && pwd)" || {
		echo "Prompts path not found or not a directory: $PROMPTS_INPUT"
		exit 1
	}
else
	PROMPTS_DIR="$DEFAULT_PROMPTS_DIR"
fi

# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_step() { echo -e "${CYAN}  -> $1${NC}"; }
log_ok() { echo -e "${GREEN}  [OK]${NC} $1"; }
log_fail() { echo -e "${RED}  [FAIL]${NC} $1"; }
log_warn() { echo -e "${YELLOW}  [WARN]${NC} $1"; }
log_header() {
	echo ""
	echo -e "${BLUE}=======================================${NC}"
	echo -e "${BOLD}${BLUE}  $1${NC}"
	echo -e "${BLUE}=======================================${NC}"
}

# Feature 폴더 이름은 'NNN-<slug>' (레거시 'feature-NNN-<slug>'도 허용)
extract_feature_num() {
	basename "$1" | sed -E 's/^feature-//' | grep -oE '^[0-9]+' || true
}

extract_feature_short_name() {
	basename "$1" | sed -E 's/^(feature-)?[0-9]+-//'
}

# 두 feature 식별자를 숫자로 비교 (003 == 3 == '003-slug'의 접두 숫자)
feature_num_eq() {
	local a b
	a=$(echo "$1" | sed -E 's/^feature-//' | grep -oE '^[0-9]+' || true)
	b=$(echo "$2" | sed -E 's/^feature-//' | grep -oE '^[0-9]+' || true)
	[ -n "$a" ] && [ -n "$b" ] && [ "$((10#$a))" -eq "$((10#$b))" ]
}

# 두 단계 번호를 숫자로 비교 (04 == 4)
step_num_eq() {
	[ -n "$1" ] && [ -n "$2" ] && [ "$((10#$1))" -eq "$((10#$2))" ]
}

save_checkpoint() {
	local feature_num="$1"
	local step="$2"
	mkdir -p "$(dirname "$RESUME_FILE")"
	echo "${feature_num}/${step}" >"$RESUME_FILE"
}

load_checkpoint() {
	if [ -f "$RESUME_FILE" ]; then
		cat "$RESUME_FILE"
	else
		echo ""
	fi
}

# ──────────────────────────────────────────────
# Resume handling
# ──────────────────────────────────────────────
if $RESUME; then
	checkpoint=$(load_checkpoint)
	if [ -z "$checkpoint" ]; then
		log_warn "No checkpoint found. Running from beginning."
	else
		log_info "Resuming from checkpoint: $checkpoint"
		FROM_FEATURE="${checkpoint%%/*}"
		FROM_STEP="${checkpoint##*/}"
	fi
fi

# ──────────────────────────────────────────────
# Claude Headless Execution
# ──────────────────────────────────────────────
run_claude_headless() {
	local prompt_content="$1"
	local log_file="$2"
	local step_name="$3"
	local max_turns_override="${4:-$MAX_TURNS}"
	local model_override="${5:-}"
	local effort_override="${6:-}"

	if $DRY_RUN; then
		echo "  [DRY-RUN] Would execute: claude -p ${model_override:+--model $model_override }${effort_override:+--effort $effort_override }'${prompt_content:0:80}...'"
		echo "  [DRY-RUN] Log: $log_file"
		return 0
	fi

	cd "$PROJECT_DIR"

	local constitution_ref=""
	if [ -f ".specify/memory/constitution.md" ]; then
		constitution_ref="Read .specify/memory/constitution.md for project principles and prohibitions."
	fi

	local claude_md_ref=""
	if [ -f "CLAUDE.md" ]; then
		claude_md_ref="Read CLAUDE.md first for project conventions."
	fi

	local processed_prompt
	processed_prompt="You are working on the project in the current directory.
${claude_md_ref}
${constitution_ref}

The following is your task. Execute it step by step:

---
${prompt_content}
---

IMPORTANT:
- Follow the instructions above precisely.
- Use 'uv run' for all Python commands (pytest, mypy, ruff, etc.).
- Run verification commands as specified.
- Stop and report on any test failure.
- Do NOT ask for confirmation — execute autonomously.
- Always respond in Korean."

	# bypassPermissions: 모든 권한 확인을 생략(헤드리스 무인 실행). --permission-mode로 모드를 명시하고,
	# --dangerously-skip-permissions로 최초 1회 책임수용 다이얼로그까지 건너뛴다(둘은 동등하나 함께 두어 의도를 명확히 함).
	"$CLAUDE_BIN" -p "$processed_prompt" \
		${model_override:+--model "$model_override"} \
		${effort_override:+--effort "$effort_override"} \
		--max-turns "$max_turns_override" \
		--output-format text \
		--permission-mode bypassPermissions \
		--dangerously-skip-permissions \
		2>&1 | tee "$log_file"

	local exit_code=${PIPESTATUS[0]}

	if [ $exit_code -ne 0 ]; then
		log_fail "$step_name (exit code: $exit_code)"
		log_warn "Log: $log_file"
		return $exit_code
	fi

	return 0
}

# ──────────────────────────────────────────────
# Git Commit
# ──────────────────────────────────────────────
do_git_commit() {
	local feature_name="$1"
	local feature_short="$2"
	local log_file="$3"

	if $NO_COMMIT; then
		log_warn "Commit skipped (--no-commit)"
		return 0
	fi

	if $DRY_RUN; then
		echo "  [DRY-RUN] Would commit: feat($feature_short): implement feature"
		return 0
	fi

	cd "$PROJECT_DIR"

	if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
		log_warn "No changes to commit"
		return 0
	fi

	local commit_prompt="You are in a git repository. Create a commit for the work just completed.

Steps:
1. Run 'git status' to see changes
2. Run 'git diff --stat' to understand what changed
3. Stage all relevant files (avoid .env, credentials, large binaries, .speckit-logs/, experiments/)
4. Create a commit with conventional commit format:
   feat($feature_short): implement $feature_name

   Include a brief body describing the key changes (2-3 bullet points).
   End with: Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
5. Do NOT push to remote

Execute these steps now."

	log_step "Committing changes..."

	"$CLAUDE_BIN" -p "$commit_prompt" \
		--max-turns 10 \
		--output-format text \
		--permission-mode bypassPermissions \
		--dangerously-skip-permissions \
		2>&1 | tee "$log_file"

	local exit_code=${PIPESTATUS[0]}

	if [ $exit_code -ne 0 ]; then
		log_warn "Auto-commit may have failed, attempting fallback..."
		git add -A -- ':!.speckit-logs' ':!.env' ':!*.mmdb' ':!experiments/'
		git commit -m "$(
			cat <<EOF
feat($feature_short): implement $feature_name

Automated commit via speckit_pipeline.sh

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
		)" || log_warn "Nothing to commit (fallback)"
	fi

	log_ok "Committed"
	return 0
}

# ──────────────────────────────────────────────
# Step-specific max turns
# ──────────────────────────────────────────────
get_max_turns_for_step() {
	local step="$1"
	case "$step" in
	01_specify) echo 30 ;;
	02_clarify) echo 50 ;;
	03_plan) echo "$MAX_TURNS" ;;
	04_checklist) echo 50 ;;
	05_tasks) echo "$MAX_TURNS" ;;
	06_analyze) echo 50 ;;
	07_implement) echo "$MAX_TURNS" ;;
	08_converge) echo "$MAX_TURNS" ;;
	*) echo "$MAX_TURNS" ;;
	esac
}

# 단계별 모델 (빈 문자열 = Claude 기본값 상속). commit은 기본값.
get_model_for_step() {
	local step="$1"
	case "$step" in
	01_specify) echo "$SPECIFY_MODEL" ;;
	02_clarify) echo "$CLARIFY_MODEL" ;;
	03_plan) echo "$PLAN_MODEL" ;;
	04_checklist) echo "$CHECKLIST_MODEL" ;;
	05_tasks) echo "$TASKS_MODEL" ;;
	06_analyze) echo "$ANALYZE_MODEL" ;;
	07_implement) echo "$IMPLEMENT_MODEL" ;;
	08_converge) echo "$CONVERGE_MODEL" ;;
	*) echo "" ;;
	esac
}

# 단계별 effort (빈 문자열 = 세션 기본값 상속). commit은 기본값.
get_effort_for_step() {
	local step="$1"
	case "$step" in
	01_specify) echo "$SPECIFY_EFFORT" ;;
	02_clarify) echo "$CLARIFY_EFFORT" ;;
	03_plan) echo "$PLAN_EFFORT" ;;
	04_checklist) echo "$CHECKLIST_EFFORT" ;;
	05_tasks) echo "$TASKS_EFFORT" ;;
	06_analyze) echo "$ANALYZE_EFFORT" ;;
	07_implement) echo "$IMPLEMENT_EFFORT" ;;
	08_converge) echo "$CONVERGE_EFFORT" ;;
	*) echo "" ;;
	esac
}

# ──────────────────────────────────────────────
# Main Execution
# ──────────────────────────────────────────────
log_header "SpecKit 8-Stage Pipeline"
log_info "Project:   $PROJECT_DIR"
log_info "Prompts:   $PROMPTS_DIR"
log_info "Logs:      $LOG_DIR"
log_info "Claude:    $($CLAUDE_BIN --version 2>/dev/null || echo 'unknown')"
log_info "Max Turns: $MAX_TURNS (plan/tasks/implement/converge), others vary per step"
log_info "Per-step model/effort (토큰 최적화):"
log_info "  specify=$SPECIFY_MODEL/$SPECIFY_EFFORT  clarify=$CLARIFY_MODEL/$CLARIFY_EFFORT  plan=$PLAN_MODEL/$PLAN_EFFORT  checklist=$CHECKLIST_MODEL/$CHECKLIST_EFFORT"
log_info "  tasks=$TASKS_MODEL/$TASKS_EFFORT  analyze=$ANALYZE_MODEL/$ANALYZE_EFFORT  implement=$IMPLEMENT_MODEL/$IMPLEMENT_EFFORT  converge=$CONVERGE_MODEL/$CONVERGE_EFFORT  (commit=default)"
echo ""

mkdir -p "$LOG_DIR"

if [ ! -d "$PROMPTS_DIR" ]; then
	log_fail "Prompts directory not found: $PROMPTS_DIR"
	exit 1
fi

# NNN-<slug> (및 레거시 feature-NNN-<slug>) 형식의 feature 폴더만 수집
FEATURES=$(find "$PROMPTS_DIR" -maxdepth 1 -mindepth 1 -type d 2>/dev/null \
	| sort \
	| grep -E '/(feature-)?[0-9]+-[^/]+$' || true)

if [ -z "$FEATURES" ]; then
	log_fail "No feature directories (NNN-<slug>) found in $PROMPTS_DIR"
	log_warn "feature 폴더를 직접 담고 있는 절대 경로를 인자로 전달하세요. 예:"
	log_warn "  $0 /abs/path/to/.speckit-prompts/japanese-tutor"
	exit 1
fi

# ──────────────────────────────────────────────
# Execution Plan
# ──────────────────────────────────────────────
log_info "Execution plan:"
skip_mode=false
[ -n "$FROM_FEATURE" ] && skip_mode=true

for feature_dir in $FEATURES; do
	feature_name=$(basename "$feature_dir")
	feature_num=$(extract_feature_num "$feature_dir")

	if $skip_mode; then
		if feature_num_eq "$feature_num" "$FROM_FEATURE"; then
			skip_mode=false
		else
			echo "  [SKIP] $feature_name"
			continue
		fi
	fi

	if [ -n "$ONLY_FEATURE" ] && ! feature_num_eq "$feature_num" "$ONLY_FEATURE"; then
		echo "  [SKIP] $feature_name"
		continue
	fi

	echo -e "  ${GREEN}[RUN]${NC}  $feature_name"
	plan_step_skip=false
	if [ -n "$FROM_STEP" ] && feature_num_eq "$feature_num" "$FROM_FEATURE"; then
		plan_step_skip=true
	fi
	for step in "${STEPS[@]}"; do
		if $plan_step_skip; then
			step_num="${step%%_*}"
			if step_num_eq "$step_num" "$FROM_STEP"; then
				plan_step_skip=false
			else
				echo "           - $step [SKIP]"
				continue
			fi
		fi
		if $SKIP_CLARIFY && [[ "$step" == "02_clarify" ]]; then
			continue
		fi
		if [ -n "$ONLY_STEP" ] && [[ "$step" != "${ONLY_STEP}_"* ]] && [[ "$step" != *"$ONLY_STEP"* ]]; then
			continue
		fi
		if [ -f "$feature_dir/${step}.md" ]; then
			local_turns=$(get_max_turns_for_step "$step")
			local_model=$(get_model_for_step "$step")
			local_effort=$(get_effort_for_step "$step")
			echo "           - $step (max ${local_turns} turns, model ${local_model:-default}, effort ${local_effort:-default})"
		fi
	done
done
echo ""

if $DRY_RUN; then
	log_warn "DRY RUN — no commands will be executed"
	echo ""
fi

# ──────────────────────────────────────────────
# Execute Pipeline
# ──────────────────────────────────────────────
START_TIME=$(date +%s)
declare -a RESULTS=()
TOTAL_FEATURES=0
PASSED_FEATURES=0
FAILED_FEATURES=0

skip_mode=false
[ -n "$FROM_FEATURE" ] && skip_mode=true

for feature_dir in $FEATURES; do
	feature_name=$(basename "$feature_dir")
	feature_num=$(extract_feature_num "$feature_dir")
	feature_short=$(extract_feature_short_name "$feature_dir")

	if $skip_mode; then
		if feature_num_eq "$feature_num" "$FROM_FEATURE"; then
			skip_mode=false
		else
			continue
		fi
	fi

	if [ -n "$ONLY_FEATURE" ] && ! feature_num_eq "$feature_num" "$ONLY_FEATURE"; then
		continue
	fi

	TOTAL_FEATURES=$((TOTAL_FEATURES + 1))
	log_header "Feature: $feature_name"
	feature_failed=false

	step_skip_active=false
	if [ -n "$FROM_STEP" ] && feature_num_eq "$feature_num" "$FROM_FEATURE"; then
		step_skip_active=true
	fi

	for step in "${STEPS[@]}"; do
		if $step_skip_active; then
			step_num="${step%%_*}"
			if step_num_eq "$step_num" "$FROM_STEP"; then
				step_skip_active=false
			else
				log_warn "Skipped: $step (--from $FROM_FEATURE/$FROM_STEP)"
				continue
			fi
		fi

		if $SKIP_CLARIFY && [[ "$step" == "02_clarify" ]]; then
			log_warn "Skipped: 02_clarify (--skip-clarify)"
			continue
		fi

		if [ -n "$ONLY_STEP" ] && [[ "$step" != "${ONLY_STEP}_"* ]] && [[ "$step" != *"$ONLY_STEP"* ]]; then
			continue
		fi

		prompt_file="$feature_dir/${step}.md"
		log_file="$LOG_DIR/${feature_name}_${step}.log"

		if [ ! -f "$prompt_file" ]; then
			log_warn "Skip: $prompt_file not found"
			continue
		fi

		log_step "Step: $step"
		step_start=$(date +%s)

		# Save checkpoint before execution
		save_checkpoint "$feature_num" "${step%%_*}"

		prompt_content=$(cat "$prompt_file")
		step_turns=$(get_max_turns_for_step "$step")
		step_model=$(get_model_for_step "$step")
		step_effort=$(get_effort_for_step "$step")

		if run_claude_headless "$prompt_content" "$log_file" "$step" "$step_turns" "$step_model" "$step_effort"; then
			step_end=$(date +%s)
			step_duration=$((step_end - step_start))
			log_ok "$step (${step_duration}s)"
		else
			step_end=$(date +%s)
			step_duration=$((step_end - step_start))
			log_fail "$step (${step_duration}s)"
			feature_failed=true

			if [ -t 0 ]; then
				echo -ne "  Continue to next step? (y/n): "
				read -r answer
				if [ "$answer" != "y" ]; then
					log_fail "Pipeline aborted by user"
					RESULTS+=("FAIL: $feature_name ($step)")
					FAILED_FEATURES=$((FAILED_FEATURES + 1))
					break 2
				fi
			else
				log_fail "Pipeline aborted (non-interactive, step failed)"
				RESULTS+=("FAIL: $feature_name ($step)")
				FAILED_FEATURES=$((FAILED_FEATURES + 1))
				break 2
			fi
		fi
	done

	# Commit after converge
	if ! $feature_failed; then
		commit_log="$LOG_DIR/${feature_name}_09_commit.log"
		do_git_commit "$feature_name" "$feature_short" "$commit_log"
		RESULTS+=("OK: $feature_name")
		PASSED_FEATURES=$((PASSED_FEATURES + 1))
		# Clear checkpoint on success
		rm -f "$RESUME_FILE"
	else
		RESULTS+=("FAIL: $feature_name")
		FAILED_FEATURES=$((FAILED_FEATURES + 1))
	fi

	echo ""
done

# ──────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
MINUTES=$((TOTAL_DURATION / 60))
SECONDS_REM=$((TOTAL_DURATION % 60))

log_header "Pipeline Summary"
echo ""
log_info "Duration: ${MINUTES}m ${SECONDS_REM}s"
log_info "Features: $TOTAL_FEATURES total, $PASSED_FEATURES passed, $FAILED_FEATURES failed"
log_info "Logs: $LOG_DIR"
echo ""

for result in "${RESULTS[@]}"; do
	if [[ "$result" == OK:* ]]; then
		echo -e "  ${GREEN}$result${NC}"
	else
		echo -e "  ${RED}$result${NC}"
	fi
done

echo ""

if [ $FAILED_FEATURES -eq 0 ]; then
	echo -e "${GREEN}All features completed successfully!${NC}"
	exit 0
else
	echo -e "${RED}$FAILED_FEATURES feature(s) failed. Check logs for details.${NC}"
	exit 1
fi
