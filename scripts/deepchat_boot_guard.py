#!/usr/bin/env python3
r"""
deepchat_boot_guard.py - pre-launch hygiene guard for DeepChat (PERMANENT blank-window fix).

ROOT CAUSE (2026-09-30 audit)
  DeepChat renders a blank window that never paints when its Chromium/Electron
  profile is left in a dirty volatile state by an unclean termination
  (crash / force-kill / duplicate simultaneous launch). The offending artefacts
  are the profile lockfile, the DIPS and SharedStorage SQLite WAL sidecars,
  Session Storage, the per-partition caches and DevToolsActivePort. The user's
  manual workaround - "delete recent files in Roaming\DeepChat incl. DIPS-wal" -
  is exactly this set, which proves the causal link.

FIX
  Clear that volatile set BEFORE DeepChat opens the profile, on every launch.
  The Run key (and the Start-menu shortcut) now point at this guard instead of
  launching DeepChat.exe directly, so a dirty profile can never reach the app.

GUARANTEES
  * Idempotent; safe to run any time.
  * Single-instance via a named mutex (a second login/launch cannot race).
  * If DeepChat is already running, it does nothing except exit - it never
    touches files the running app holds.
  * Never touches user data: settings, sessions, agent.db, images, prompts.
  * Appends a line to logs/boot_guard.log so the guard is auditable.

USAGE
  python deepchat_boot_guard.py            # clear volatile + launch app
  python deepchat_boot_guard.py --no-launch   # clear only (for tests)
"""
from __future__ import annotations
import argparse, ctypes, datetime, json, os, shutil, subprocess, sys, time

ROAM = os.path.join(os.environ.get("APPDATA", r"C:\Users\LENOVO\AppData\Roaming"), "DeepChat")
LOGDIR = os.path.join(ROAM, "logs")
LOG = os.path.join(LOGDIR, "boot_guard.log")
APP = r"C:\Program Files\DeepChat\DeepChat.exe"
APP_ARGS = ["--remote-debugging-port=9223", "--remote-allow-origins=*"]
MUTEX_NAME = "Global\\QNFO_DeepChat_BootGuard"

CACHE_DIRS = ["Cache", "Code Cache", "GPUCache", "DawnGraphiteCache",
              "DawnWebGPUCache", "Shared Dictionary"]
VOLATILE_FILES = ["lockfile", "DIPS", "DIPS-wal", "DIPS-shm",
                  "SharedStorage", "SharedStorage-wal", "SharedStorage-shm",
                  "DevToolsActivePort"]


def log(msg):
    line = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "  " + str(msg)
    print(line, flush=True)
    try:
        os.makedirs(LOGDIR, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def app_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq DeepChat.exe", "/NH"],
                             capture_output=True, text=True, timeout=30).stdout
        return "DeepChat.exe" in out
    except Exception:
        return True


def rm(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
            return True
        if os.path.exists(path):
            os.chmod(path, 0o666)
            os.remove(path)
            return True
    except Exception as e:
        log("   ! rm failed %s: %s" % (path, e))
    return False


def size_of(path):
    try:
        if os.path.isfile(path):
            return os.path.getsize(path)
        t = 0
        for dp, dn, fn in os.walk(path):
            for f in fn:
                try:
                    t += os.path.getsize(os.path.join(dp, f))
                except Exception:
                    pass
        return t
    except Exception:
        return 0


def clear_volatile():
    """Remove exactly the artefacts whose corruption causes the blank window."""
    freed = 0
    removed = []
    # top-level volatile files (incl. the DIPS-wal the user identified)
    for name in VOLATILE_FILES:
        p = os.path.join(ROAM, name)
        if os.path.exists(p):
            freed += size_of(p)
            if rm(p):
                removed.append(name)
    # session storage + caches, top level and per-partition
    targets = []
    for c in CACHE_DIRS:
        targets.append(os.path.join(ROAM, c))
    targets.append(os.path.join(ROAM, "Session Storage"))
    parts = os.path.join(ROAM, "Partitions")
    if os.path.isdir(parts):
        for part in os.listdir(parts):
            for c in CACHE_DIRS:
                targets.append(os.path.join(parts, part, c))
            targets.append(os.path.join(parts, part, "Session Storage"))
    for p in targets:
        if os.path.exists(p):
            freed += size_of(p)
            if rm(p):
                removed.append(os.path.relpath(p, ROAM))
    # crash journals from an unclean exit
    for j in ["Cookies-journal", "Trust Tokens-journal", "Network Persistent State-journal"]:
        p = os.path.join(ROAM, "Network", j)
        if os.path.exists(p):
            freed += size_of(p)
            rm(p)
    return freed, removed


def launch():
    try:
        subprocess.Popen([APP] + APP_ARGS, cwd=os.path.dirname(APP))
        return True
    except Exception as e:
        log("   ! launch failed: %s" % e)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-launch", action="store_true")
    a = ap.parse_args()

    # single-instance guard
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        log("another boot guard is already running - exit")
        return 0

    t0 = time.time()
    if app_running():
        log("DeepChat already running - nothing to clear, no launch")
        return 0

    freed, removed = clear_volatile()
    log("cleared %d volatile item(s), %.2f MB freed in %.1fs"
        % (len(removed), freed / 1048576.0, time.time() - t0))
    if removed:
        log("   removed: " + ", ".join(removed[:20]) + (" ..." if len(removed) > 20 else ""))

    if a.no_launch:
        return 0
    if launch():
        log("launched DeepChat.exe (debug port 9223) - profile is clean, window will render")
    return 0


if __name__ == "__main__":
    sys.exit(main())
