# RGNODES™ Deep Repair Build v2

Applied against the supplied `main-main.zip` source and the supplied deployment logs/screenshots.

## Fixed regressions

- SSH configuration now performs an effective `sshd -T` check, unlocks the root account, and verifies a real port-22 listener before deployment is considered ready.
- The LXD port-forward implementation no longer attempts IPv4 `0.0.0.0:PORT` and IPv6 `[::]:PORT` simultaneously. When a verified global IPv6 exists, IPv6 listeners bind to that exact address.
- Persistent forwards that encounter a stale occupied host port are automatically moved to a free host port during rebuild/start instead of repeatedly failing with `address already in use`.
- Pinggy defaults to `free.pinggy.io:443` and uses the current TCP SSH reverse-tunnel pattern. Pinggy starts automatically after deployment; reconnect creates a fresh tunnel.
- The deployment selector no longer exposes the broken `images:debian/11` alias. Supported entries are Ubuntu 20.04/22.04/24.04 and Debian 12/13.
- Reinstall confirmation now carries `owner_id`, fixing the observed `ConfirmView` `AttributeError`.
- Dashboard controls remove `Reconnect SSHX` and the standalone `Pinggy` button. The remaining `SSHX` action starts a fresh session when requested; Pinggy is automatic/reconnect-only.
- Maintenance mode updates bot presence to a maintenance status and remains admin-only.

## Validation performed in the build container

- `python3 -m py_compile bot.py node-agent.py`
- `bash -n setup.sh install_node.sh selfchack.sh`
- `node --check ecosystem.config.js`
- `./selfchack.sh` → `RGNODES ultra self-check: PASS`

## Runtime boundary

The build container does not contain the user's real LXD host, provider network, Discord token, or external tunnel sessions. Therefore a live public SSH/Pinggy/SSHX connection cannot be truthfully claimed as tested here. The code is structured so primary SSH provisioning is fail-closed: the bot will not report a newly deployed VPS as ready if its guest SSH daemon or host forwarding did not pass local readiness checks.
