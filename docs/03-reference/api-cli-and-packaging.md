# Go API, CLI & Packaging

## Exported Go API (`freeport.go`)

| Function | Return Type | Behavior |
| :--- | :--- | :--- |
| `GetFreePort()` | `(int, error)` | Resolves `localhost:0`, binds a temporary TCP listener, closes it, and returns the assigned port |
| `GetFreePorts(count int)` | `([]int, error)` | Allocates `count` distinct free TCP ports before closing all listeners on return |
| `GetPort()` *(deprecated)* | `int` | Calls `GetFreePort()` and panics on error; kept only for backwards compatibility |

## CLI Entry Point (`cmd/freeport/main.go`)

| Binary | Output | Exit Code |
| :--- | :--- | :--- |
| `freeport` | Single line containing decimal TCP port integer | `0` on success; `1` via `log.Fatal(err)` on bind failure |

## Module & Repository Files

| File | Purpose |
| :--- | :--- |
| [`go.mod`](../../go.mod) | Declares `module github.com/phayes/freeport` (`go 1.21`, zero external dependencies) |
| [`freeport_test.go`](../../freeport_test.go) | Baseline tests `TestGetFreePort` and `TestGetFreePorts` |
| [`docs_tutorials_howtos_test.go`](../../docs_tutorials_howtos_test.go) | Extended library and compiled CLI verification tests |
| [`.goreleaser.yml`](../../.goreleaser.yml) | Cross-compile configuration (`linux`/`darwin` across `amd64`, `386`, `arm64`, `.deb`, `.rpm`, Homebrew) |
