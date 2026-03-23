# C++ Build Rules (CMake)

> CMake를 빌드 시스템으로 사용한다. C++20 표준.

## 기본 설정

### 최소 CMake 버전

```cmake
cmake_minimum_required(VERSION 3.20)
project(hoosiki
  VERSION 1.0.0
  LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
```

- CMake 3.20 이상 사용 (C++20 모듈 지원).
- `CMAKE_CXX_EXTENSIONS OFF`로 GNU 확장 비활성화.

## 프로젝트 디렉토리 레이아웃

```
project/
├── CMakeLists.txt              # 루트 CMake
├── cmake/
│   ├── CompilerWarnings.cmake  # 경고 옵션
│   └── Dependencies.cmake      # 외부 의존성 (FetchContent)
├── src/
│   ├── CMakeLists.txt
│   ├── core/
│   │   ├── CMakeLists.txt
│   │   ├── event_handler.h
│   │   └── event_handler.cc
│   └── webhook/
│       ├── CMakeLists.txt
│       ├── webhook_client.h
│       └── webhook_client.cc
├── tests/
│   ├── CMakeLists.txt
│   ├── core/
│   │   └── event_handler_test.cc
│   └── webhook/
│       └── webhook_client_test.cc
└── build/                      # 빌드 디렉토리 (git 무시)
```

## 컴파일러 경고

`cmake/CompilerWarnings.cmake`:

```cmake
add_library(project_warnings INTERFACE)

target_compile_options(project_warnings INTERFACE
  -Wall
  -Wextra
  -Wpedantic
  -Wshadow
  -Wnon-virtual-dtor
  -Wold-style-cast
  -Wcast-align
  -Wunused
  -Woverloaded-virtual
  -Wconversion
  -Wsign-conversion
  -Wnull-dereference
  -Wformat=2
  -Wimplicit-fallthrough
)

# Treat warnings as errors in CI
option(WARNINGS_AS_ERRORS "Treat warnings as errors" OFF)
if(WARNINGS_AS_ERRORS)
  target_compile_options(project_warnings INTERFACE -Werror)
endif()
```

- 개발 중에는 경고만, CI에서는 `-Werror` 활성화.

## 외부 의존성 관리

`cmake/Dependencies.cmake`:

```cmake
include(FetchContent)

# Google Test
FetchContent_Declare(
  googletest
  GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_TAG v1.14.0
)
FetchContent_MakeAvailable(googletest)
```

- `FetchContent`로 의존성 관리 (시스템 설치 의존 없음).
- 버전을 태그로 고정한다.
- `find_package()`는 시스템 라이브러리에만 사용.

## 라이브러리/실행파일 정의

```cmake
# src/core/CMakeLists.txt
add_library(core
  event_handler.cc
)

target_include_directories(core
  PUBLIC ${PROJECT_SOURCE_DIR}/src
)

target_link_libraries(core
  PRIVATE project_warnings
)
```

- 라이브러리는 모듈 단위로 분리한다.
- `target_*` 명령어를 사용한다 (전역 `include_directories()` 금지).
- `PUBLIC`/`PRIVATE`/`INTERFACE` 스코프를 명확히 지정한다.

## 테스트 CMake

```cmake
# tests/CMakeLists.txt
enable_testing()

function(add_unit_test TEST_NAME TEST_SOURCE)
  add_executable(${TEST_NAME} ${TEST_SOURCE})
  target_link_libraries(${TEST_NAME}
    PRIVATE
      GTest::gtest_main
      GTest::gmock
      ${ARGN}  # 추가 라이브러리
  )
  gtest_discover_tests(${TEST_NAME})
endfunction()

add_unit_test(event_handler_test core/event_handler_test.cc core)
add_unit_test(webhook_client_test webhook/webhook_client_test.cc webhook)
```

- `gtest_discover_tests()`로 CTest 자동 등록.
- 테스트별 실행파일 또는 모듈별 통합 실행파일 선택 가능.

## 빌드 명령어

```bash
# 설정 (Debug)
cmake -B build -DCMAKE_BUILD_TYPE=Debug

# 설정 (Release)
cmake -B build -DCMAKE_BUILD_TYPE=Release

# 빌드
cmake --build build -j$(nproc)

# 테스트 실행
cd build && ctest --output-on-failure

# 경고를 에러로 (CI용)
cmake -B build -DWARNINGS_AS_ERRORS=ON
```

- out-of-source 빌드 필수 (`build/` 디렉토리).
- `build/` 디렉토리는 `.gitignore`에 추가한다.

## 금지 사항

- in-source 빌드 금지 (`cmake .` 대신 `cmake -B build`).
- 전역 `include_directories()`, `link_libraries()` 금지.
- `file(GLOB ...)` 으로 소스 파일 수집 금지 (명시적 나열).
- 절대 경로 하드코딩 금지.
- `CMAKE_CXX_FLAGS`에 직접 추가 금지 (`target_compile_options` 사용).
