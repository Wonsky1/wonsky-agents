# Language Adapters

Resolve the project's real toolchain before running any build / test / lint / type-check / run command. **Detect first, then use the project's actual configured commands** — the tables below are defaults, not overrides. If the project defines custom scripts (npm scripts, Makefile targets, Bazel, Nx, justfile, Xcode schemes), those win.

## Detection markers

| Marker file(s) | Language / ecosystem |
|----------------|----------------------|
| `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile` | Python |
| `Package.swift`, `*.xcodeproj`, `*.xcworkspace`, `Podfile` | Swift / Apple |
| `CMakeLists.txt`, `Makefile`, `*.vcxproj`, `conanfile.*`, `meson.build` | C / C++ |
| `package.json` (+ `tsconfig.json` for TS) | JavaScript / TypeScript |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `build.gradle(.kts)`, `pom.xml` | JVM (Kotlin / Java) |
| `*.csproj`, `*.sln` | .NET / C# |
| `mix.exs` | Elixir |
| `Gemfile` | Ruby |

If multiple markers exist (polyglot repo), resolve per directory/target, not globally.

## Default command tables

### Python
- **Deps/env:** `uv` or `poetry` or `python -m venv` + `pip install -e .`
- **Test:** `pytest` (use the `testing-pytest` skill)
- **Lint:** `ruff check` · **Format:** `ruff format` (or `black`)
- **Type-check:** `mypy` or `pyright`
- **Run:** `python -m <pkg>` / project entry point

### Swift
- **Build:** `swift build` (SPM) or `xcodebuild -scheme <S> build`
- **Test:** `swift test` or `xcodebuild test -scheme <S> -destination '<dest>'`
- **Lint:** `swiftlint` · **Format:** `swift-format` or `swiftformat`
- **Run:** `swift run <target>` or run the built product / simulator

### C / C++
- **Configure/Build:** `cmake -B build && cmake --build build` (or `make`)
- **Test:** `ctest --test-dir build` (or the project's test target)
- **Lint/Static:** `clang-tidy`, `cppcheck` · **Format:** `clang-format`
- **Sanitizers:** prefer building with `-fsanitize=address,undefined` for debugging
- **Run:** the built binary in `build/`

### JavaScript / TypeScript
- **Deps:** detect `pnpm` / `yarn` / `npm` / `bun` from lockfile; install accordingly
- **Test:** the project's test script (`vitest`, `jest`, `node --test`, `playwright`)
- **Lint:** `eslint` · **Format:** `prettier`
- **Type-check:** `tsc --noEmit` (TS)
- **Build/Run:** the project's `build` / `dev` / `start` scripts

### Go
- **Build:** `go build ./...` · **Run:** `go run .`
- **Test:** `go test ./...` (`-race` for concurrency)
- **Lint:** `golangci-lint run` · **Format:** `gofmt` / `goimports`
- **Vet:** `go vet ./...`

### Rust
- **Build:** `cargo build` · **Run:** `cargo run`
- **Test:** `cargo test`
- **Lint:** `cargo clippy` · **Format:** `cargo fmt`
- **Type-check:** `cargo check`

### JVM (Kotlin / Java)
- **Gradle:** `./gradlew build` / `test` / `run`
- **Maven:** `mvn verify` / `test`
- **Lint/Format:** `ktlint` / `detekt` (Kotlin); `spotless`, `checkstyle` (Java)

### .NET / C#
- **Build:** `dotnet build` · **Run:** `dotnet run`
- **Test:** `dotnet test` · **Format:** `dotnet format`

## How the orchestrator uses this

1. Detect language(s) from markers.
2. Read the project's own config to confirm the real commands (custom scripts override defaults).
3. Use those commands in Phase 4 (build/run), Phase 5 (test/lint/type-check), and the Completion Verification Route.
4. When delegating to the `test-engineer` or `qa-tester` agent, pass the resolved commands so the agent doesn't re-guess.
5. If detection is ambiguous, ask the user once, then proceed.
