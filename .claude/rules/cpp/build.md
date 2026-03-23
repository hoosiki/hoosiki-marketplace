# C++ Build Rules (CMake)

> Uses CMake as the build system. C++20 standard.

## Basic Configuration

### Minimum CMake Version

```cmake
cmake_minimum_required(VERSION 3.20)
project(hoosiki
  VERSION 1.0.0
  LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Generate compile_commands.json for clangd and other tools
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
```

- Use CMake 3.20+ (C++20 module support).
- `CMAKE_CXX_EXTENSIONS OFF` disables GNU extensions.
- `CMAKE_EXPORT_COMPILE_COMMANDS ON` enables IDE/LSP integration.

## Project Directory Layout

```
project/
├── CMakeLists.txt              # Root CMake
├── CMakePresets.json            # Build presets (debug, release, CI)
├── cmake/
│   ├── CompilerWarnings.cmake  # Warning options
│   ├── Sanitizers.cmake        # Sanitizer configurations
│   └── Dependencies.cmake      # External dependencies (FetchContent)
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
├── .clang-format               # Formatting rules
├── .clang-tidy                 # Static analysis rules
└── build/                      # Build directory (gitignored)
```

## CMake Presets

Use `CMakePresets.json` for reproducible builds:

```json
{
  "version": 6,
  "configurePresets": [
    {
      "name": "debug",
      "displayName": "Debug",
      "binaryDir": "${sourceDir}/build/debug",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Debug",
        "CMAKE_EXPORT_COMPILE_COMMANDS": "ON"
      }
    },
    {
      "name": "release",
      "displayName": "Release",
      "binaryDir": "${sourceDir}/build/release",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Release"
      }
    },
    {
      "name": "ci",
      "displayName": "CI Build",
      "inherits": "debug",
      "cacheVariables": {
        "WARNINGS_AS_ERRORS": "ON",
        "ENABLE_SANITIZERS": "ON"
      }
    }
  ],
  "buildPresets": [
    {
      "name": "debug",
      "configurePreset": "debug"
    },
    {
      "name": "release",
      "configurePreset": "release"
    }
  ],
  "testPresets": [
    {
      "name": "debug",
      "configurePreset": "debug",
      "output": { "outputOnFailure": true }
    }
  ]
}
```

## Compiler Warnings

`cmake/CompilerWarnings.cmake`:

```cmake
add_library(project_warnings INTERFACE)

target_compile_options(project_warnings INTERFACE
  $<$<CXX_COMPILER_ID:GNU,Clang,AppleClang>:
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
    -Wmisleading-indentation
    -Wduplicated-cond
    -Wduplicated-branches
    -Wlogical-op
  >
  $<$<CXX_COMPILER_ID:MSVC>:
    /W4
    /permissive-
    /w14640
    /w14242
    /w14254
    /w14263
    /w14265
    /w14287
  >
)

# Treat warnings as errors in CI
option(WARNINGS_AS_ERRORS "Treat warnings as errors" OFF)
if(WARNINGS_AS_ERRORS)
  target_compile_options(project_warnings INTERFACE
    $<$<CXX_COMPILER_ID:GNU,Clang,AppleClang>:-Werror>
    $<$<CXX_COMPILER_ID:MSVC>:/WX>
  )
endif()
```

- Warnings only during development, `-Werror` in CI.
- Cross-platform support using generator expressions.

## Sanitizers

`cmake/Sanitizers.cmake`:

```cmake
option(ENABLE_SANITIZERS "Enable sanitizers" OFF)

if(ENABLE_SANITIZERS)
  add_library(project_sanitizers INTERFACE)

  set(SANITIZER_FLAGS "-fsanitize=address,undefined -fno-omit-frame-pointer")
  target_compile_options(project_sanitizers INTERFACE ${SANITIZER_FLAGS})
  target_link_options(project_sanitizers INTERFACE ${SANITIZER_FLAGS})
endif()
```

## External Dependency Management

`cmake/Dependencies.cmake`:

```cmake
include(FetchContent)

# Google Test
FetchContent_Declare(
  googletest
  GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_TAG v1.15.2
  FIND_PACKAGE_ARGS  # Prefer system install if available
)
FetchContent_MakeAvailable(googletest)

# fmt (if std::format is not available)
FetchContent_Declare(
  fmt
  GIT_REPOSITORY https://github.com/fmtlib/fmt.git
  GIT_TAG 11.1.4
)
FetchContent_MakeAvailable(fmt)
```

- Use `FetchContent` for dependency management (no system install dependency).
- Pin versions with git tags.
- Use `FIND_PACKAGE_ARGS` to prefer system packages when available.
- `find_package()` is used only for system-level libraries.
- Alternative: vcpkg or Conan for larger projects with many dependencies.

## Library / Executable Definitions

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
  $<$<BOOL:${ENABLE_SANITIZERS}>:project_sanitizers>
)
```

- Split libraries by module.
- Use `target_*` commands (no global `include_directories()`).
- Clearly specify `PUBLIC`/`PRIVATE`/`INTERFACE` scope.

## Test CMake

```cmake
# tests/CMakeLists.txt
include(GoogleTest)
enable_testing()

function(add_unit_test TEST_NAME TEST_SOURCE)
  add_executable(${TEST_NAME} ${TEST_SOURCE})
  target_link_libraries(${TEST_NAME}
    PRIVATE
      GTest::gtest_main
      GTest::gmock
      project_warnings
      ${ARGN}  # Additional libraries
  )
  gtest_discover_tests(${TEST_NAME}
    DISCOVERY_TIMEOUT 30
    PROPERTIES
      TIMEOUT 60
  )
endfunction()

add_unit_test(event_handler_test core/event_handler_test.cc core)
add_unit_test(webhook_client_test webhook/webhook_client_test.cc webhook)
```

- Use `gtest_discover_tests()` for automatic CTest registration.
- Set `DISCOVERY_TIMEOUT` and per-test `TIMEOUT` to catch hanging tests.
- Link `project_warnings` to test targets too.

## Static Analysis (clang-tidy)

Recommended `.clang-tidy` configuration:

```yaml
Checks: >
  -*,
  bugprone-*,
  clang-analyzer-*,
  cppcoreguidelines-*,
  modernize-*,
  performance-*,
  readability-*,
  -modernize-use-trailing-return-type,
  -readability-identifier-length

WarningsAsErrors: ''
HeaderFilterRegex: 'src/.*'
```

Integrate with CMake:

```cmake
option(ENABLE_CLANG_TIDY "Enable clang-tidy" OFF)
if(ENABLE_CLANG_TIDY)
  find_program(CLANG_TIDY_EXE clang-tidy)
  if(CLANG_TIDY_EXE)
    set(CMAKE_CXX_CLANG_TIDY ${CLANG_TIDY_EXE})
  endif()
endif()
```

## Build Commands

```bash
# Using presets (recommended)
cmake --preset debug
cmake --build --preset debug
ctest --preset debug

# Manual — Debug
cmake -B build -DCMAKE_BUILD_TYPE=Debug

# Manual — Release
cmake -B build -DCMAKE_BUILD_TYPE=Release

# Build (use nproc on Linux, sysctl on macOS)
cmake --build build -j$(nproc 2>/dev/null || sysctl -n hw.ncpu)

# Run tests
cd build && ctest --output-on-failure

# CI build with warnings-as-errors and sanitizers
cmake -B build -DWARNINGS_AS_ERRORS=ON -DENABLE_SANITIZERS=ON
```

- Out-of-source builds are mandatory (`build/` directory).
- Add `build/` to `.gitignore`.

## Prohibited

- No in-source builds (`cmake .` — use `cmake -B build`).
- No global `include_directories()` or `link_libraries()`.
- No `file(GLOB ...)` for source file collection (list files explicitly).
- No hardcoded absolute paths.
- No direct modification of `CMAKE_CXX_FLAGS` (use `target_compile_options`).
- No `add_definitions()` (use `target_compile_definitions`).
- No `link_directories()` (use `target_link_libraries` with full paths or imported targets).
