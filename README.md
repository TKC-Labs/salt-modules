# Custom salt modules for TKC Labs

This repository contains custom salt modules for use in TKC Labs

## Content

### Runners

Salt CI Tools: [modules/runners/citools.py](modules/runners/citools.py)

Provides utility functions that CI workfliws might find helpful which can be exposed from the salt-api runner client.

Functions:
  - `validate_pr `: Validate a PR by comparing the pillar data for the PR's target and incoming environments.
  - Other helper functions to make the advertised functions above work.
  - Dependencies: specific `git_pillar` configuration requirements need to be met.
