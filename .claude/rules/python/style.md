# Python Style Rules

> PEP 8 기반 코딩 스타일. ruff를 린터/포매터로 사용한다.

## 기본 원칙

- PEP 8을 기본 스타일 가이드로 따른다.
- ruff로 자동 검사/수정 가능한 항목은 ruff에 위임한다.
- ruff가 커버하지 않는 영역만 이 문서에서 명시한다.

## 포매팅

- 들여쓰기: 스페이스 4칸 (탭 금지)
- 최대 줄 길이: 120자 (ruff `line-length = 120`)
- 문자열: 큰따옴표(`"`) 기본 사용 (ruff `quote-style = "double"`)
- trailing comma: 멀티라인 컬렉션에 항상 추가

## 네이밍

| 대상 | 규칙 | 예시 |
|------|------|------|
| 모듈/패키지 | `snake_case` | `webhook.py`, `notify_stop.py` |
| 함수/변수 | `snake_case` | `build_message()`, `event_type` |
| 클래스 | `PascalCase` | `WebhookClient`, `EventHandler` |
| 상수 | `UPPER_SNAKE_CASE` | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| private | `_` 접두사 | `_validate_url()`, `_internal_state` |

## Import 규칙

```python
# 1. 표준 라이브러리
import os
import sys
from pathlib import Path

# 2. 서드파티
import pytest
from unittest.mock import patch

# 3. 로컬/프로젝트
from webhook import build_message
```

- import 그룹 사이에 빈 줄 1개
- ruff의 `isort` 규칙(`I`)으로 자동 정렬
- 와일드카드 import(`from x import *`) 금지
- 순환 import 금지

## 함수/메서드

- 함수는 하나의 책임만 가진다.
- 함수 길이는 50줄 이내를 권장한다.
- 중첩 함수는 2단계까지만 허용한다.
- 매개변수는 5개 이내를 권장한다. 초과 시 dataclass 또는 TypedDict 사용을 고려한다.

## 주석 및 Docstring

- 코드가 자명한 경우 주석을 달지 않는다.
- 복잡한 비즈니스 로직이나 비직관적인 결정에만 주석을 단다.
- public 함수/클래스에는 docstring을 작성한다 (Google style).

```python
def build_payload(message: str, format_type: str) -> dict:
    """메시지를 지정된 포맷의 payload로 변환한다.

    Args:
        message: 전송할 메시지 본문.
        format_type: webhook 포맷 ("discord", "slack", "generic").

    Returns:
        포맷에 맞는 payload 딕셔너리.

    Raises:
        ValueError: 지원하지 않는 format_type인 경우.
    """
```

## ruff 실행

```bash
# 린트 검사
ruff check .

# 자동 수정
ruff check --fix .

# 포매팅
ruff format .
```

## 금지 사항

- `print()` 디버깅 코드를 커밋하지 않는다 (로깅 사용).
- mutable 기본 인자를 사용하지 않는다 (`def f(items=[])`).
- bare `except:` 를 사용하지 않는다 (최소 `except Exception:`).
- 글로벌 변수를 통한 상태 공유를 하지 않는다.
