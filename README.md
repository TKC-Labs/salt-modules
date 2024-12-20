# Custom salt modules for TKC Labs

This repository contains custom salt modules for use in TKC Labs

## Content

### Runners

Salt CI Tools: [modules/runners/citools.py](modules/runners/citools.py)

Provides utility functions that CI workfliws might find helpful which can be exposed from the salt-api runner client.

Functions:
  - `validate_pillar_pr `: Validate a PR by comparing the pillar data for the PR's target and incoming environments.
  - Other helper functions to make the advertised functions above work.
  - Dependencies: specific `git_pillar` configuration requirements need to be met.

### Example output: validate_pillar_pr

This is a very minimal example where I added demo keys to a salt pillar repository to demonstrate the kind of output the `vaidate_pr` function can help create.

#### Salt Pillar Validation: `success`

```console
salt01.tkclabs.io:
    ----------
    salt:
        ----------
        demo_key01:
            added


ghar01.tkclabs.io:
    ----------
    ghar:
        ----------
        testing_key01:
            added
        testing_key02:
            added


ghar02.tkclabs.io:
    ----------
    ghar:
        ----------
        testing_key01:
            added
        testing_key02:
            added


salt-ci01.tkclabs.io:
    ----------
    salt:
        ----------
        demo_key01:
            added
```
