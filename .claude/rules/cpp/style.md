# C++ Style Rules

> Google C++ Style Guide 기반. C++20 표준을 사용한다.

## 기본 원칙

- [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)를 기본으로 따른다.
- C++20 기능을 적극 활용한다.
- 이 문서는 Google 스타일에서 프로젝트에 맞게 조정한 항목만 명시한다.

## 네이밍

| 대상 | 규칙 | 예시 |
|------|------|------|
| 파일 | `snake_case.cc` / `snake_case.h` | `event_handler.cc`, `event_handler.h` |
| 클래스/구조체 | `PascalCase` | `EventHandler`, `WebhookClient` |
| 함수 | `PascalCase` | `SendMessage()`, `BuildPayload()` |
| 변수 | `snake_case` | `event_type`, `retry_count` |
| 멤버 변수 | `snake_case_` (trailing underscore) | `base_url_`, `timeout_` |
| 상수 | `kPascalCase` | `kMaxRetries`, `kDefaultTimeout` |
| 매크로 | `UPPER_SNAKE_CASE` | `HOOSIKI_VERSION_MAJOR` |
| 네임스페이스 | `snake_case` | `hoosiki::webhook` |
| enum 값 | `kPascalCase` | `kSuccess`, `kNotFound` |
| 템플릿 파라미터 | `PascalCase` | `typename Container`, `typename ValueType` |

## 파일 구조

### 헤더 파일 (.h)

```cpp
#ifndef HOOSIKI_MODULE_NAME_H_
#define HOOSIKI_MODULE_NAME_H_

// 1. C 시스템 헤더
#include <cstdint>

// 2. C++ 표준 라이브러리
#include <string>
#include <vector>

// 3. 서드파티 라이브러리
#include "gtest/gtest.h"

// 4. 프로젝트 헤더
#include "hoosiki/core/types.h"

namespace hoosiki::module {

class ClassName {
 public:
  // 생성자, 소멸자
  // public 메서드

 private:
  // private 메서드
  // 멤버 변수
};

}  // namespace hoosiki::module

#endif  // HOOSIKI_MODULE_NAME_H_
```

- `#pragma once` 대신 전통적인 include guard 사용 (Google 스타일)
- include 그룹 사이에 빈 줄 1개

### 소스 파일 (.cc)

```cpp
#include "hoosiki/module/class_name.h"  // 대응하는 헤더 먼저

#include <algorithm>

#include "hoosiki/core/logging.h"

namespace hoosiki::module {

// 구현

}  // namespace hoosiki::module
```

## 포매팅

- 들여쓰기: 스페이스 2칸
- 최대 줄 길이: 80자
- 중괄호: K&R 스타일 (여는 중괄호는 같은 줄)
- `clang-format`으로 자동 포매팅 (`.clang-format` 파일에 `BasedOnStyle: Google`)

## C++20 기능 활용

### 적극 사용

- `std::format` (문자열 포매팅)
- `std::span` (배열/버퍼 참조)
- Concepts (템플릿 제약)
- `constexpr` 확장 (constexpr 가상 함수, constexpr 동적 메모리)
- Designated initializers
- `std::ranges` 알고리즘
- Three-way comparison (`<=>`)
- `[[nodiscard]]`, `[[likely]]`, `[[unlikely]]`

### 사용 예시

```cpp
// Concepts
template <std::integral T>
T SafeAdd(T a, T b);

// Ranges
auto filtered = items | std::views::filter([](const auto& item) {
  return item.IsValid();
});

// Designated initializers
WebhookConfig config{
    .url = "https://example.com",
    .timeout = 30,
};

// std::format
auto msg = std::format("[{}] {}: {}", hostname, project, message);
```

## 클래스 설계

- Rule of Zero를 기본으로 한다 (특수 멤버 함수를 직접 정의하지 않음).
- 리소스 관리가 필요하면 Rule of Five를 따른다.
- 가상 소멸자가 필요한 클래스는 `virtual ~ClassName() = default;`
- 단일 매개변수 생성자에는 `explicit` 키워드 필수.
- 복사/이동을 금지할 때는 `= delete`로 명시한다.

## 금지 사항

- `using namespace std;` 금지 (헤더 파일에서 절대 금지, 소스 파일에서도 자제).
- C 스타일 캐스트 금지. `static_cast`, `dynamic_cast`, `reinterpret_cast` 사용.
- `goto` 금지.
- 매크로 남용 금지. `constexpr`, `inline`, 템플릿으로 대체.
- `new`/`delete` 직접 사용 금지. 스마트 포인터 사용 (memory-safety.md 참조).
- 전역 변수 사용 금지 (상수 제외).
