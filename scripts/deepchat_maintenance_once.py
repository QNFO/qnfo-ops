#!/usr/bin/env python3
r"""
deepchat_maintenance_once.py - one-shot detached agent.db compaction + clean relaunch.

WHY
  VACUUM requires an exclusive lock, so the app must be closed. This orchestrator
  is launched by a one-shot Task Scheduler job (so it survives the app's death),
  compacts the store offline, clears the volatile profile state, and relaunches a
  verified, clean DeepChat. It is the same close->maintain->relaunch protocol that
  deepchat_vacuum_once.py established, pointed at the new deepchat_compact engine.

SEQUENCE
  1. grace delay (default 90s) so the requesting chat session can deliver its report
  2. pending-restart.json -> status=pending (watchdog must not touch the app)
  3. WM_CLOSE every DeepChat window -> graceful taskkill -> wait -> force fallback
  4. clear volatile Chromium state (deepchat_boot_guard --no-launch)
  5. deepchat_compact.py --mode offline --vacuum   (prune + VACUUM)
  6. pending-restart.json -> done / vacuum_ok
  7. verified relaunch of DeepChat.exe
  8. heal stale hidden settings frames
  9. delete this one-shot task

USAGE (from an elevated/normal shell)
  python deepchat_maintenance_once.py --grace 90 --tape-days 3 --chat-days 14
"""
from __future__ import annotations
import argparse, ctypes, ctypes.wintypes as wt, datetime, json, os, subprocess, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(BASE, "deepchat_maintenance_once.log")
RESTARTS = os.path.expandvars(r"%USERPROFILE%\.deepchat\restarts.log")
PENDING = os.path.expandvars(r"%USERPROFILE%\.deepchat\pending-restart.json")
APP = r"C:\Program Files\DeepChat\DeepChat.exe"
APP_ARGS = ["--remote-debugging-port=9223", "--remote-allow-origins=*"]
TASK = "QNFO_DeepChat_Maintenance_Once"
PY = r"C:\Users\LENOVO\AppData\Local\Programs\Python\Python312\python.exe"
COMPACT = os.path.join(BASE, "deepchat_compact.py")
BOOTGUARD = os.path.join(BASE, "deepchat_boot_guard.py")
HEALER = os.path.join(BASE, "heal_settings_frame.py")


def log(msg):
    line = "%s  [maint] %s" % (datetime.datetime.now().isoformat(), msg)
    print(line, flush=True)
    for p in (LOG, RESTARTS):
        try:
            with open(p, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass


def pids():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq DeepChat.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    r = []
    for row in out.splitlines():
        parts = row.strip('"').split('","')
        if len(parts) >= 2 and parts[0].lower() == "deepchat.exe":
            try:
                r.append(int(parts[1]))
            except ValueError:
                pass
    return r


def wm_close_all():
    WM_CLOSE = 0x0010
    ps = set(pids())
    if not ps:
        return
    user32 = ctypes.windll.user32
    targets = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, lparam):
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in ps:
            targets.append(hwnd)
        return True

    user32.EnumWindows(cb, 0)
    for h in targets:
        user32.PostMessageW(h, WM_CLOSE, 0, 0)
    log("posted WM_CLOSE to %d window(s) of %d process(es)" % (len(targets), len(ps)))


def wait_exit(timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if not pids():
            return True
        time.sleep(2)
    return False


def set_pending(status, ok, extra=None):
    d = {"reason": "agent.db compaction", "scheduled_at": datetime.datetime.now().isoformat(),
         "status": status, "vacuum_ok": ok, "finished_at": datetime.datetime.now().isoformat()}
    if extra:
        d.update(extra)
    try:
        with open(PENDING, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)
    except Exception as e:
        log("pending write failed: %s" % e)


def relaunch(retries=3, timeout=60):
    for i in range(1, retries + 1):
        log("relaunch attempt %d" % i)
        try:
            subprocess.Popen([APP] + APP_ARGS, cwd=os.path.dirname(APP))
        except Exception as e:
            log("Popen failed: %s" % e)
        t0 = time.time()
        while time.time() - t0 < timeout:
            time.sleep(2)
            if pids():
                log("verified DeepChat running")
                return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grace", type=int, default=90)
    ap.add_argument("--tape-days", type=int, default=3)
    ap.add_argument("--chat-days", type=int, default=14)
    ap.add_argument("--keep-sessions", type=int, default=12)
    ap.add_argument("--no-chat-prune", action="store_true")
    a = ap.parse_args()

    log("=== maintenance start (grace %ss, tape %sd, chat %sd, keep %d) ==="
        % (a.grace, a.tape_days, a.chat_days, a.keep_sessions))
    try:
        time.sleep(max(0, a.grace))
        set_pending("pending", False)
        wm_close_all()
        subprocess.run(["taskkill", "/IM", "DeepChat.exe"], capture_output=True, text=True)
        if wait_exit(120):
            log("DeepChat exited gracefully")
        else:
            log("graceful exit timed out - force killing")
            for p in pids():
                subprocess.run(["taskkill", "/PID", str(p), "/F"], capture_output=True, text=True)
            time.sleep(5)

        # clear volatile profile state while nothing holds it
        try:
            subprocess.run([PY, BOOTGUARD, "--no-launch"], capture_output=True, text=True, timeout=180)
            log("boot guard volatile clear done")
        except Exception as e:
            log("boot guard error: %s" % e)

        # prune + vacuum
        cmd = [PY, COMPACT, "--mode", "offline", "--vacuum",
               "--tape-days", str(a.tape_days), "--chat-days", str(a.chat_days),
               "--keep-sessions", str(a.keep_sessions)]
        if a.no_chat_prune:
            cmd.append("--no-chat-prune")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        log("compact rc=%d" % r.returncode)
        if r.stdout:
            log("compact out tail: " + r.stdout.strip()[-1200:])
        if r.stderr:
            log("compact err tail: " + r.stderr.strip()[-400:])
        set_pending("done", r.returncode == 0, {"compact_rc": r.returncode})
    except Exception as e:
        import traceback
        log("FAILED: %s\n%s" % (e, traceback.format_exc()))
        try:
            set_pending("done", False, {"error": str(e)})
        except Exception:
            pass
    finally:
        relaunch()
        try:
            subprocess.run([PY, HEALER], capture_output=True, text=True, timeout=90)
        except Exception as e:
            log("healer error: %s" % e)
        subprocess.run(["schtasks", "/delete", "/tn", TASK, "/f"], capture_output=True, text=True)
        log("=== maintenance complete; one-shot task removed ===")


if __name__ == "__main__":
    sys.exit(main())
