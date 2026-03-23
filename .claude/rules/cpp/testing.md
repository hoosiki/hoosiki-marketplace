# C++ Testing Rules (Google Test)

> TDD-based testing. Uses Google Test as the test framework.

## Core Principle: Red-Green-Refactor

1. **Red** — Write a failing test first
2. **Green** — Write the minimum code to make the test pass
3. **Refactor** — Clean up the code while keeping tests passing

## Directory Structure

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
│   ├── webhook/
│   │   └── webhook_client_test.cc
│   └── test_main.cc            # Optional custom main
├── CMakeLists.txt
└── tests/CMakeLists.txt
```

- Test files go in `tests/` mirroring the source directory structure.
- Test file naming: `{source_file}_test.cc`
- Maintain a 1:1 mapping between source files and test files.

## Test Writing Rules

### Basic Structure

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

  void TearDown() override {
    // Cleanup if needed
  }

  std::unique_ptr<EventHandler> handler_;
};

// Test naming: TestSuite / Action_Condition_ExpectedResult
TEST_F(EventHandlerTest, ProcessEvent_WithValidPayload_ReturnsSuccess) {
  // Arrange
  const Event event{.type = "webhook", .data = "test"};

  // Act
  const auto result = handler_->ProcessEvent(event);

  // Assert
  EXPECT_EQ(result, Status::kSuccess);
}

TEST_F(EventHandlerTest, ProcessEvent_WithEmptyData_ReturnsInvalidArgument) {
  const Event event{.type = "webhook", .data = ""};

  const auto result = handler_->ProcessEvent(event);

  EXPECT_EQ(result, Status::kInvalidArgument);
}

}  // namespace
}  // namespace hoosiki::core
```

### Naming Conventions

- Test Suite: `{ClassName}Test` or `{FeatureName}Test`
- Test Case: `{Action}_{Condition}_{ExpectedResult}`
- All test names must clearly express the test intent.

### Assertion Guide

```cpp
// Value comparison
EXPECT_EQ(actual, expected);   // ==
EXPECT_NE(actual, expected);   // !=
EXPECT_LT(actual, expected);   // <
EXPECT_LE(actual, expected);   // <=
EXPECT_GT(actual, expected);   // >
EXPECT_GE(actual, expected);   // >=

// Boolean
EXPECT_TRUE(condition);
EXPECT_FALSE(condition);

// String
EXPECT_STREQ(actual, expected);
EXPECT_THAT(str, ::testing::HasSubstr("partial"));
EXPECT_THAT(str, ::testing::StartsWith("prefix"));
EXPECT_THAT(str, ::testing::MatchesRegex("pattern.*"));

// Floating point (with tolerance)
EXPECT_FLOAT_EQ(actual, expected);
EXPECT_DOUBLE_EQ(actual, expected);
EXPECT_NEAR(actual, expected, tolerance);

// Container matchers
EXPECT_THAT(vec, ::testing::ElementsAre(1, 2, 3));
EXPECT_THAT(vec, ::testing::Contains(42));
EXPECT_THAT(vec, ::testing::IsEmpty());
EXPECT_THAT(vec, ::testing::SizeIs(3));
EXPECT_THAT(map, ::testing::UnorderedElementsAre(
    ::testing::Pair("key1", "val1"),
    ::testing::Pair("key2", "val2")));

// Exceptions
EXPECT_THROW(statement, ExceptionType);
EXPECT_THROW(statement, std::runtime_error);
EXPECT_NO_THROW(statement);
EXPECT_ANY_THROW(statement);

// Fatal assertions (abort test on failure) — use for preconditions
ASSERT_NE(ptr, nullptr);  // Subsequent code dereferences ptr
ptr->DoSomething();
```

- Generally use `EXPECT_*` (allows multiple checks per test).
- Use `ASSERT_*` only for preconditions that subsequent code depends on.
- Prefer `EXPECT_THAT` with matchers for complex assertions — they produce better error messages.

## Google Mock

```cpp
#include <gmock/gmock.h>

class MockHttpClient : public HttpClientInterface {
 public:
  MOCK_METHOD(StatusCode, Post,
              (const std::string& url, const std::string& body), (override));
  MOCK_METHOD(StatusCode, Get,
              (const std::string& url), (override, const));
  MOCK_METHOD(void, SetTimeout, (int seconds), (override));
};

TEST_F(WebhookClientTest, Send_CallsPostWithCorrectUrl) {
  MockHttpClient mock_client;
  WebhookClient webhook(&mock_client);

  EXPECT_CALL(mock_client, Post("https://example.com/hook", ::testing::_))
      .WillOnce(::testing::Return(StatusCode::kOk));

  const auto result = webhook.Send("test message");

  EXPECT_EQ(result, Status::kSuccess);
}

// Verify call ordering
TEST_F(WebhookClientTest, Send_SetsTimeoutBeforePost) {
  ::testing::InSequence seq;
  MockHttpClient mock_client;
  WebhookClient webhook(&mock_client);

  EXPECT_CALL(mock_client, SetTimeout(30));
  EXPECT_CALL(mock_client, Post(::testing::_, ::testing::_))
      .WillOnce(::testing::Return(StatusCode::kOk));

  webhook.Send("test");
}
```

- Extract interfaces and replace external dependencies (network, filesystem) with mocks.
- Use `EXPECT_CALL` for invocation verification, `WillOnce`/`WillRepeatedly` for return values.
- Use `::testing::InSequence` to verify call ordering when it matters.
- Prefer `NiceMock<T>` to suppress uninteresting call warnings when appropriate.

## Parameterized Tests

```cpp
struct UrlTestCase {
  std::string url;
  bool expected;
  std::string description;  // For readable test names
};

class ValidateUrlTest : public ::testing::TestWithParam<UrlTestCase> {};

TEST_P(ValidateUrlTest, ReturnsExpectedResult) {
  const auto& [url, expected, description] = GetParam();
  EXPECT_EQ(ValidateUrl(url), expected) << "Failed for: " << description;
}

INSTANTIATE_TEST_SUITE_P(
    UrlValidation, ValidateUrlTest,
    ::testing::Values(
        UrlTestCase{"https://example.com", true, "https valid"},
        UrlTestCase{"http://example.com/path", true, "http with path"},
        UrlTestCase{"ftp://example.com", false, "ftp invalid"},
        UrlTestCase{"not-a-url", false, "no scheme"},
        UrlTestCase{"", false, "empty string"}
    ),
    [](const ::testing::TestParamInfo<UrlTestCase>& info) {
      // Generate readable test names
      std::string name = info.param.description;
      std::replace(name.begin(), name.end(), ' ', '_');
      return name;
    });
```

- Use structs for test parameters to improve readability.
- Provide a custom name generator for meaningful test output.

## Typed Tests

Use when testing generic code across multiple types:

```cpp
template <typename T>
class ContainerTest : public ::testing::Test {
 protected:
  T container_;
};

using ContainerTypes = ::testing::Types<std::vector<int>, std::deque<int>, std::list<int>>;
TYPED_TEST_SUITE(ContainerTest, ContainerTypes);

TYPED_TEST(ContainerTest, IsEmptyInitially) {
  EXPECT_TRUE(this->container_.empty());
}

TYPED_TEST(ContainerTest, SizeAfterPushBack) {
  this->container_.push_back(42);
  EXPECT_EQ(this->container_.size(), 1);
}
```

## Death Tests

For testing that code correctly aborts, asserts, or exits:

```cpp
TEST(PreconditionTest, NullPointerAborts) {
  EXPECT_DEATH(ProcessEvent(nullptr), ".*null.*");
}

TEST(ConfigTest, InvalidConfigExits) {
  EXPECT_EXIT(LoadConfigOrDie("nonexistent.json"),
              ::testing::ExitedWithCode(1),
              "Failed to load");
}
```

- Place death tests in a separate test suite suffixed with `DeathTest`.
- Death tests run in a subprocess — keep them fast and isolated.

## Running Tests

```bash
# Run all tests
cd build && ctest --output-on-failure

# Run with verbose output
cd build && ctest --output-on-failure -V

# Filter specific tests
./tests/all_tests --gtest_filter="EventHandlerTest.*"

# Run a single test
./tests/all_tests --gtest_filter="EventHandlerTest.ProcessEvent_WithValidPayload_ReturnsSuccess"

# Repeat tests to detect flakiness
./tests/all_tests --gtest_repeat=10 --gtest_shuffle

# Output timing information
./tests/all_tests --gtest_print_time=1

# Output as JUnit XML (for CI)
./tests/all_tests --gtest_output=xml:report.xml
```

## Sanitizer Integration

Always run tests with sanitizers in CI:

```bash
# AddressSanitizer — detects buffer overflows, use-after-free
cmake -B build -DCMAKE_CXX_FLAGS="-fsanitize=address -fno-omit-frame-pointer"

# UndefinedBehaviorSanitizer — detects undefined behavior
cmake -B build -DCMAKE_CXX_FLAGS="-fsanitize=undefined"

# ThreadSanitizer — detects data races
cmake -B build -DCMAKE_CXX_FLAGS="-fsanitize=thread"

# Combined ASan + UBSan (recommended default for CI)
cmake -B build -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer"
```

## Coverage

Generate coverage reports with `gcov` / `llvm-cov`:

```bash
# Build with coverage instrumentation
cmake -B build -DCMAKE_CXX_FLAGS="--coverage" -DCMAKE_BUILD_TYPE=Debug

# Run tests
cd build && ctest

# Generate report (gcovr)
gcovr --root .. --html --html-details -o coverage.html

# Or with llvm-cov
llvm-cov report ./tests/all_tests -instr-profile=default.profdata
```

## Test Coverage Requirements

- Every public method must have at least one test.
- Test both happy paths and error paths.
- Include boundary values and edge cases.
- Each test verifies a single behavior.
- Follow the Arrange-Act-Assert (AAA) pattern.

## Implementation Workflow

### Adding a New Feature

```
1. Analyze requirements
2. Create test file → write a failing test (Red)
3. Run ctest → verify build failure or test failure
4. Write the minimum implementation code (Green)
5. Run ctest → verify test passes
6. Refactor the code (Refactor)
7. Run ctest → verify tests still pass
```

### Fixing a Bug

```
1. Write a test that reproduces the bug (Red)
2. Run ctest → verify test failure
3. Fix the bug (Green)
4. Run ctest → verify test passes
```

## Prohibited

- Do not commit new C++ code without tests.
- Do not commit with `DISABLED_` tests without a clear reason comment.
- Do not make real network calls or filesystem access in tests (use mocks).
- Do not use `sleep()` in tests.
- Do not create state sharing or execution order dependencies between tests.
- Do not use `ASSERT_*` where `EXPECT_*` suffices — prefer non-fatal assertions.
- Do not test private methods directly — test through the public interface.
