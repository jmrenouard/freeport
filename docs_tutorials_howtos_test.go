package freeport

import (
	"net"
	"os/exec"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"testing"
)

func TestGetFreePortsDistinctAndZeroCount(t *testing.T) {
	empty, err := GetFreePorts(0)
	if err != nil {
		t.Fatalf("GetFreePorts(0) unexpected error: %v", err)
	}
	if len(empty) != 0 {
		t.Fatalf("GetFreePorts(0) returned %d ports, want 0", len(empty))
	}

	ports, err := GetFreePorts(5)
	if err != nil {
		t.Fatalf("GetFreePorts(5) failed: %v", err)
	}
	if len(ports) != 5 {
		t.Fatalf("GetFreePorts(5) len = %d, want 5", len(ports))
	}

	seen := make(map[int]struct{}, len(ports))
	for _, port := range ports {
		if port <= 0 || port > 65535 {
			t.Fatalf("invalid TCP port %d", port)
		}
		if _, dup := seen[port]; dup {
			t.Fatalf("duplicate port returned by GetFreePorts(5): %d", port)
		}
		seen[port] = struct{}{}
	}
}

func TestDeprecatedGetPort(t *testing.T) {
	port := GetPort()
	if port <= 0 || port > 65535 {
		t.Fatalf("GetPort() returned invalid port %d", port)
	}
}

func TestCLIBinaryReturnsBindablePort(t *testing.T) {
	binName := "freeport-cli-test"
	if runtime.GOOS == "windows" {
		binName += ".exe"
	}
	binPath := filepath.Join(t.TempDir(), binName)

	build := exec.Command("go", "build", "-o", binPath, "./cmd/freeport")
	if out, err := build.CombinedOutput(); err != nil {
		t.Fatalf("go build ./cmd/freeport failed: %v\n%s", err, out)
	}

	run := exec.Command(binPath)
	out, err := run.CombinedOutput()
	if err != nil {
		t.Fatalf("freeport CLI execution failed: %v\n%s", err, out)
	}

	portText := strings.TrimSpace(string(out))
	port, err := strconv.Atoi(portText)
	if err != nil || port <= 0 || port > 65535 {
		t.Fatalf("CLI output %q is not a valid port number: %v", portText, err)
	}

	ln, err := net.Listen("tcp", net.JoinHostPort("127.0.0.1", strconv.Itoa(port)))
	if err != nil {
		t.Fatalf("failed to bind CLI-selected port %d: %v", port, err)
	}
	_ = ln.Close()
}
