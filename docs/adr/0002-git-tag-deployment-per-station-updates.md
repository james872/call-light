# Git clone + release tags for delivery, with per-station updates only

The first-run install script and the web-UI update feature share one delivery mechanism: clone the GitHub repo and check out the newest release tag (install), or fetch and check out the newest tag (update). Releases are deliberate — tag = ship — the tip of `main` is never deployed, and rollback is checking out the previous tag. The root `VERSION` file must match the release tag; the updater can verify this.

Updating is strictly per-station: each Station's web UI shows "Update available" when a newer tag exists (internet permitting) and its Update button updates only that Station. A fleet-wide "update everyone" button was rejected because it means stations executing code on a peer's instruction over an unauthenticated stage network, and a mid-update failure could take down stations nobody is standing next to. Auto-update-on-boot was rejected because a surprise breaking release must never land unattended on the morning of a gig. Partial upgrades are expected and safe: the protocol version field (ADR 0001 family) makes lagging Stations visible as "Incompatible — update required" rather than silently broken.

## Considered Options

- **GitHub Release tarballs** — no git dependency on the Pi, but hand-rolls the versioning, atomic swap, and rollback that git provides. Rejected.
- **pip/PyPI packaging** — clean Python story, but adds a publish step to every release of a personal project. Rejected.
- **Fleet update / auto-update on boot** — rejected for the reasons above; the explicit no is the point of this ADR.
