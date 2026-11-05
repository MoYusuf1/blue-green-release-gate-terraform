# 2. Promotion and rollback change routing, not containers

## Context
Blue-green only pays off if switching back is fast and doesn't rebuild the previous release.

## Decision
Each release has its own config file and container, replaced only when that release changes (`replace_triggered_by`). The proxy mounts a config directory and is never replaced on a color change; `reload_proxy.py` activates the new file. Tests assert the routing in plan.

## Consequences
A color change plans as one file replacement with no container replaced. It also means `terraform apply` alone doesn't move traffic: activation is a separate, verified step.
