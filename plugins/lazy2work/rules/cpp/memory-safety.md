---
paths:
  - "**/*.cpp"
  - "**/*.cc"
  - "**/*.cxx"
  - "**/*.h"
  - "**/*.hpp"
  - "**/*.hxx"
---

# C++ Memory Safety Rules

> RAII and smart pointer-centric memory safety rules. Based on C++20.

## Core Principles

- **RAII (Resource Acquisition Is Initialization)** is the foundation for all resource management.
- Never use `new`/`delete` directly.
- Express ownership explicitly through types.
- Prefer value semantics. Use the heap only when necessary.

## Smart Pointers

### Ownership Model

| Pointer | Ownership | When to Use |
|---------|-----------|-------------|
| `std::unique_ptr<T>` | Exclusive | Default choice. Most dynamic allocations |
| `std::shared_ptr<T>` | Shared | Only when true shared ownership is needed |
| `T*` (raw pointer) | Non-owning | Observer that does not own. Nullable reference |
| `T&` (reference) | Non-owning | Observer that does not own. Guaranteed non-null |
| `std::weak_ptr<T>` | Weak | Breaking `shared_ptr` circular references |

### Decision Flowchart

```
Need dynamic allocation?
├── No → Use value semantics (stack allocation)
└── Yes → Does ownership transfer?
    ├── Single owner → std::unique_ptr
    └── Multiple owners → std::shared_ptr
        └── Observer only → raw T* or T&
            └── Need to check if alive → std::weak_ptr
```

### Usage Rules

```cpp
// Good — unique_ptr for exclusive ownership
auto handler = std::make_unique<EventHandler>(config);

// Good — ownership transfer
void RegisterHandler(std::unique_ptr<EventHandler> handler);
registry.RegisterHandler(std::move(handler));

// Good — non-owning reference (raw pointer or reference)
void ProcessEvent(const EventHandler& handler, const Event& event);
EventHandler* FindHandler(const std::string& name);  // nullable

// Bad — direct new/delete
EventHandler* handler = new EventHandler(config);
delete handler;

// Bad — unnecessary shared_ptr
auto handler = std::make_shared<EventHandler>(config);  // unique_ptr if not shared
```

### Factory Functions

```cpp
// Good — always use make functions
auto ptr = std::make_unique<MyClass>(arg1, arg2);
auto sptr = std::make_shared<MyClass>(arg1, arg2);

// Bad — exception safety issue possible
std::unique_ptr<MyClass> ptr(new MyClass(arg1, arg2));
```

## Value Semantics First

Prefer stack allocation and value types. Use dynamic allocation only when needed:

```cpp
// Good — value on stack
EventHandler handler(config);

// Good — value in container
std::vector<Event> events;
events.emplace_back("webhook", "test data");

// Good — return by value (NRVO applies)
EventHandler CreateHandler(const Config& config) {
  EventHandler handler(config);
  handler.Initialize();
  return handler;  // Move or NRVO, no copy
}

// Bad — unnecessary heap allocation
auto handler = std::make_unique<EventHandler>(config);  // Stack is fine here
```

## Containers and std::span

```cpp
// Good — std::span for non-owning view of contiguous memory
void ProcessItems(std::span<const Item> items);

// Good — container manages memory
std::vector<Item> items;
items.emplace_back(Item{.name = "test"});

// Good — fixed-size array
std::array<int, 4> values = {1, 2, 3, 4};

// Bad — C-style array with size parameter
void ProcessItems(const Item* items, size_t count);
```

- Use `std::span` for non-owning contiguous memory references.
- Use `std::vector` for dynamic arrays.
- Use `std::array` for fixed-size arrays.
- C-style arrays (`T[]`, `T*` + size) are prohibited.

## Strings

```cpp
// Good — std::string owns, std::string_view references
std::string BuildMessage(std::string_view hostname, std::string_view project);

// Good — store as string, pass as string_view
class Config {
 public:
  explicit Config(std::string name) : name_(std::move(name)) {}
  [[nodiscard]] std::string_view Name() const { return name_; }

 private:
  std::string name_;  // Owns the string
};

// Bad — manual C string management
char* message = (char*)malloc(256);
sprintf(message, "[%s] %s", hostname, project);
free(message);
```

- Owning strings: `std::string`
- Non-owning string references: `std::string_view`
- Manual `char*` management is prohibited.
- **Warning**: Never store `std::string_view` that outlives the referenced string.

## Optional and Expected

### std::optional — Nullable Values

```cpp
// Good — optional to express "value may not exist"
[[nodiscard]] std::optional<Config> LoadConfig(const std::string& path);

auto config = LoadConfig("config.json");
if (config.has_value()) {
  Initialize(*config);
}

// Good — with value_or for defaults
const int timeout = config.value_or(DefaultConfig()).timeout;

// Bad — nullptr to represent "absent"
Config* LoadConfig(const std::string& path);  // Ownership unclear
```

### std::expected (C++23) — Error Handling

```cpp
// Good — explicit error type
[[nodiscard]] std::expected<Config, std::string> LoadConfig(
    const std::filesystem::path& path);

auto result = LoadConfig("config.json");
if (!result) {
  LOG(ERROR) << "Failed: " << result.error();
  return;
}
const auto& config = *result;

// Good — monadic operations (C++23)
auto timeout = LoadConfig("config.json")
    .transform([](const Config& c) { return c.timeout; })
    .value_or(kDefaultTimeout);
```

## RAII Patterns

### RAII Wrapper

```cpp
// File handle RAII wrapper
class FileHandle {
 public:
  explicit FileHandle(const std::filesystem::path& path)
      : file_(std::fopen(path.c_str(), "r")) {
    if (!file_) {
      throw std::runtime_error(
          std::format("Failed to open file: {}", path.string()));
    }
  }

  ~FileHandle() {
    if (file_) std::fclose(file_);
  }

  // Non-copyable, movable
  FileHandle(const FileHandle&) = delete;
  FileHandle& operator=(const FileHandle&) = delete;
  FileHandle(FileHandle&& other) noexcept
      : file_(std::exchange(other.file_, nullptr)) {}
  FileHandle& operator=(FileHandle&& other) noexcept {
    if (this != &other) {
      if (file_) std::fclose(file_);
      file_ = std::exchange(other.file_, nullptr);
    }
    return *this;
  }

  [[nodiscard]] FILE* Get() const { return file_; }

 private:
  FILE* file_;
};
```

### Scope Guard (for cleanup actions)

```cpp
// Simple scope guard for cleanup
class ScopeGuard {
 public:
  explicit ScopeGuard(std::function<void()> cleanup)
      : cleanup_(std::move(cleanup)) {}
  ~ScopeGuard() { if (cleanup_) cleanup_(); }

  ScopeGuard(const ScopeGuard&) = delete;
  ScopeGuard& operator=(const ScopeGuard&) = delete;

  void Dismiss() { cleanup_ = nullptr; }

 private:
  std::function<void()> cleanup_;
};

// Usage
void ProcessFile(const std::filesystem::path& path) {
  auto* resource = AcquireResource();
  ScopeGuard guard([resource] { ReleaseResource(resource); });

  // Work with resource...
  // Automatically released even on exception
}
```

## Concurrency Safety

### std::jthread — Preferred Thread Type

```cpp
// Good — jthread auto-joins and supports cooperative cancellation
std::jthread worker([](std::stop_token stoken) {
  while (!stoken.stop_requested()) {
    ProcessNextItem();
  }
});
// worker automatically joins when destroyed

// Bad — std::thread requires manual join
std::thread worker([] { /* ... */ });
// Forgetting worker.join() is undefined behavior
```

### Mutex and Lock Guidelines

```cpp
// Good — scoped lock
std::mutex mutex;
{
  const std::scoped_lock lock(mutex);
  shared_data.Update();
}

// Good — shared_mutex for read-heavy workloads
std::shared_mutex rw_mutex;
{
  const std::shared_lock read_lock(rw_mutex);  // Multiple readers OK
  return shared_data.Read();
}
{
  const std::unique_lock write_lock(rw_mutex);  // Exclusive writer
  shared_data.Write(new_value);
}

// Bad — manual lock/unlock
mutex.lock();
shared_data.Update();
mutex.unlock();  // Missed if exception thrown
```

## Unsafe Code Zones (Use Only When Necessary)

For external C libraries or performance-critical code:

```cpp
// Clearly isolate unsafe code and document safety invariants
// SAFETY: C library call — returned pointer is valid for the scope of `safe`
auto* raw = c_library_create();
auto safe = std::unique_ptr<CType, decltype(&c_library_destroy)>(
    raw, c_library_destroy);
```

- Document `// SAFETY:` when using raw pointers with safety justification.
- Wrap C library resources in `unique_ptr` with custom deleter immediately.

## Sanitizer Usage

Run sanitizers regularly (see build.md for CMake integration):

| Sanitizer | Detects | Flag |
|-----------|---------|------|
| AddressSanitizer (ASan) | Buffer overflows, use-after-free, double-free | `-fsanitize=address` |
| UndefinedBehaviorSanitizer (UBSan) | Signed overflow, null deref, alignment | `-fsanitize=undefined` |
| ThreadSanitizer (TSan) | Data races, deadlocks | `-fsanitize=thread` |
| MemorySanitizer (MSan) | Uninitialized reads | `-fsanitize=memory` |

- ASan + UBSan should be the default CI configuration.
- TSan should be used for concurrent code.
- ASan and TSan cannot be used together (separate CI jobs).

## Prohibited

- No direct `new`/`delete` (use `make_unique`/`make_shared`).
- No `malloc`/`free`/`realloc` (use C++ containers).
- No dangling pointers/references.
- No `std::shared_ptr` overuse (use `unique_ptr` when ownership is clear).
- No uninitialized variables.
- No C-style casts `(int)x` (use `static_cast<int>(x)`).
- No `void*` for type erasure (use `std::variant`, `std::any`, or templates).
- No `std::thread` (use `std::jthread`).
- No manual `mutex.lock()`/`mutex.unlock()` (use `scoped_lock` / `unique_lock`).
- No storing `std::string_view` beyond the lifetime of the source string.
