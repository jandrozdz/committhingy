#!/usr/bin/env python3
"""committhingy — tick a counter, commit it, and push, to keep the graph green.

Run with --jitter (as cron does) to sleep a random 0-30 min before working,
so commits land roughly every hour, give or take half an hour.
"""
import os
import sys
import time
import random
import datetime
import subprocess

REPO = os.path.dirname(os.path.abspath(__file__))
COUNT_FILE = os.path.join(REPO, "ticks.txt")
LOG_FILE = os.path.join(REPO, "committhingy.log")


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def git(*args):
    return subprocess.run(
        ["git", "-C", REPO, *args], capture_output=True, text=True
    )


def main():
    if "--jitter" in sys.argv[1:]:
        delay = random.randint(0, 30 * 60)  # 0-30 min
        log(f"jitter: sleeping {delay}s before this tick")
        time.sleep(delay)

    try:
        n = int(open(COUNT_FILE).read().strip())
    except (FileNotFoundError, ValueError):
        n = 0
    n += 1
    with open(COUNT_FILE, "w") as f:
        f.write(f"{n}\n")

    git("add", "ticks.txt")
    if git("diff", "--cached", "--quiet").returncode == 0:
        log(f"nothing staged for tick {n}, skipping")
        return

    msg = f"Tick #{n}"
    r = git("commit", "-m", msg)
    if r.returncode != 0:
        log(f"commit failed: {r.stderr.strip()}")
        return
    log(f"committed {msg}")

    p = git("push", "origin", "HEAD")
    if p.returncode == 0:
        log(f"pushed {msg}")
    else:
        log(f"push failed (unpushed commits will go out next run): "
            f"{p.stderr.strip()}")


if __name__ == "__main__":
    main()
