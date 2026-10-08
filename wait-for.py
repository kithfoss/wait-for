#!/usr/bin/env python3
"""wait-for: Wait until a port or URL is reachable, then run a command."""

import argparse
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


def parse_target(target):
    """Parse 'host:port' or 'http://...' target. Returns ('tcp'|'http', host, port, url)."""
    if target.startswith("http://") or target.startswith("https://"):
        return ("http", None, None, target)
    if ":" in target:
        parts = target.rsplit(":", 1)
        host = parts[0]
        try:
            port = int(parts[1])
        except ValueError:
            raise ValueError(f"Invalid port in target: {target!r}")
        return ("tcp", host, port, None)
    raise ValueError(
        f"Target must be 'host:port' or an http/https URL, got: {target!r}"
    )


def check_tcp(host, port, timeout=2):
    """Return True if TCP connection to host:port succeeds."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def check_http(url, timeout=5):
    """Return True if HTTP GET to url returns any response (even 4xx/5xx)."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except urllib.error.HTTPError:
        # Got a response — server is up, even if status is bad
        return True
    except (urllib.error.URLError, OSError, Exception):
        return False


def poll(kind, host, port, url, timeout, interval, quiet):
    """Poll until ready or timeout. Returns True if ready, False if timed out."""
    start = time.monotonic()
    dots = 0
    while True:
        if kind == "tcp":
            ready = check_tcp(host, port)
        else:
            ready = check_http(url)

        if ready:
            if not quiet and dots > 0:
                print("", flush=True)
            return True

        elapsed = time.monotonic() - start
        if timeout is not None and elapsed >= timeout:
            if not quiet and dots > 0:
                print("", flush=True)
            return False

        if not quiet:
            print(".", end="", flush=True)
            dots += 1

        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(
        description="Wait until a port or URL is reachable, then run a command.",
        epilog=(
            "Examples:\n"
            "  wait-for localhost:5432\n"
            "  wait-for localhost:5432 -- python app.py\n"
            "  wait-for http://localhost:8080/health -- pytest\n"
            "  wait-for localhost:6379 --timeout 30 --interval 0.5\n"
            "  wait-for localhost:5432 --status"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("target", help="host:port or http/https URL to wait for")
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        metavar="SECONDS",
        help="give up after N seconds (default: wait forever)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="polling interval in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="suppress progress output",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="check once and exit 0 if ready, 1 if not (no polling)",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="command to run after target is ready (prefix with --)",
    )

    args = parser.parse_args()

    # Strip leading '--' separator if present
    cmd = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]

    # Parse target
    try:
        kind, host, port, url = parse_target(args.target)
    except ValueError as e:
        print(f"wait-for: {e}", file=sys.stderr)
        sys.exit(2)

    target_label = args.target

    # --status: single check, no polling
    if args.status:
        if kind == "tcp":
            ready = check_tcp(host, port)
        else:
            ready = check_http(url)
        if ready:
            if not args.quiet:
                print(f"wait-for: {target_label} is up")
            sys.exit(0)
        else:
            if not args.quiet:
                print(f"wait-for: {target_label} is not yet up")
            sys.exit(1)

    # Normal poll loop
    if not args.quiet:
        msg = f"Waiting for {target_label}"
        if args.timeout is not None:
            msg += f" (timeout {args.timeout}s)"
        print(msg, end="", flush=True)

    ready = poll(kind, host, port, url, args.timeout, args.interval, args.quiet)

    if not ready:
        if not args.quiet:
            print(
                f"\nwait-for: timed out waiting for {target_label} after {args.timeout}s",
                file=sys.stderr,
            )
        sys.exit(1)

    if not args.quiet:
        print(f" ready.")

    # Run command if given
    if cmd:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)

    sys.exit(0)


if __name__ == "__main__":
    main()
