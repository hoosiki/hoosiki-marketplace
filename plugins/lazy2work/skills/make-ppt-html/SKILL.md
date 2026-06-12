---
name: make-ppt-html
description: >
  Convert any input document (markdown research note, report, README, storyboard, spec)
  into a presentation-quality reveal.js + Tailwind CSS single-file HTML slide deck with a
  light↔dark theme toggle button. Use this skill whenever the user wants a document turned
  into slides, a PPT, or presentation material — triggers include "ppt로 만들어", "발표자료로",
  "슬라이드로 변환", "html 프레젠테이션", "reveal.js로 만들어", "presentation 만들어줘",
  "make slides from this doc", "deck으로" — even if they don't explicitly say "reveal.js"
  or "HTML". Produces assertion-evidence slides following bundled design guidelines
  (60-30-10 color rule, single accent color, WCAG contrast, Pretendard, 960×700 canvas)
  with speaker notes, PDF export support, and a verified light/dark toggle.
---

# make-ppt-html — 문서 → reveal.js + Tailwind 프레젠테이션 HTML

입력 문서를 읽고, 디자인 가이드라인을 따르는 **단일 HTML 발표 덱**을 만든다.
산출물: reveal.js 5.2.1 + Tailwind Play CDN(전략 A — 내장 테마 미사용) + 라이트↔다크 토글
(버튼 + `D` 단축키 + localStorage 기억) + 발표자 노트 + `?print-pdf` 지원.

## 워크플로

### 1. 입력 문서를 읽고 슬라이드를 설계한다

- 문서에서 **BLUF(결론) · 주요 섹션 3~7개 · 하이라이트 인사이트 1~2개**를 식별한다.
- 10~20장으로 계획한다. 슬라이드 수는 공짜다 — 내용이 많으면 쪼갠다.
- **모든 슬라이드 제목은 주장 문장(assertion)으로** 쓴다. "성능 분석"(주제어) ❌ →
  "BBQ 양자화는 메모리를 95% 줄인다"(주장) ✅. 본문은 그 주장의 증거 1개.
- 슬라이드마다 **주인공 1개**(가장 큰 요소 = 그 슬라이드의 결론)를 정한다.
- 상세 수치·출처·부연은 `<aside class="notes">`로 보낸다 (본문의 3~5배 분량).
- 하이라이트 슬라이드 1~2장은 `data-bg-role="divider"`로 배경을 교차시켜 리듬을 만든다.

### 2. 템플릿을 복사해서 시작한다

`assets/template.html`을 출력 경로로 복사하고 슬라이드 영역만 교체한다.

- 출력 파일명: `presentation_<주제슬러그>_<YYYYMMDD>.html`, 입력 문서와 같은 디렉토리
  (사용자가 다른 위치를 지정하면 그곳).
- **템플릿의 CSS/JS 배관을 새로 쓰지 마라.** 토글 로직·border 보정·인쇄 숨김·UI 크롬은
  실브라우저 검증을 거친 코드다 — 아래 "기술 가드레일"에 각각이 없으면 무엇이 깨지는지 있다.
- 템플릿 안의 `<!-- PATTERN: ... -->` 주석이 슬라이드 유형별 마크업 견본이다.

### 3. 토큰 표대로 색을 쓴다 (라이트/다크 클래스를 항상 쌍으로)

토글 덱의 제1규칙: **코드 카드 밖의 모든 색 유틸리티는 `dark:` 짝이 필요하다.**
하나라도 빠지면 다크 모드에서 그 요소만 라이트 색으로 남는다. 다 만든 뒤 자신의 출력에서
`text-`/`bg-`/`border-` 색 클래스를 grep해 짝 없는 것을 찾아라.

| 역할 | 클래스 쌍 (그대로 복사) |
|---|---|
| 제목·강한 본문 | `text-slate-800 dark:text-slate-100` |
| 일반 본문 | `text-slate-700 dark:text-slate-200` |
| 보조 텍스트 | `text-slate-500 dark:text-slate-400` |
| 보조 — **divider 배경 위** | `text-slate-600 dark:text-slate-400` (아래 대비 함정 참조) |
| 카드 | `bg-white border border-slate-200 dark:bg-slate-800 dark:border-slate-700` |
| **강조 (슬라이드당 1~2곳)** | `text-blue-600 dark:text-sky-400` + `font-bold` |
| 시맨틱 긍정 | `text-emerald-700 dark:text-emerald-400` + ✓ |
| 시맨틱 부정 | `text-red-600 dark:text-red-400` + ✗ |
| 시맨틱 주의 | `text-amber-700 dark:text-amber-400` + ⚠ |
| 표 보더 | `border-slate-200 dark:border-slate-700` (헤더는 `-300`/`-600`) |
| 코드 카드 (테마 불변) | `bg-slate-900 dark:bg-slate-950 border border-slate-700` + `text-slate-100`, 주석 `text-slate-400`, 코드 내 강조 `text-sky-400` — **내부에 dark: 불필요** |

**WCAG 실측으로 확인된 대비 함정** (이 조합들은 그럴듯해 보이지만 실패한다):

- `text-slate-500`을 divider 배경(slate-100)에 직접 올리면 4.34:1로 본문 기준(4.5:1) 미달
  → divider 슬라이드에서는 `text-slate-600`.
- `text-amber-600`·`text-emerald-600`을 흰 배경 텍스트로 쓰면 3.19/3.77:1로 실패
  → 텍스트는 **-700 단계**, -600은 보더·배경 스와치 전용.
- `text-slate-400`은 **다크 모드 전용 토큰** — 라이트 배경 위 텍스트로 쓰지 마라(2.4~2.6:1).
- 흐름 화살표(→·↓) 같은 의미 있는 그래픽은 `text-slate-500` 이상(3:1 그래픽 기준).

### 4. 크기·레이아웃 규칙 (요약 — 전체는 references/design-guidelines.md)

- 표지 `text-6xl` / 슬라이드 제목 `text-4xl`~`5xl` bold / **본문 `text-2xl`(하한 `xl`)** /
  캡션 `text-base`~`lg` / **코드 `text-base` 하한**(본문보다 작게 금지) / 스탯 콜아웃 `text-7xl`.
- 정보 유형 → 레이아웃: 단일 주장=중앙 대형 · 비교=`grid grid-cols-2 gap-8` 동일 구조 ·
  프로세스=번호+화살표 ≤5단계 · 정확 수치=표 · 목록 ≤4불릿 · 상세·부록=vertical `<section>` 중첩.
- 본문은 좌측 정렬(`text-left`), 중앙 정렬은 제목·단일 메시지만. 한글 이탤릭 금지(굵기·색으로).
- 강조는 색+굵기 **이중 단서**, 상태는 색+아이콘(✓/✗/⚠) 병행 — 적록색약 ~8% 대응.
- 차트·다이어그램 다색이 필요하면 Okabe-Ito 8색을 임의값으로(`text-[#E69F00]` 등).
- 입력 문서의 mermaid 다이어그램은 **내용 동일한 HTML/Tailwind 박스 플로우로 재구현**한다
  (mermaid 라이브러리는 다크 토글에 재렌더링이 필요해 토글 덱과 상성이 나쁘다).

### 5. 기술 가드레일 (왜 템플릿이 그렇게 생겼는가)

- **960×700 고정 좌표계**: reveal은 `transform: scale`로 통째로 확대/축소한다.
  `vh`/`vw`/% 높이/`md:`·`lg:` 반응형 prefix는 무효 또는 깨짐 — 절대 좌표로 디자인.
- **border-style 보정은 필수**: reveal `reset.css`(Meyer)의 `div{border:0}`(명시도 0,0,1)가
  Tailwind Preflight의 `*{border-style:solid}`(0,0,0)를 이긴다 → border-style이 none이 되고
  CSS 규칙상 computed border-width가 0으로 강제되어 **모든 border 유틸이 조용히 사라진다**.
  템플릿의 `.reveal .slides * { border-style: solid; }` 한 줄이 이것을 복원한다 — 지우지 마라.
- **토글 동작 원리**: 모든 leaf `<section>`의 `data-background-color`를 테마 맵으로 다시 쓰고
  `Reveal.sync()`로 배경을 재생성한다. 따라서 **vertical 스택의 래퍼 `<section>`에는
  `data-background-color`를 절대 넣지 마라** (JS 셀렉터가 leaf만 잡도록 설계됨).
- **인쇄 숨김**: `#theme-toggle`은 `position:fixed`라 숨기지 않으면 PDF 모든 페이지에 찍힌다.
  템플릿의 `html.reveal-print` + `@media print` 규칙이 처리한다.
- **`D` 단축키 가드**: reveal의 슬라이드 점프(`G`) 입력 중 d 타이핑이 토글을 누르지 않도록
  activeElement 검사가 들어 있다.
- 슬라이드 콘텐츠 높이는 **~650px 이하**로 설계한다(좌표계 700px - 여백).
- `style=` 인라인 속성 금지(토글 버튼 아이콘 스왑 제외 — 템플릿에 이미 있는 것만).
- 이미지: 입력 문서가 참조하는 이미지는 출력 옆 `img/`로 **복사**해 상대 경로로 쓴다
  (덱 폴더가 자체 완결되도록). CC 라이선스 이미지는 캡션에 표기(정자체 `text-sm`).

### 6. 검증한다 (선택이 아니라 워크플로의 일부)

정적 검사 (항상):

- [ ] 모든 leaf `<section>`에 `data-background-color` 있음 / 래퍼에는 없음
- [ ] `md:`·`lg:`·`vh`·`vw` 미사용, `.slides` 안에 `style=` 없음
- [ ] 코드 카드 밖의 모든 색 클래스에 `dark:` 짝 있음
- [ ] 콘텐츠 슬라이드에 `<aside class="notes">` 있음
- [ ] 강조색 텍스트가 슬라이드당 1~2곳 이하

브라우저 검사 (chrome-devtools MCP·Playwright 등이 사용 가능할 때):

- [ ] `file://`로 열어 콘솔 에러 0 확인
- [ ] 각 leaf section의 `scrollHeight ≤ 680` (비활성 슬라이드는 `display:block` 후 측정)
- [ ] 토글 클릭 → `html.dark` 토글 + 배경색 변경 확인, 양 테마 스크린샷
- [ ] `?print-pdf`로 열어 `.pdf-page` 수 == 슬라이드 수, 토글 버튼 숨김 확인

### 7. 사용자에게 알린다

- 파일 경로, 슬라이드 수, 조작법: 토글 버튼/`D` 키, `S` 발표자 노트, `ESC` overview,
  PDF는 `?print-pdf` → Chrome 인쇄(가로·여백 없음·배경 그래픽 ON).
- **CDN 주의**: Tailwind Play CDN + Pretendard CDN은 프로토타입용 — 오프라인 발표 전
  빌드/로컬 번들로 교체하라고 안내한다.

## 참조 파일

- `references/design-guidelines.md` — 전체 디자인 규격(색상 5규칙·폰트·위계 8레버·
  레이아웃 매핑·금지 목록·체크리스트). 슬라이드 설계 단계에서 읽는다.
- `assets/template.html` — 검증된 보일러플레이트 + 슬라이드 패턴 견본. 2단계에서 복사한다.
