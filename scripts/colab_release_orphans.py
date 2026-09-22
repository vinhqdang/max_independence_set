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
    args = ap.parse_args()

    st = State()
    known = {s.endpoint for s in st.store.list().values()}

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
