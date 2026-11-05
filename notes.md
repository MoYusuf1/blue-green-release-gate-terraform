# Lab notes

Observed values only. Write "not measured" for anything you didn't capture. Times are from the terminal output (GMT).

## Run 1 · 2026-11-05

- Candidate failure: Green v2-bad answered `/health` **200** and `/quote` **200** with `total_cents=999`; the check **FAILED** (`expected 1200`). Blue still **PASSED**. (17:33:03 GMT, `screenshots/3.png`)
- Promote plan: `1 to add, 0 to change, 1 to destroy`, only the proxy config file; no container replaced. (`screenshots/5.png`)
- Curl between promote apply and reload showed: **blue**.
- Surprise: the curl right **after** the reload also showed **blue**, and the Green check **FAILED** on color and version. The reload had been requested (17:35:01 GMT) but hadn't taken effect yet. A moment later live traffic was Green. Same on rollback (17:37:17 GMT): the first check still saw Green. (`screenshots/12.png`, `screenshots/13.png`)
- What I changed: `reload_proxy.py` now waits until live traffic actually reaches the configured color before saying it's done.
- Live failure: health **200**, check **FAILED** with `total_cents=999` (17:36:06 GMT, `screenshots/7.png`).
- Rollback decision time: not measured.
- First recovered Blue PASS time: not measured.
- Probe summary: not measured (`evidence/run.jsonl` was not saved).

## Run 2 (redo from 0:45) · 2026-11-05

- Reload output: first curl **blue**, reload waited, then `Live traffic now reaches green`, second curl **green**, check **PASSED** (reload 17:44:35 GMT, `screenshots/6.png`).
- Promoted live response (`evidence/promoted-green.json`): `{"color":"green","version":"v2","total_cents":1200}`.
- Live failure: first wrong quote seen by the probe at **17:45:27.673 GMT**; health stayed **200** the whole time (`screenshots/11.png`).
- Rollback decision time: not measured.
- Rollback reload: 17:46:28 GMT; the check **PASSED** right after (`screenshots/8.png`).
- First recovered sample: **17:46:29.723 GMT**. Last wrong quote: 17:46:28.723 GMT.
- Wrong answers were live for about **61 seconds**, from the first wrong quote to the first correct one. That includes my time noticing and deciding, not just the rollback.
- Probe summary: **118 samples, 62 failed, 62 wrong_total, 0 http_or_connection** (`evidence/run.jsonl`).
- The point of the lab, in one number: **0 HTTP errors** during 62 wrong answers. An HTTP-only monitor would have seen nothing.
- Cleanup: `8 destroyed`, no containers left (`screenshots/10.png`).
