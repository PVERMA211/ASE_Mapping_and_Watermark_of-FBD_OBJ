#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path


def check_python_version(required_major: int = 3, required_minor: int = 14) -> tuple[bool, str]:
    current = sys.version_info
    if (current.major, current.minor) != (required_major, required_minor):
        return (
            False,
            f"Python {required_major}.{required_minor} is required, found {current.major}.{current.minor}.{current.micro}.",
        )
    return True, f"Python version OK: {current.major}.{current.minor}.{current.micro}"


def check_command(command: str) -> tuple[bool, str]:
    resolved = shutil.which(command)
    if not resolved:
        return False, f"Missing required command: {command}"
    return True, f"Found {command}: {resolved}"


def run_command(*command: str, cwd: Path | None = None) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, f"Command not available: {' '.join(command)}"
    except subprocess.CalledProcessError as error:
        output = (error.stdout + "\n" + error.stderr).strip()
        return False, output or f"Command failed: {' '.join(command)}"
    output = (completed.stdout or completed.stderr).strip()
    return True, output or f"Command succeeded: {' '.join(command)}"


def check_port_available(port: int) -> tuple[bool, str]:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
        candidate.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            candidate.bind(("127.0.0.1", port))
        except OSError as error:
            return False, f"Port {port} is not available: {error}"
    return True, f"Port {port} is available"


def parse_env(project_root: Path) -> dict[str, str]:
    env_path = project_root / ".env"
    source_path = env_path if env_path.exists() else project_root / ".env.example"
    values: dict[str, str] = {}
    if source_path.exists():
        for raw_line in source_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def validate(project_root: Path) -> list[tuple[str, bool, str]]:
    env_values = parse_env(project_root)
    port = int(os.environ.get("N8N_PORT") or env_values.get("N8N_PORT", "5678"))
    checks: list[tuple[str, bool, str]] = []

    checks.append(("python", *check_python_version()))
    checks.append(("docker", *check_command("docker")))
    checks.append(("docker_compose", *run_command("docker", "compose", "version")))
    checks.append(("docker_daemon", *run_command("docker", "info")))
    checks.append(("compose_config", *run_command("docker", "compose", "config", cwd=project_root)))
    checks.append(("port", *check_port_available(port)))
    checks.append(
        (
            "env_file",
            True,
            f"Using environment values from {(project_root / '.env') if (project_root / '.env').exists() else (project_root / '.env.example')}",
        )
    )

    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate machine prerequisites for running n8n.")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    project_root = args.project_root.resolve()

    results = validate(project_root)
    failures = 0
    for name, passed, message in results:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}: {message}")
        if not passed:
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
