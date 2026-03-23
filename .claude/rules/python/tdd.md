# Python TDD (Test-Driven Development) Rules

> 이 프로젝트의 모든 Python 파일에 대해 TDD 원칙을 적용한다.

## 핵심 원칙: Red-Green-Refactor

1. **Red** — 실패하는 테스트를 먼저 작성한다
2. **Green** — 테스트를 통과하는 최소한의 코드를 작성한다
3. **Refactor** — 테스트가 통과하는 상태를 유지하며 코드를 정리한다

## 필수 규칙

### 1. 테스트 먼저 작성

- 새로운 함수, 클래스, 모듈을 구현하기 **전에** 반드시 테스트를 먼저 작성한다.
- 기존 코드를 수정할 때도 변경 사항을 검증하는 테스트를 **먼저** 추가하거나 수정한다.
- 버그 수정 시 해당 버그를 재현하는 테스트를 **먼저** 작성한 후 수정한다.

### 2. 테스트 파일 구조

```
tests/
├── __init__.py
├── test_webhook.py          # plugins/lazy2work/scripts/webhook.py
├── test_notify_waiting.py   # plugins/lazy2work/scripts/notify_waiting.py
├── test_notify_stop.py      # plugins/lazy2work/scripts/notify_stop.py
└── test_up2date.py          # plugins/lazy2work/skills/up2date/scripts/up2date.py
```

- 테스트 파일은 `tests/` 디렉토리에 위치한다.
- 테스트 파일명은 `test_` 접두사를 붙인다: `test_{module_name}.py`
- 소스 파일과 테스트 파일은 1:1 대응을 유지한다.

### 3. 테스트 작성 규칙

```python
# 테스트 함수명: test_{동작}_{조건}_{기대결과} 패턴 사용
def test_build_message_with_valid_event_returns_formatted_string():
    ...

def test_validate_url_with_ftp_scheme_returns_false():
    ...

def test_send_webhook_with_invalid_url_raises_system_exit():
    ...
```

- **pytest**를 테스트 프레임워크로 사용한다.
- 테스트 함수명은 `test_` 접두사로 시작하고, 테스트 의도를 명확히 드러낸다.
- 함수명 패턴: `test_{동작}_{조건}_{기대결과}`
- 각 테스트는 하나의 동작만 검증한다 (Single Assertion Principle).
- `Arrange-Act-Assert` (AAA) 패턴을 따른다.

### 4. 테스트 커버리지

- 모든 public 함수는 최소 1개 이상의 테스트를 가진다.
- 정상 경로(happy path)와 에러 경로(error path)를 모두 테스트한다.
- 경계값(boundary)과 엣지 케이스를 포함한다.
- 외부 의존성(네트워크, 파일시스템, 환경변수)은 mock/patch를 사용한다.

### 5. Mock 및 Fixture 사용

```python
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_env(monkeypatch):
    """공통 환경변수 fixture."""
    monkeypatch.setenv("CLAUDE_WEBHOOK_URL", "https://example.com/hook")
    monkeypatch.setenv("CLAUDE_WEBHOOK_FORMAT", "generic")

@patch("webhook.urlopen")
def test_send_webhook_calls_urlopen(mock_urlopen):
    ...
```

- 네트워크 호출(`urlopen`, `subprocess.run` 등)은 반드시 mock한다.
- 환경변수는 `monkeypatch.setenv()`로 격리한다.
- 파일시스템 접근은 `tmp_path` fixture 또는 mock을 사용한다.
- fixture는 `conftest.py`에 공통으로 정의한다.

### 6. 테스트 실행

```bash
# 전체 테스트 실행
pytest tests/ -v

# 특정 모듈 테스트
pytest tests/test_webhook.py -v

# 커버리지 리포트
pytest tests/ --cov=plugins --cov-report=term-missing
```

- 코드 변경 후 반드시 관련 테스트를 실행하여 통과를 확인한다.
- PR/커밋 전에 전체 테스트 스위트를 실행한다.

## 구현 워크플로우

### 새 기능 추가 시

```
1. 요구사항 분석
2. 테스트 파일 생성/수정 → 실패하는 테스트 작성 (Red)
3. pytest 실행 → 테스트 실패 확인
4. 최소한의 구현 코드 작성 (Green)
5. pytest 실행 → 테스트 통과 확인
6. 코드 리팩토링 (Refactor)
7. pytest 실행 → 테스트 여전히 통과 확인
8. 다음 테스트 케이스로 반복
```

### 버그 수정 시

```
1. 버그 재현 테스트 작성 (Red)
2. pytest 실행 → 테스트 실패 확인 (버그 재현됨)
3. 버그 수정 코드 작성 (Green)
4. pytest 실행 → 테스트 통과 확인
5. 회귀 테스트로 유지
```

### 리팩토링 시

```
1. 기존 테스트가 모두 통과하는지 확인
2. 코드 리팩토링 수행
3. 기존 테스트가 여전히 통과하는지 확인
4. 필요 시 테스트도 함께 리팩토링
```

## 프로젝트별 테스트 가이드

### webhook.py 테스트 예시

```python
# tests/test_webhook.py
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def webhook_env(monkeypatch):
    monkeypatch.setenv("CLAUDE_WEBHOOK_URL", "https://hooks.example.com/test")
    monkeypatch.setenv("CLAUDE_WEBHOOK_TOKEN", "test-token")
    monkeypatch.setenv("CLAUDE_WEBHOOK_FORMAT", "generic")

class TestBuildMessage:
    @patch("webhook.get_hostname", return_value="myhost")
    @patch("webhook.get_cwd_name", return_value="myproject")
    def test_includes_hostname_and_cwd(self, mock_cwd, mock_host):
        from webhook import build_message
        result = build_message("Hello!")
        assert result == "[myhost] myproject: Hello!"

class TestBuildPayload:
    def test_discord_format_uses_content_key(self):
        from webhook import build_payload
        result = build_payload("msg", "discord")
        assert result == {"content": "msg"}

    def test_generic_format_uses_text_key(self):
        from webhook import build_payload
        result = build_payload("msg", "generic")
        assert result == {"text": "msg"}

class TestValidateUrl:
    @pytest.mark.parametrize("url,expected", [
        ("https://example.com", True),
        ("http://example.com/path", True),
        ("ftp://example.com", False),
        ("file:///etc/passwd", False),
        ("not-a-url", False),
    ])
    def test_url_validation(self, url, expected):
        from webhook import _validate_url
        assert _validate_url(url) == expected

class TestSendWebhook:
    @patch("webhook.urlopen")
    def test_sends_json_post_for_generic(self, mock_urlopen):
        from webhook import send_webhook
        send_webhook("https://example.com", "", {"text": "hi"}, "generic")
        mock_urlopen.assert_called_once()

class TestRun:
    @patch("webhook.send_webhook")
    def test_skips_when_no_url(self, mock_send, monkeypatch):
        monkeypatch.delenv("CLAUDE_WEBHOOK_URL", raising=False)
        from webhook import run
        run("test")
        mock_send.assert_not_called()
```

## 금지 사항

- 테스트 없이 새로운 Python 코드를 커밋하지 않는다.
- 실패하는 테스트를 무시(`skip`, `xfail`)하고 커밋하지 않는다 (명확한 사유 주석 없이).
- 테스트에서 실제 외부 서비스(웹훅 URL, API 등)를 호출하지 않는다.
- `time.sleep()`을 테스트에서 사용하지 않는다.
- 테스트 간 상태 공유나 실행 순서 의존성을 만들지 않는다.
