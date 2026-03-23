# C++ Style Rules

> Based on the Google C++ Style Guide. Uses the C++20 standard.

## Core Principles

- Follow the [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html) as the baseline.
- Actively leverage C++20 features.
- This document specifies only project-specific adjustments to the Google style.

## Naming

| Target | Convention | Example |
|--------|-----------|---------|
| File | `snake_case.cc` / `snake_case.h` | `event_handler.cc`, `event_handler.h` |
| Class/Struct | `PascalCase` | `EventHandler`, `WebhookClient` |
| Function | `PascalCase` | `SendMessage()`, `BuildPayload()` |
| Variable | `snake_case` | `event_type`, `retry_count` |
| Member variable | `snake_case_` (trailing underscore) | `base_url_`, `timeout_` |
| Constant | `kPascalCase` | `kMaxRetries`, `kDefaultTimeout` |
| Macro | `UPPER_SNAKE_CASE` | `HOOSIKI_VERSION_MAJOR` |
| Namespace | `snake_case` | `hoosiki::webhook` |
| Enum value | `kPascalCase` | `kSuccess`, `kNotFound` |
| Template parameter | `PascalCase` | `typename Container`, `typename ValueType` |
| Concept | `PascalCase` | `Sendable`, `Hashable` |

## File Structure

### Header Files (.h)

```cpp
#ifndef HOOSIKI_MODULE_NAME_H_
#define HOOSIKI_MODULE_NAME_H_

// 1. C system headers
#include <cstdint>

// 2. C++ standard library
#include <string>
#include <vector>

// 3. Third-party libraries
#include "gtest/gtest.h"

// 4. Project headers
#include "hoosiki/core/types.h"

namespace hoosiki::module {

class ClassName {
 public:
  // Constructors, destructor
  // Public methods

 private:
  // Private methods
  // Member variables
};

}  // namespace hoosiki::module

#endif  // HOOSIKI_MODULE_NAME_H_
```

- Use traditional include guards instead of `#pragma once` (Google style).
- One blank line between include groups.

### Source Files (.cc)

```cpp
#include "hoosiki/module/class_name.h"  // Corresponding header first

#include <algorithm>

#include "hoosiki/core/logging.h"

namespace hoosiki::module {

// Implementation

}  // namespace hoosiki::module
```

## Formatting

- Indentation: 2 spaces
- Max line length: 80 characters
- Braces: K&R style (opening brace on the same line)
- Auto-format with `clang-format` (`.clang-format` with `BasedOnStyle: Google`)

Recommended `.clang-format`:

```yaml
BasedOnStyle: Google
ColumnLimit: 80
IndentWidth: 2
PointerAlignment: Left
DerivePointerAlignment: false
AllowShortFunctionsOnASingleLine: Inline
```

## `auto` Usage Policy

- Use `auto` when the type is obvious from the right-hand side.
- Do not use `auto` when it obscures the type and harms readability.
- Always use `auto` for iterator types, lambda captures, and `make_unique`/`make_shared` results.

```cpp
// Good — type is obvious
auto handler = std::make_unique<EventHandler>(config);
auto it = container.begin();
auto callback = [](int x) { return x * 2; };

// Good — structured bindings
auto [key, value] = *map.begin();

// Bad — type is unclear
auto result = Process(input);  // What type is result?

// Good — explicit type when clarity matters
StatusCode result = Process(input);
```

## Const Correctness

- Mark everything `const` by default. Remove `const` only when mutation is needed.
- Use `const` for local variables that are not modified.
- Use `const&` for function parameters that are not modified.
- Use `constexpr` for values computable at compile time.
- Mark member functions `const` if they do not modify state.

```cpp
// Good — const by default
const auto config = LoadConfig("path");
const std::string& name = config.name();

void PrintReport(const Report& report);  // Does not modify report

class Cache {
 public:
  [[nodiscard]] size_t Size() const { return entries_.size(); }
  void Clear() { entries_.clear(); }  // Mutates, not const

 private:
  std::vector<Entry> entries_;
};
```

## C++20 Features

### Actively Use

- `std::format` — Type-safe string formatting
- `std::span` — Non-owning view over contiguous memory
- Concepts — Template constraints
- `constexpr` extensions — constexpr virtual functions, constexpr dynamic memory
- `consteval` — Guaranteed compile-time evaluation
- `constinit` — Guaranteed constant initialization (avoids static init order fiasco)
- Designated initializers
- `std::ranges` algorithms and views
- Three-way comparison (`<=>`)
- `[[nodiscard]]`, `[[nodiscard("reason")]]`, `[[likely]]`, `[[unlikely]]`
- `std::jthread` — Auto-joining, cooperative-cancellation thread

### Usage Examples

```cpp
// Concepts
template <std::integral T>
[[nodiscard]] T SafeAdd(T a, T b);

// Custom concept
template <typename T>
concept Sendable = requires(T t, std::string msg) {
  { t.Send(msg) } -> std::convertible_to<bool>;
};

template <Sendable T>
void Notify(T& sender, std::string_view message);

// Ranges
auto filtered = items | std::views::filter([](const auto& item) {
  return item.IsValid();
}) | std::views::transform([](const auto& item) {
  return item.Name();
});

// Designated initializers
const WebhookConfig config{
    .url = "https://example.com",
    .timeout = 30,
    .retry_count = 3,
};

// std::format
auto msg = std::format("[{}] {}: {}", hostname, project, message);

// consteval — must be evaluated at compile time
consteval int Square(int n) { return n * n; }
static_assert(Square(5) == 25);

// constinit — guaranteed constant initialization
constinit int global_counter = 0;

// [[nodiscard("reason")]]
[[nodiscard("Ignoring error status may cause silent failures")]]
StatusCode SendWebhook(const WebhookConfig& config);

// std::jthread with stop token
std::jthread worker([](std::stop_token stoken) {
  while (!stoken.stop_requested()) {
    // Do work
  }
});
```

## Class Design

- Default to the **Rule of Zero** (do not define special member functions).
- Use the **Rule of Five** when manual resource management is needed.
- Classes with virtual methods: `virtual ~ClassName() = default;`
- Single-parameter constructors must be `explicit`.
- Use `= delete` to explicitly prohibit copy/move.
- Prefer composition over inheritance.
- Mark non-overridable virtual methods as `final`.

```cpp
// Rule of Zero — let the compiler generate everything
class EventHandler {
 public:
  explicit EventHandler(WebhookConfig config) : config_(std::move(config)) {}

  [[nodiscard]] Status ProcessEvent(const Event& event) const;

 private:
  WebhookConfig config_;  // std::string members handle their own resources
};

// Explicitly non-copyable, movable
class Connection {
 public:
  Connection(Connection&&) noexcept = default;
  Connection& operator=(Connection&&) noexcept = default;
  Connection(const Connection&) = delete;
  Connection& operator=(const Connection&) = delete;
};
```

## Error Handling

- Prefer return values over exceptions for expected errors.
- Use `std::expected<T, E>` (C++23) or a project-level `Result<T, E>` type.
- Use exceptions only for truly exceptional, unrecoverable situations.
- Always use `[[nodiscard]]` on functions that return error codes.

```cpp
// Good — error as value (C++23 or polyfill)
[[nodiscard]] std::expected<Config, std::string> LoadConfig(
    const std::filesystem::path& path);

// Good — enum error codes
enum class StatusCode { kOk, kNotFound, kTimeout, kInvalidArgument };

[[nodiscard]] StatusCode SendWebhook(const WebhookConfig& config);

// Caller must handle the result
auto result = LoadConfig("config.json");
if (!result.has_value()) {
  LOG(ERROR) << "Failed to load config: " << result.error();
  return;
}
const auto& config = result.value();
```

## Documentation

- Use `///` Doxygen-style comments for public APIs.
- Document all public classes, functions, and enums.
- Include `@param`, `@return`, `@throws` where applicable.
- Add `@code` / `@endcode` blocks for usage examples.

```cpp
/// Sends a message to the configured webhook endpoint.
///
/// @param config The webhook configuration.
/// @param message The message body to send.
/// @return kOk on success, or an error status code.
///
/// @code
///   const WebhookConfig config{.url = "https://example.com", .timeout = 30};
///   auto status = SendWebhook(config, "deploy complete");
///   if (status != StatusCode::kOk) { /* handle error */ }
/// @endcode
[[nodiscard]] StatusCode SendWebhook(const WebhookConfig& config,
                                     std::string_view message);
```

## Prohibited

- No `using namespace std;` (absolutely forbidden in headers, discouraged in source files).
- No C-style casts. Use `static_cast`, `dynamic_cast`, `reinterpret_cast`.
- No `goto`.
- No macro abuse. Replace with `constexpr`, `consteval`, `inline`, or templates.
- No direct `new`/`delete`. Use smart pointers (see memory-safety.md).
- No global mutable variables (constants are allowed).
- No implicit conversions via non-explicit single-argument constructors.
- No `std::endl` (use `'\n'` — `std::endl` forces a flush).
- No `NULL`. Use `nullptr`.
