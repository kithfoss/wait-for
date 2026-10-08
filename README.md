# wait-for

Wait until a TCP port or URL is reachable, then optionally run a command.

## Usage

```
wait-for <target> [options] [-- command...]
```

`target` is either `host:port` for a TCP check or an `http://` / `https://` URL for an HTTP check.

## Examples

```bash
# Wait for Postgres to accept connections
wait-for localhost:5432

# Wait, then run your app
wait-for localhost:5432 -- python app.py

# Wait for an HTTP health endpoint, then run tests
wait-for http://localhost:8080/health -- pytest

# Timeout after 30 seconds, poll every 500ms
wait-for localhost:6379 --timeout 30 --interval 0.5

# One-shot check — exits 0 if up, 1 if not
wait-for localhost:5432 --status

# Scripting: suppress all output
wait-for localhost:5432 --timeout 60 --quiet && echo "up"
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--timeout SECONDS` | none | Give up after N seconds. Without this, wait forever. |
| `--interval SECONDS` | `1.0` | How often to retry. |
| `--quiet` / `-q` | off | No output. Exit code only. |
| `--status` | off | Check once and exit immediately (no polling). |

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Target became ready (command ran successfully if provided). |
| `1` | Timed out before target was ready, or `--status` check found target down. |
| `2` | Bad arguments (invalid target format). |
| `N` | Exit code of the trailing command, if it ran and exited non-zero. |

## How it works

**TCP check:** Attempts a socket connection to `host:port`. Ready as soon as the connection is accepted.

**HTTP/HTTPS check:** Sends a GET request. Ready as soon as any response arrives — including 4xx or 5xx. The server is up; you don't need a healthy status code.

Progress dots print to stdout while polling. `--quiet` suppresses everything; exit codes still work for scripting.

## Installation

```bash
# Symlink to ~/bin (or anywhere on PATH)
ln -s "$(pwd)/wait-for.py" ~/bin/wait-for
chmod +x wait-for.py
```

## Limitations

- HTTP check accepts any response, including error pages. Use `--status` in a loop with a health endpoint if you need a specific 200.
- HTTPS connections are checked for TCP reachability via the urllib stack; certificate errors count as "not up."
- No retry on command failure — `wait-for` runs the command once.
