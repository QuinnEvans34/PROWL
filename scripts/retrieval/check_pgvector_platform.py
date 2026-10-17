#!/usr/bin/env python3
"""Read-only Mac preflight and bounded synthetic trial. Never pulls images.

check needs no credentials/data directory. run requires an existing empty directory
and private password file, and always stops its Compose service on normal/failure exit.
"""
import argparse
import fcntl
import signal
import json
import os
from pathlib import Path
import plistlib
import shutil
import socket
import stat
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "infra/retrieval/compose.yaml"
IMAGE = "pgvector/pgvector@sha256:88b17bc7a7dd6ef73d46c1b15aaa5936d50acb24e4a78713e134c579bf359e25"
GIB = 1024**3
INTERNAL_FLOOR = 100 * GIB
INTERNAL_RESERVE = 4 * GIB
EXTERNAL_FLOOR = 400 * GIB
DATA_CAP = 8 * GIB
SECONDS = 1800


def command(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, timeout=30, **kwargs)


def validate_config(c):
    if set(c) != {"mount", "volume_uuid", "data", "password_file", "port"}:
        raise ValueError("Unexpected or missing configuration fields")
    mount, data = Path(c["mount"]), Path(c["data"])
    if not mount.is_absolute() or not data.is_absolute():
        raise ValueError("Absolute storage paths required")
    if data.resolve() == mount.resolve() or not data.resolve().is_relative_to(mount.resolve()):
        raise ValueError("Data must be inside the mounted volume")
    if data != data.resolve() or mount != mount.resolve():
        raise ValueError("Symlink/ambiguous storage path refused")
    if type(c["port"]) is not int or not 1024 <= c["port"] <= 65535:
        raise ValueError("Invalid unprivileged port")


def check_observation(c, volume, internal_free, external_free, port_free):
    errors = []
    if volume.get("VolumeUUID", "").upper() != c["volume_uuid"].upper():
        errors.append("External volume UUID mismatch")
    if volume.get("MountPoint") != c["mount"] or volume.get("Mounted") is False:
        errors.append("Expected volume is not mounted at configured path")
    if internal_free < INTERNAL_FLOOR + INTERNAL_RESERVE:
        errors.append("Internal space below 100 GiB floor + 4 GiB reservation")
    if external_free < EXTERNAL_FLOOR + DATA_CAP:
        errors.append("External space below 400 GiB floor + 8 GiB reservation")
    if not port_free:
        errors.append("Local port is occupied")
    return errors


def preflight(c):
    validate_config(c)
    volume = plistlib.loads(command(["diskutil", "info", "-plist", c["mount"]]).stdout)
    internal = shutil.disk_usage("/System/Volumes/Data").free
    external = shutil.disk_usage(c["mount"]).free
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", c["port"]))
            port_free = True
        except OSError:
            port_free = False
    errors = check_observation(c, volume, internal, external, port_free)
    info = json.loads(command(["docker", "--context", "desktop-linux", "info", "--format", "{{json .}}"]).stdout)
    # Existing desktop-linux context only: no remote Docker bind mount assumptions.
    context = command(["docker", "context", "show"]).stdout.decode().strip()
    if context != "desktop-linux":
        errors.append("Expected local Docker Desktop context desktop-linux")
    physical = int(command(["sysctl", "-n", "hw.memsize"]).stdout)
    if info["MemTotal"] > physical * .15:
        errors.append("Docker VM memory exceeds P4a 15 percent bar")
    existing = command(["docker", "--context", "desktop-linux", "ps", "-aq", "--filter",
                        "label=com.docker.compose.project=prowl-retrieval-smoke"]).stdout.strip()
    if existing:
        errors.append("Existing trial container: preserve/review before a fresh run")
    return {"ready": not errors, "errors": errors, "internal_free": internal,
            "external_free": external, "port": c["port"], "volume_uuid": volume.get("VolumeUUID"),
            "docker_context": context, "docker_memory": info["MemTotal"],
            "image": IMAGE, "image_local_checked": False}


def compose(c):
    env = dict(os.environ, PROWL_DB_PORT=str(c["port"]), PROWL_DB_DATA=c["data"],
               PROWL_DB_PASSWORD_FILE=c["password_file"])
    return ["docker", "--context", "desktop-linux", "compose", "-p", "prowl-retrieval-smoke", "-f", str(COMPOSE)], env


def runtime_reason(elapsed, internal_free, external_free, data_bytes):
    if elapsed >= SECONDS:
        return "Time ceiling reached"
    if internal_free < INTERNAL_FLOOR:
        return "Internal free-space floor reached"
    if external_free < EXTERNAL_FLOOR:
        return "External free-space floor reached"
    if data_bytes >= DATA_CAP:
        return "External data ceiling reached"
    return None


def sample_resources(c, start, output):
    # Allocated blocks; never read database payloads. Sampling is not a disk quota.
    used = int(command(["du", "-sk", c["data"]]).stdout.split()[0]) * 1024
    observation = {"seconds": time.monotonic() - start, "data_bytes": used,
                   "internal_free": shutil.disk_usage("/System/Volumes/Data").free,
                   "external_free": shutil.disk_usage(c["mount"]).free}
    with (output / "metrics.jsonl").open("a") as metrics:
        metrics.write(json.dumps(observation) + "\n")
    reason = runtime_reason(observation["seconds"], observation["internal_free"],
                            observation["external_free"], used)
    if reason:
        raise RuntimeError(reason)


def stop_trial(base, env, output):
    result = {"stop_confirmed": False}
    try:
        stopped = subprocess.run(base + ["stop", "-t", "60"], env=env, capture_output=True, timeout=75)
        result["stop_exit_code"] = stopped.returncode
        (output / "stop.stderr").write_bytes(stopped.stderr)
        running = command(base + ["ps", "--status", "running", "-q"], env=env).stdout.strip()
        result["stop_confirmed"] = stopped.returncode == 0 and not running
    except Exception as exc:
        result["stop_error"] = str(exc)
    return result


def run_owned(c, output):
    report = preflight(c)
    if not report["ready"]:
        raise ValueError(report["errors"])
    data, password = Path(c["data"]), Path(c["password_file"])
    if not data.is_dir() or any(data.iterdir()):
        raise ValueError("Fresh existing empty data directory required; no automatic creation/deletion")
    if password.is_symlink() or not password.is_file() or stat.S_IMODE(password.stat().st_mode) & 0o077:
        raise ValueError("Password must be a private regular file (mode 600)")
    if len(password.read_bytes().strip()) < 24:
        raise ValueError("Password must contain at least 24 bytes")
    command(["docker", "--context", "desktop-linux", "image", "inspect", IMAGE])  # No implicit image pull.
    output.mkdir(parents=True, exist_ok=False)
    base, env = compose(c)
    command(base + ["config", "--quiet"], env=env)
    start = time.monotonic()
    process = None
    result = {"preflight": report, "state": "starting"}
    try:
        sample_resources(c, start, output)
        launched = command(base + ["up", "-d", "--pull", "never"], env=env)
        (output / "startup.stdout").write_bytes(launched.stdout)
        (output / "startup.stderr").write_bytes(launched.stderr)
        with (output / "smoke.stdout").open("wb") as out, (output / "smoke.stderr").open("wb") as err:
            for _ in range(60):
                sample_resources(c, start, output)
                ready = subprocess.run(base + ["exec", "-T", "db", "pg_isready", "-h", "127.0.0.1", "-U", "prowl_trial", "-d", "prowl_synthetic"],
                                       env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                if ready.returncode == 0:
                    break
                time.sleep(1)
            else:
                raise RuntimeError("Database readiness timeout")
            with (ROOT / "infra/retrieval/smoke.sql").open("rb") as sql:
                process = subprocess.Popen(base + ["exec", "-T", "db", "psql", "-X", "-v", "ON_ERROR_STOP=1",
                                                  "-U", "prowl_trial", "-d", "prowl_synthetic"],
                                           env=env, stdin=sql, stdout=out, stderr=err)
                while True:
                    sample_resources(c, start, output)
                    if process.poll() is not None:
                        break
                    time.sleep(1)
                if process.returncode:
                    raise RuntimeError(f"SQL smoke failed: {process.returncode}")
        result["state"] = "smoke_passed"
    except BaseException as exc:
        result.update(state="failed", error=str(exc))
        if isinstance(exc, subprocess.CalledProcessError):
            (output / "failure.stdout").write_bytes(exc.stdout or b"")
            (output / "failure.stderr").write_bytes(exc.stderr or b"")
        raise
    finally:
        # Preserve container/data for review; never down -v or delete.
        try:
            result.update(stop_trial(base, env, output))
        finally:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        if not result.get("stop_confirmed"):
            raise RuntimeError("Stop not confirmed; inspect owned trial immediately")


def run(c, output):
    # One local coordinator; retain the lock file so unlink races cannot create two locks.
    lock_path = ROOT / "outputs/prowl/pgvector-platform.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        previous = signal.getsignal(signal.SIGTERM)
        def interrupted(signum, frame):
            raise KeyboardInterrupt("Requested stop")
        signal.signal(signal.SIGTERM, interrupted)
        try:
            run_owned(c, output)
        finally:
            signal.signal(signal.SIGTERM, previous)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["check", "run"])
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    c = json.loads(args.config.read_text())
    if args.action == "check":
        report = preflight(c)
        print(json.dumps(report, indent=2))
        return 0 if report["ready"] else 2
    if args.output is None:
        p.error("run requires a fresh --output directory")
    run(c, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
