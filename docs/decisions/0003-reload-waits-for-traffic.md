# 3. A reload is done when traffic moves, not when NGINX accepts it

## Context
On the first run the check right after `nginx -s reload` still reached the old release and failed. NGINX reloads gracefully: new workers start while old ones finish, so the signal returns before traffic switches.

## Decision
`reload_proxy.py` runs `nginx -t`, reloads, then polls the live address until it returns the configured color, for up to 15 seconds, and fails if it doesn't.

## Consequences
The script's success message now means what it says. The release check still runs afterwards; the reload proves routing, the check proves correctness.
