#!/usr/bin/env python3
"""Release Colab VMs that the CLI can no longer address by name.

A container restart clears ~/.config/colab-cli/sessions.json, which holds the
name -> session mapping. The VMs themselves keep running on Google's side and
keep occupying the concurrent-assignment quota, so creating a replacement fails
with TooManyAssignmentsError and the replication stalls with no way forward.

This releases every assignment that has no entry in the local state file. It
reads nothing but endpoint identifiers, and authenticates through the CLI's own
client, so no credential is ever handled here.

Run with the CLI's interpreter, which has colab_cli importable:
    /home/user/colabenv/bin/python scripts/colab_release_orphans.py [--dry-run]
"""
import argparse
import sys

from colab_cli.common import State


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="list what would be released without releasing it")
    ap.add_argument("--config", default=None,
                    help="session state file to judge against; must be the one "
                         "the driver uses, or every assignment looks named")
    ap.add_argument("--include-unreachable", action="store_true",
                    help="also release assignments whose session is named "
                         "locally but no longer answers (Colab reclaimed it)")
    args = ap.parse_args()

    st = State()
    if args.config:
        st.config_path = args.config
    sessions = st.store.list()
    known = {v.endpoint for v in sessions.values()}

    if args.include_unreachable:
        # A reclaimed VM keeps its assignment, and so keeps its slot, while no
        # longer answering. It is still named locally, so it does not look
        # orphaned; only probing tells the difference.
        import subprocess, tempfile, os as _os
        probe = _os.path.join(tempfile.gettempdir(), "_reach_probe.py")
        with open(probe, "w") as f:
            f.write("print('REACH_OK')\n")
        for name, v in list(sessions.items()):
            cmd = ["/home/user/colabenv/bin/colab"]
            if args.config:
                cmd += ["--config", args.config]
            cmd += ["exec", "-s", name, "-f", probe, "--timeout", "60"]
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                alive = "REACH_OK" in (r.stdout or "") + (r.stderr or "")
            except subprocess.TimeoutExpired:
                alive = False
            if not alive:
                print("unreachable, will release:", name, v.endpoint)
                known.discard(v.endpoint)

    assignments = st.client.list_assignments()
    orphans = [a.endpoint for a in assignments if a.endpoint not in known]

    print("assignments: %d, named locally: %d, orphaned: %d"
          % (len(assignments), len(known), len(orphans)))
    for ep in orphans:
        if args.dry_run:
            print("would release", ep)
            continue
        try:
            st.client.unassign(ep)
            print("released", ep)
        except Exception as e:                      # keep going for the rest
            print("failed", ep, type(e).__name__, str(e)[:120])
    return 0


if __name__ == "__main__":
    sys.exit(main())
