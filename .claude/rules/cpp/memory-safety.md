# C++ Memory Safety Rules

> RAII와 스마트 포인터 중심의 메모리 안전성 규칙. C++20 기준.

## 핵심 원칙

- **RAII (Resource Acquisition Is Initialization)** 를 모든 리소스 관리의 기본으로 한다.
- `new`/`delete`를 직접 사용하지 않는다.
- 소유권(ownership)을 타입으로 명시한다.

## 스마트 포인터

### 소유권 모델

| 포인터 | 소유권 | 사용 시점 |
|--------|--------|-----------|
| `std::unique_ptr<T>` | 단독 소유 | 기본 선택. 대부분의 동적 할당 |
| `std::shared_ptr<T>` | 공유 소유 | 진짜 공유 소유가 필요할 때만 |
| `T*` (raw pointer) | 비소유 참조 | 소유하지 않는 관찰자. nullable 참조 |
| `T&` (reference) | 비소유 참조 | 소유하지 않는 관찰자. non-null 보장 |
| `std::weak_ptr<T>` | 약한 참조 | `shared_ptr` 순환 참조 방지 |

### 사용 규칙

```cpp
// Good — unique_ptr로 소유권 명시
auto handler = std::make_unique<EventHandler>(config);

// Good — 소유권 이전
void RegisterHandler(std::unique_ptr<EventHandler> handler);
registry.RegisterHandler(std::move(handler));

// Good — 비소유 참조 (raw pointer 또는 reference)
void ProcessEvent(const EventHandler& handler, const Event& event);
EventHandler* FindHandler(const std::string& name);  // nullable

// Bad — new/delete 직접 사용
EventHandler* handler = new EventHandler(config);
delete handler;

// Bad — 불필요한 shared_ptr
auto handler = std::make_shared<EventHandler>(config);  // 공유 필요 없으면 unique_ptr
```

### make 함수 사용

```cpp
// Good
auto ptr = std::make_unique<MyClass>(arg1, arg2);
auto sptr = std::make_shared<MyClass>(arg1, arg2);

// Bad — 예외 안전성 문제 가능
std::unique_ptr<MyClass> ptr(new MyClass(arg1, arg2));
```

## 컨테이너와 std::span

```cpp
// Good — std::span으로 배열/버퍼 전달 (소유하지 않음)
void ProcessItems(std::span<const Item> items);

// Good — 컨테이너가 메모리 관리
std::vector<Item> items;
items.push_back(Item{.name = "test"});

// Bad — C 스타일 배열과 크기 전달
void ProcessItems(const Item* items, size_t count);
```

- 연속 메모리 참조에는 `std::span` 사용.
- 동적 배열에는 `std::vector` 사용.
- 고정 크기 배열에는 `std::array` 사용.
- C 스타일 배열 (`T[]`, `T*` + size) 금지.

## 문자열

```cpp
// Good — std::string 소유, std::string_view 참조
std::string BuildMessage(std::string_view hostname, std::string_view project);

// Bad — C 문자열 직접 관리
char* message = (char*)malloc(256);
sprintf(message, "[%s] %s", hostname, project);
free(message);
```

- 소유하는 문자열: `std::string`
- 참조하는 문자열: `std::string_view`
- `char*` 직접 관리 금지.

## 리소스 관리 패턴

### RAII 래퍼

```cpp
// 파일 핸들 RAII 래퍼
class FileHandle {
 public:
  explicit FileHandle(const std::filesystem::path& path)
      : file_(std::fopen(path.c_str(), "r")) {
    if (!file_) throw std::runtime_error("Failed to open file");
  }

  ~FileHandle() {
    if (file_) std::fclose(file_);
  }

  // 복사 금지, 이동 허용
  FileHandle(const FileHandle&) = delete;
  FileHandle& operator=(const FileHandle&) = delete;
  FileHandle(FileHandle&& other) noexcept : file_(std::exchange(other.file_, nullptr)) {}
  FileHandle& operator=(FileHandle&& other) noexcept {
    if (this != &other) {
      if (file_) std::fclose(file_);
      file_ = std::exchange(other.file_, nullptr);
    }
    return *this;
  }

 private:
  FILE* file_;
};
```

### std::optional로 nullable 대체

```cpp
// Good — optional로 "값이 없을 수 있음" 표현
std::optional<Config> LoadConfig(const std::string& path);

auto config = LoadConfig("config.json");
if (config.has_value()) {
  Initialize(*config);
}

// Bad — nullptr로 "없음" 표현
Config* LoadConfig(const std::string& path);  // 소유권 불명확
```

## 위험 구역 (필요 시에만)

외부 C 라이브러리나 성능 최적화가 필요한 경우:

```cpp
// 위험한 코드를 명확히 격리하고 주석을 단다
// SAFETY: C 라이브러리 호출 — 반환된 포인터는 이 스코프에서만 유효
auto* raw = c_library_create();
auto safe = std::unique_ptr<CType, decltype(&c_library_destroy)>(
    raw, c_library_destroy);
```

- raw pointer 사용 시 `// SAFETY:` 주석으로 안전성 근거를 명시한다.
- C 라이브러리 자원은 커스텀 deleter를 가진 `unique_ptr`로 즉시 감싼다.

## 금지 사항

- `new`/`delete` 직접 사용 금지 (`make_unique`/`make_shared` 사용).
- `malloc`/`free`/`realloc` 금지 (C++ 컨테이너 사용).
- dangling pointer/reference 생성 금지.
- `std::shared_ptr` 남용 금지 (소유권이 명확하면 `unique_ptr`).
- 초기화하지 않은 변수 사용 금지.
- C 스타일 캐스트 `(int)x` 금지 (`static_cast<int>(x)` 사용).
- `void*`로 타입 정보 우회 금지 (`std::variant`, `std::any` 사용).
