#!/usr/bin/env python3
"""calendar-sync.py — Outlook calendar -> JSON for QNFO intent orchestrator ingestion.

Closes CALENDAR-SYNC-TOOL-GAP-1 (2026-08-21): the prior calendar sync cron
(78136b24) failed at its 300s cap because this durable script did not exist
anywhere. Canonical home: QNFO/qnfo-ops scripts/calendar-sync.py (mirror:
C:/Users/LENOVO/.deepchat/scripts/calendar-sync.py).

Usage:
    python calendar-sync.py [days] [--pretty]
    python calendar-sync.py 14      # next 14 days, compact JSON on stdout
Exit codes: 0 = ok, 2 = Outlook/pywin32 unavailable, 3 = unexpected error.
Output: {"ok": true, "count": N, "events": [{"subject","start","duration_min","location","all_day"}]}
"""
import sys, json
from datetime import datetime, timedelta

try:
    import win32com.client
except ImportError:
    print(json.dumps({"ok": False, "error": "pywin32 not installed"}))
    sys.exit(2)


def get_upcoming_events(days):
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    cal = ns.GetDefaultFolder(9)  # olFolderCalendar
    items = cal.Items
    items.IncludeRecurrences = True
    items.Sort("[Start]")
    now = datetime.now()
    horizon = now + timedelta(days=int(days))
    events = []
    for it in items:
        try:
            start = it.Start
            if isinstance(start, str):
                start = datetime.fromisoformat(start.replace("Z", ""))
            if start < now:
                continue
            if start > horizon:
                break
            events.append({
                "subject": str(it.Subject or "").strip(),
                "start": start.isoformat(),
                "duration_min": int(it.Duration or 0),
                "location": str(it.Location or "").strip(),
                "all_day": bool(it.AllDayEvent),
            })
            if len(events) >= 30:
                break
        except Exception:
            continue
    return events


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    try:
        events = get_upcoming_events(days)
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(3)
    print(json.dumps({"ok": True, "count": len(events), "events": events}, indent=2))


if __name__ == "__main__":
    main()
