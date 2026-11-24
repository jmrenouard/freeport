# Allocate Ephemeral Ports Safely in Go and CI

## Prerequisites

- Install Go `1.21` or newer on your host or CI runner.
- Confirm [`go.mod`](../../go.mod) exists at the repository root.

## Procedure

### Step 1: Validate the Module and Test Suite

1. Run `go vet` across all packages to detect static defects.

```bash
go vet ./...
```

2. Run `go test` to verify single and multi-port allocation on the target host.

```bash
go test -v ./...
```

### Step 2: Integrate `freeport` Safely Into Scripts or Services

CAUTION: Bind your service immediately after `freeport` returns a port. Another local process can claim an unbound port first.

1. For shell integration, run the compiled CLI binary and start your server without long delays.

```bash
PORT="$(go run ./cmd/freeport)"
echo "$PORT"
```

2. For Go programs that need multiple distinct ports, call `freeport.GetFreePorts(count)` instead of repeated `GetFreePort()` calls.

NOTE: `GetPort()` panics on socket errors and is deprecated. Always call `GetFreePort()` and handle its `error` return value.

3. If a downstream server fails with `address already in use`, request a fresh port and retry the startup step.

## Validation

Confirm `go vet ./...` reports zero issues and `go test -v ./...` passes all tests. Confirm no temporary build binaries remain in the local repository:

```bash
git status --short
```

## Rollback

If a local modification to CLI callers or `go.mod` breaks builds, revert the change cleanly:

```bash
git checkout -- go.mod
```

## Related Documentation

- [Go API & CLI Reference](../03-reference/api-cli-and-packaging.md)
- [Kernel Port Allocation & TOCTOU Explanation](../04-explanation/kernel-port-allocation-and-race-model.md)
