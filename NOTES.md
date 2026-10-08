# wait-for — Build Notes

**Week 47** | Seeded 2026-09-06 | Built 2026-10-03

## What it does

Polls a TCP port or HTTP URL until it's reachable, then optionally hands off to a command. One stdlib Python file, no dependencies.

## Design decisions

**Two check modes, not one.** TCP (`host:port`) and HTTP (`http://...`) behave differently in practice. A TCP connect proves the socket accepted; that's enough for databases and message queues. HTTP is trickier — even a 503 means the server is up and responding, which is usually what you want when waiting for a container to start. So HTTP success is defined as "got any response," not "got 200." If you need a healthy 200, that's a different problem (use a real health-check loop).

**Progress to stdout, errors to stderr.** The `Waiting...` line and dots go to stdout so they can be redirected or suppressed independently. The timeout message goes to stderr. `--quiet` kills stdout entirely; exit codes remain meaningful for scripting.

**Exit code propagation.** If a trailing command is given, its exit code becomes wait-for's exit code. This makes `wait-for db:5432 -- flask run` behave like `flask run` from the caller's perspective — no wrapper noise.

**No retries on command failure.** wait-for's job is to know when the target is up. What happens after that is the caller's problem. Adding retry-on-failure would be scope creep and would make exit code semantics ambiguous.

**`--status` for scripting.** One-shot check without polling. Useful in `if wait-for localhost:5432 --status --quiet; then ...` patterns where you want to branch on current state, not wait for it.

**Stdlib only.** `socket`, `urllib.request`, `subprocess`, `time`, `argparse`. No `requests`, no `aiohttp`. The tool should install anywhere Python 3.6+ runs without a venv.

## Test coverage

30 tests across parse, status, poll, timeout, command, defaults, and HTTP. Tests spin real TCP and HTTP servers in threads to avoid mocking the network. Exit codes, stdout/stderr routing, and quiet mode all verified.

## What's blocked

Release needs `GH_TOKEN`. Tool is complete; waiting on re-auth.

## Lessons

The `--` separator before the trailing command is idiomatic (`docker run`, `ssh`) and avoids ambiguity when the command has flags. `argparse.REMAINDER` collects everything after `--` cleanly.

HTTP "any response is up" surprised me slightly — my first instinct was to check for 2xx only. But in practice you're waiting for the process to bind and start serving, not for the app to be healthy. A 503 from Flask's startup error page still means the port is open and the server is alive.
