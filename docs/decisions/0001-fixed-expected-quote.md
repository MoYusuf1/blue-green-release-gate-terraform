# 1. The release check's expected quote is fixed in code

## Context
The app's quote comes from `lab.auto.tfvars.json`. If the check read the same value, a bad config would change the expectation along with the answer, and a wrong release would pass.

## Decision
`check_release.py` expects `total_cents == 1200`, hard-coded and independent of any config. `set_release.py` can change the app but never the expectation.

## Consequences
Changing the correct quote is a reviewed code change to the check, not a config edit. That's the point: the test and the thing under test can't drift together.
