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
# The CLI keeps its name -> session mapping under ~/.config, which this
# container does not reliably preserve across a restart. Losing it strands the
# VMs: they keep running and keep holding the concurrent-assignment quota, but
# can no longer be addressed by name. Keeping the file beside the repository,
# which does survive, lets a restarted driver pick the same VMs back up.
COLAB_STATE = os.environ.get(
    "COLAB_STATE", os.path.join(ROOT, ".colab", "sessions.json"))
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
    os.makedirs(os.path.dirname(COLAB_STATE), exist_ok=True)
    try:
        r = subprocess.run([COLAB, "--config", COLAB_STATE] + args,
                           capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return 1, "TIMEOUT"


def exec_py(session, code, timeout=300, exec_timeout=180):
    # These snippets are built as Python strings inside this file, so an escape
    # sequence in a comment (a stray \\n) silently splits a line and ships the
    # VM a file that will not parse. The VM then prints nothing, and a caller
    # reading the reply for a sentinel concludes "not ready" rather than
    # "broken" -- which cost a provisioned machine an hour of idling once.
    # Refuse to send anything that does not compile here.
    try:
        compile(code, "<remote:%s>" % session, "exec")
    except SyntaxError as e:
        return 1, "LOCAL_SYNTAX_ERROR %s" % e

    path = "/tmp/_colab_exec_%s.py" % session
    with open(path, "w") as f:
        f.write(code)
    return colab(["exec", "-s", session, "-f", path, "--timeout", str(exec_timeout)], timeout)


def session_alive(session):
    rc, out = exec_py(session, "print('SESSION_STATE=ALIVE')", timeout=180, exec_timeout=60)
    return "SESSION_STATE=ALIVE" in out


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


def setup_state(session):
    """Returns (ready, reason).

    The VM answers with one sentinel token, so the verdict survives whatever
    else the Colab client prints around it. A reply carrying neither sentinel
    means the probe itself failed, which is not the same as a machine that is
    still provisioning, and is reported as its own case: read as "provisioning"
    it leaves a ready machine idle indefinitely with nothing in the log to say
    so."""
    rc, out = exec_py(session, """
import subprocess
# grep -c exits 1 on a zero count, so a '|| echo 0' fallback fires on top of
# the zero grep already printed and the reply comes back as two lines. grep -q
# plus one echo keeps the answer to a single token.
hit = subprocess.run(['bash','-c','grep -q SETUP_COMPLETE /content/setup.log 2>/dev/null && echo yes || echo no'],
                     capture_output=True, text=True).stdout.strip()
print('SETUP_STATE=' + ('READY' if hit == 'yes' else 'PENDING'))
""", timeout=240)
    if "SETUP_STATE=READY" in out:
        return True, "ready"
    if "SETUP_STATE=PENDING" in out:
        return False, "still provisioning"
    return False, "PROBE FAILED (no verdict returned): %s" % out.strip()[-160:]


def bench_running(session):
    rc, out = exec_py(session, """
import subprocess
# The bracket stops the pattern matching this command's own line.
hit = subprocess.run(['bash','-c','pgrep -f "[r]un_bench.py" >/dev/null && echo y'],
                     capture_output=True, text=True).stdout.strip()
print('BENCH_STATE=' + ('RUNNING' if hit == 'y' else 'IDLE'))
""", timeout=240)
    return "BENCH_STATE=RUNNING" in out


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
        log("poll: %d instances complete, %d outstanding"
            % (len(done), sum(len(v) for v in outstanding.values())))
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
            ready, why = setup_state(session)
            if not ready:
                log("%s: %s" % (session, why))
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
