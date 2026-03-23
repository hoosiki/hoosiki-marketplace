# Python Type Hints Rules

> 점진적 타입 적용 정책. pyright + ruff로 검증한다.

## 기본 원칙

- 타입 힌트를 **점진적으로** 적용한다. 모든 코드에 한꺼번에 강제하지 않는다.
- **새로 작성하는 코드**에는 타입 힌트를 필수로 적용한다.
- **기존 코드**는 수정 시 해당 함수/클래스에 타입 힌트를 추가한다.
- pyright를 type checker로, ruff의 type 관련 규칙을 보조로 사용한다.

## 적용 범위

### 필수 (새 코드)

- 모든 public 함수의 매개변수와 반환 타입
- 클래스 속성 (특히 `__init__`에서 정의하는 인스턴스 변수)
- 모듈 레벨 상수/변수

```python
def send_webhook(url: str, token: str, payload: dict[str, str]) -> bool:
    ...

class WebhookClient:
    base_url: str
    timeout: int

    def __init__(self, base_url: str, timeout: int = 30) -> None:
        self.base_url = base_url
        self.timeout = timeout
```

### 권장 (기존 코드 수정 시)

- 수정하는 함수에 타입 힌트 추가
- 해당 함수가 호출하는 내부 헬퍼에도 가능하면 추가

### 선택 (나중에)

- 테스트 코드 (fixture 반환 타입 등)
- 단순한 스크립트/일회성 코드
- private 헬퍼 함수의 지역 변수

## 타입 표기 규칙

### 모던 문법 사용 (Python 3.10+)

```python
# Good — 내장 타입 직접 사용
def process(items: list[str]) -> dict[str, int]:
    result: str | None = None
    ...

# Bad — typing 모듈에서 import
from typing import List, Dict, Optional
def process(items: List[str]) -> Dict[str, int]:
    result: Optional[str] = None
```

### 주요 패턴

```python
from collections.abc import Callable, Sequence, Mapping
from typing import Any, TypeAlias

# Union → | 연산자
value: str | int | None

# Callable
handler: Callable[[str, int], bool]

# TypeAlias (복잡한 타입)
Payload: TypeAlias = dict[str, str | int | list[str]]

# TypedDict (구조화된 dict)
from typing import TypedDict

class WebhookConfig(TypedDict):
    url: str
    token: str
    format: str
    timeout: int
```

## pyright 설정

프로젝트 루트에 `pyrightconfig.json`:

```json
{
  "typeCheckingMode": "basic",
  "pythonVersion": "3.10",
  "reportMissingTypeStubs": false,
  "reportUnknownMemberType": false,
  "include": ["plugins", "tests"],
  "exclude": ["**/__pycache__", ".ruff_cache"]
}
```

- `basic` 모드에서 시작하여 점진적으로 `standard`로 올린다.
- 새 모듈을 추가할 때 `include`에 반영한다.

## ruff 연계 규칙

ruff에서 활성화할 type 관련 규칙:

- `UP` (pyupgrade): 레거시 타입 표기를 모던 문법으로 자동 변환
- `ANN` (flake8-annotations): 타입 힌트 누락 경고 (새 파일에만 적용 권장)
- `TCH` (flake8-type-checking): `TYPE_CHECKING` 블록 최적화

## 금지 사항

- `Any`를 편의를 위해 남용하지 않는다. 정말 any 타입이 필요한 경우에만 사용한다.
- `# type: ignore`를 주석 없이 사용하지 않는다. 사유를 반드시 명시한다.
  ```python
  result = external_lib.call()  # type: ignore[no-untyped-call]  # 라이브러리에 스텁 없음
  ```
- `cast()`를 남용하지 않는다. 타입 좁히기(`isinstance`, 패턴 매칭)를 우선 사용한다.
