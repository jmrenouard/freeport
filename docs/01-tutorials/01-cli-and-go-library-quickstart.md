# Tutorial 1: Run the FreePort CLI and Go Library

In this tutorial, you build and run [`cmd/freeport/main.go`](../../cmd/freeport/main.go), execute the repository's Go unit tests, and verify how `GetFreePort` and `GetFreePorts` behave.

## Prerequisites

- Go `1.21` or newer

Confirm your Go version and module configuration:

```bash
go version
```

## Step 1: Run the Go Test Suite

Execute all Go tests using the module defined in [`go.mod`](../../go.mod):

```bash
go test -v ./...
```

Expected output shows `TestGetFreePort`, `TestGetFreePorts`, and doc-verification tests passing cleanly (`PASS`).

## Step 2: Build and Execute the CLI Binary

Compile [`cmd/freeport/main.go`](../../cmd/freeport/main.go) into a temporary binary and print a free TCP port:

```bash
go build -o /tmp/freeport-cli ./cmd/freeport
/tmp/freeport-cli
rm -f /tmp/freeport-cli
```

Expected output prints a single valid TCP port integer in the host's ephemeral port range (for example `45312`).

## Step 3: Allocate Multiple Distinct Ports in Go

[`freeport.go`](../../freeport.go) exports `GetFreePorts(count int)` alongside `GetFreePort()`:

```bash
go test -v -run 'TestGetFreePorts$' ./...
```

All `count` returned ports are guaranteed distinct from one another because `GetFreePorts` holds each TCP listener open via `defer l.Close()` until all ports are assigned.

## Next Steps

- Apply [How-To: Allocate Ephemeral Ports Safely in Go and CI](../02-how-to-guides/allocate-ports-safely-in-go-and-ci.md).
- Inspect [Reference: Go API, CLI & Packaging](../03-reference/api-cli-and-packaging.md).
