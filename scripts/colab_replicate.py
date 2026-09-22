#!/usr/bin/env python3
"""Drives the hardware-replication run on Colab VMs.

Colab sessions are reclaimed without warning, so this driver assumes they will
die: it downloads each VM's partial results on every poll, tracks which
instances are already complete, and recreates and re-provisions a session that
has been lost, handing it only the instances that are still outstanding.

Instances are ordered cheapest-first within each session, so that losing a
session late costs the least.
"""
import argparse
import base64
import collections
import csv
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLAB = os.environ.get("COLAB_BIN", "/home/user/colabenv/bin/colab")
SOLVERS = "cascade,redumis,online_mis,numvc,fastvc,nearlinear,lineartime"
N_SOLVERS = len(SOLVERS.split(","))
SETUP_URL = ("https://raw.githubusercontent.com/vinhqdang/max_independence_set/"
             "main/scripts/colab_setup.sh")

# Cheapest first; the heavy ones are last so a lost session costs least.
QUEUES = {
    "rep1": ["ca-AstroPh", "ca-CondMat", "email-Enron", "frb30-15-1", "frb35-17-1",
             "del16", "rgg16", "web-Stanford", "del20"],
    "rep2": ["frb40-19-1", "frb45-21-1", "frb50-23-1", "com-dblp", "com-amazon",
             "rgg18", "del18", "roadNet-PA", "rgg20"],
    "rep3": ["frb53-24-1", "frb59-26-1", "com-youtube", "wiki-Talk", "web-BerkStan",
             "as-skitter", "roadNet-CA"],
}


def colab(args, timeout=300):
    try:
        r = subprocess.run([COLAB] + args, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return 1, "TIMEOUT"


def exec_py(session, code, timeout=300, exec_timeout=180):
    path = "/tmp/_colab_exec_%s.py" % session
    with open(path, "w") as f:
        f.write(code)
    return colab(["exec", "-s", session, "-f", path, "--timeout", str(exec_timeout)], timeout)


def session_alive(session):
    rc, out = exec_py(session, "print('ALIVE')", timeout=180, exec_timeout=60)
    return "ALIVE" in out


def ensure_session(session, log):
    if session_alive(session):
        return True
    log("session %s not reachable; creating" % session)
    colab(["stop", "-s", session], timeout=120)
    rc, out = colab(["new", "-s", session], timeout=600)
    if not session_alive(session):
        log("  could not create %s: %s" % (session, out.strip()[:120]))
        return False
    log("  created %s; provisioning" % session)
    exec_py(session, f"""
import subprocess
subprocess.run(['bash','-c','curl -sSL -o /content/setup.sh {SETUP_URL} && chmod +x /content/setup.sh'])
subprocess.Popen(['bash','-c','nohup bash /content/setup.sh > /content/setup.log 2>&1 &'])
print('provisioning')
""", timeout=300)
    return True


def setup_done(session):
    rc, out = exec_py(session, """
import subprocess
print(subprocess.run(['bash','-c','grep -c SETUP_COMPLETE /content/setup.log 2>/dev/null || echo 0'],
                     capture_output=True,text=True).stdout.strip())
""", timeout=240)
    return "1" in out.split("\n")[-2:][0] if out else False


def bench_running(session):
    rc, out = exec_py(session, """
import subprocess
print('RUNNING' if subprocess.run(['bash','-c','pgrep -f run_bench.py >/dev/null && echo y'],
      capture_output=True,text=True).stdout.strip()=='y' else 'IDLE')
""", timeout=240)
    return "RUNNING" in out


def launch(session, instances, log):
    inst = ",".join(instances)
    log("  launching %s on %d instances" % (session, len(instances)))
    exec_py(session, f"""
import subprocess
cmd = ('cd /content/mis/max_independence_set && MIS_BASELINE_DIR=/content/mis/baselines '
       'nohup python3 scripts/run_bench.py --catalogue /content/data/instances/catalogue.json '
       '--solvers {SOLVERS} --time-limit 60 --instances {inst} '
       '--out /content/replication.csv >> /content/bench.log 2>&1 &')
subprocess.Popen(['bash','-c',cmd])
print('launched')
""", timeout=300)


def fetch(session):
    """Returns the VM's CSV rows, base64 encoded in transit so nothing is mangled."""
    rc, out = exec_py(session, """
import base64, os
p='/content/replication.csv'
print('B64:' + (base64.b64encode(open(p,'rb').read()).decode() if os.path.exists(p) else ''))
""", timeout=300)
    for line in out.split("\n"):
        if line.startswith("B64:"):
            blob = line[4:].strip()
            if not blob:
                return []
            try:
                text = base64.b64decode(blob).decode()
            except Exception:
                return []
            return [r for r in csv.reader(text.strip().split("\n")) if r and r[0] != "instance"]
    return []


def merge(rows, path):
    existing = []
    if os.path.exists(path):
        with open(path) as f:
            existing = [r for r in csv.reader(f) if r and r[0] != "instance"]
    seen = {(r[0], r[4], r[5]) for r in existing}
    added = [r for r in rows if (r[0], r[4], r[5]) not in seen]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["instance", "family", "n", "m", "solver", "seed",
                    "time_limit", "size", "seconds", "verified", "note"])
        for r in existing + added:
            w.writerow(r)
    return len(added), len(existing) + len(added)


def completed(path):
    counts = collections.Counter()
    if os.path.exists(path):
        with open(path) as f:
            for r in csv.reader(f):
                if r and r[0] != "instance":
                    counts[r[0]] += 1
    return {i for i, c in counts.items() if c >= N_SOLVERS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "replication60.csv"))
    ap.add_argument("--poll", type=int, default=180)
    ap.add_argument("--max-hours", type=float, default=6.0)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    deadline = time.time() + args.max_hours * 3600
    launched = set()

    def log(msg):
        print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)

    while time.time() < deadline:
        done = completed(args.out)
        outstanding = {s: [i for i in q if i not in done] for s, q in QUEUES.items()}
        if not any(outstanding.values()):
            log("all instances complete")
            break

        for session, todo in outstanding.items():
            if not todo:
                continue
            if not ensure_session(session, log):
                continue
            rows = fetch(session)
            if rows:
                added, total = merge(rows, args.out)
                if added:
                    log("%s: +%d rows (%d total)" % (session, added, total))
            if not setup_done(session):
                log("%s: still provisioning" % session)
                launched.discard(session)
                continue
            if not bench_running(session):
                still = [i for i in todo if i not in completed(args.out)]
                if still:
                    launch(session, still, log)
                    launched.add(session)
        time.sleep(args.poll)

    log("driver finished; %d instances complete" % len(completed(args.out)))


if __name__ == "__main__":
    sys.exit(main())
