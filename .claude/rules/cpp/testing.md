# C++ Testing Rules (Google Test)

> TDD 원칙 기반. Google Test를 테스트 프레임워크로 사용한다.

## 핵심 원칙: Red-Green-Refactor

1. **Red** — 실패하는 테스트를 먼저 작성한다
2. **Green** — 테스트를 통과하는 최소한의 코드를 작성한다
3. **Refactor** — 테스트가 통과하는 상태를 유지하며 코드를 정리한다

## 디렉토리 구조

```
project/
├── src/
│   ├── core/
│   │   ├── event_handler.h
│   │   └── event_handler.cc
│   └── webhook/
│       ├── webhook_client.h
│       └── webhook_client.cc
├── tests/
│   ├── core/
│   │   └── event_handler_test.cc
│   └── webhook/
│       └── webhook_client_test.cc
├── CMakeLists.txt
└── tests/CMakeLists.txt
```

- 테스트 파일은 `tests/` 디렉토리에 소스와 동일한 하위 구조로 배치한다.
- 테스트 파일명: `{소스파일명}_test.cc`
- 소스 파일과 테스트 파일은 1:1 대응을 유지한다.

## 테스트 작성 규칙

### 기본 구조

```cpp
#include "hoosiki/core/event_handler.h"

#include <gtest/gtest.h>
#include <gmock/gmock.h>

namespace hoosiki::core {
namespace {

// Test fixture
class EventHandlerTest : public ::testing::Test {
 protected:
  void SetUp() override {
    handler_ = std::make_unique<EventHandler>();
  }

  std::unique_ptr<EventHandler> handler_;
};

// 테스트명: Test Suite / Test Case 패턴
// TestSuite: 테스트 대상 클래스 또는 기능
// TestCase: {동작}_{조건}_{기대결과}
TEST_F(EventHandlerTest, ProcessEvent_WithValidPayload_ReturnsSuccess) {
  // Arrange
  Event event{.type = "webhook", .data = "test"};

  // Act
  auto result = handler_->ProcessEvent(event);

  // Assert
  EXPECT_EQ(result, Status::kSuccess);
}

TEST_F(EventHandlerTest, ProcessEvent_WithEmptyData_ReturnsInvalidArgument) {
  Event event{.type = "webhook", .data = ""};

  auto result = handler_->ProcessEvent(event);

  EXPECT_EQ(result, Status::kInvalidArgument);
}

}  // namespace
}  // namespace hoosiki::core
```

### 네이밍 규칙

- Test Suite: `{클래스명}Test` 또는 `{기능명}Test`
- Test Case: `{동작}_{조건}_{기대결과}`
- 모든 테스트명은 테스트 의도를 명확히 드러내야 한다.

### Assertion 사용

```cpp
// 값 비교
EXPECT_EQ(actual, expected);   // ==
EXPECT_NE(actual, expected);   // !=
EXPECT_LT(actual, expected);   // <
EXPECT_GT(actual, expected);   // >

// 불리언
EXPECT_TRUE(condition);
EXPECT_FALSE(condition);

// 문자열
EXPECT_STREQ(actual, expected);
EXPECT_THAT(str, ::testing::HasSubstr("partial"));

// 예외
EXPECT_THROW(statement, ExceptionType);
EXPECT_NO_THROW(statement);

// 치명적 실패 (테스트 즉시 중단)는 ASSERT_* 사용
ASSERT_NE(ptr, nullptr);  // nullptr이면 이후 코드 실행 무의미
ptr->DoSomething();
```

- 일반적으로 `EXPECT_*` 사용 (하나의 테스트에서 여러 검증 가능).
- `ASSERT_*`는 이후 코드가 의존하는 전제 조건에만 사용.

## Google Mock

```cpp
#include <gmock/gmock.h>

class MockHttpClient : public HttpClientInterface {
 public:
  MOCK_METHOD(StatusCode, Post,
              (const std::string& url, const std::string& body), (override));
  MOCK_METHOD(StatusCode, Get,
              (const std::string& url), (override, const));
};

TEST_F(WebhookClientTest, Send_CallsPostWithCorrectUrl) {
  MockHttpClient mock_client;
  WebhookClient webhook(&mock_client);

  EXPECT_CALL(mock_client, Post("https://example.com/hook", ::testing::_))
      .WillOnce(::testing::Return(StatusCode::kOk));

  auto result = webhook.Send("test message");

  EXPECT_EQ(result, Status::kSuccess);
}
```

- 외부 의존성(네트워크, 파일시스템)은 인터페이스 추출 후 Mock으로 대체.
- `EXPECT_CALL`로 호출 검증, `WillOnce`/`WillRepeatedly`로 반환값 설정.

## Parameterized Tests

```cpp
class ValidateUrlTest : public ::testing::TestWithParam<std::pair<std::string, bool>> {};

TEST_P(ValidateUrlTest, ReturnsExpectedResult) {
  auto [url, expected] = GetParam();
  EXPECT_EQ(ValidateUrl(url), expected);
}

INSTANTIATE_TEST_SUITE_P(
    UrlValidation, ValidateUrlTest,
    ::testing::Values(
        std::make_pair("https://example.com", true),
        std::make_pair("http://example.com/path", true),
        std::make_pair("ftp://example.com", false),
        std::make_pair("not-a-url", false)
    ));
```

## 테스트 실행

```bash
# 전체 테스트
cd build && ctest --output-on-failure

# 특정 테스트 필터
./tests/all_tests --gtest_filter="EventHandlerTest.*"

# 상세 출력
./tests/all_tests --gtest_print_time=1
```

## 테스트 커버리지

- 모든 public 메서드는 최소 1개 이상의 테스트를 가진다.
- 정상 경로와 에러 경로를 모두 테스트한다.
- 경계값과 엣지 케이스를 포함한다.
- 각 테스트는 하나의 동작만 검증한다.
- Arrange-Act-Assert (AAA) 패턴을 따른다.

## 구현 워크플로우

### 새 기능 추가 시

```
1. 요구사항 분석
2. 테스트 파일 생성 → 실패하는 테스트 작성 (Red)
3. ctest 실행 → 빌드 실패 또는 테스트 실패 확인
4. 최소한의 구현 코드 작성 (Green)
5. ctest 실행 → 테스트 통과 확인
6. 코드 리팩토링 (Refactor)
7. ctest 실행 → 테스트 여전히 통과 확인
```

### 버그 수정 시

```
1. 버그 재현 테스트 작성 (Red)
2. ctest 실행 → 테스트 실패 확인
3. 버그 수정 (Green)
4. ctest 실행 → 테스트 통과 확인
```

## 금지 사항

- 테스트 없이 새로운 C++ 코드를 커밋하지 않는다.
- 실패하는 테스트를 `DISABLED_`로 무시하고 커밋하지 않는다 (명확한 사유 주석 없이).
- 테스트에서 실제 네트워크 호출, 파일시스템 접근을 하지 않는다 (Mock 사용).
- `sleep()`을 테스트에서 사용하지 않는다.
- 테스트 간 상태 공유나 실행 순서 의존성을 만들지 않는다.
