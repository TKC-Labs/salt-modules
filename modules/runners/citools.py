"""
Salt runner module providing CI tools and utilities.

Provides utility functions that CI workflows might find helpful which can be exposed from the salt-api runner client.
"""

import logging

# This lets us python -m pydoc modules/runners/citools.py and not need
# to worry about the salt dependency in the available python environment.
try:
    import salt.config
    import salt.loader
    import salt.pillar
except ImportError:
    salt = None

log = logging.getLogger(__name__)


def _remove_unchanged(data):
    """
    Removes dict tree nodes that are marked as "unchanged".

    This is a helper function to adjust the final output produced by the
    validate_pr function.

    Args:
        data (dict): The dictionary to remove unchanged nodes from.

    Returns:
        dict: The dictionary with unchanged nodes removed.
    """
    if isinstance(data, dict):
        keys_to_remove = []
        for key, value in data.items():
            if isinstance(value, dict):
                remove_unchanged(value)
                if not value:  # if the dictionary is empty after removing unchanged
                    keys_to_remove.append(key)
            elif value == "unchanged":
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del data[key]
    return data


def get_pillar_for_env(minion_id, pillarenv):
    """
    Get the pillar data for a minion in a specific environment.

    Args:
        minion_id (str): The minion ID. (hostname, fqdn, etc.)
        env (str): The environment. (base, dev.<change_id>)

          In salt the "base" environment often maps to either the "main" or
          "master" branch. Other environments can be statically mapped to
          branches but using dynamic __env__ mapping is better for CI
          purposes.

    Returns:
        dict: The rendered pillar data for the minion_id and pillarenv
    """
    opts = salt.config.master_config("/etc/salt/master")

    opts["pillarenv"] = pillarenv
    grains = salt.loader.grains(opts)
    pillar = salt.pillar.Pillar(opts, grains, minion_id, pillarenv)
    pillar_data = pillar.compile_pillar()

    return pillar_data


def determine_changes(target_pillarenv, incoming_pillarenv):
    """
    Compare the pillar data for a minion in two different environments.

    Args:
        target_pillarenv (dict): A dict of the pillar rendered for the
          target pillar environment / branch.

          Example:
            .. code-block:: python
            {
                "ghar01.tkclabs.io": {
                    "common": {
                        "demo_key01": "demo_key01_value01",
                        "demo_key02": {
                            "demo_nestedkey01": "demo_nestedkey01_value",
                            "demo_nestedkey02": "demo_nestedkey02_value"
                        },
                        "demo_key04": "demo_key04_value01"
                    },
                    "ghar": {
                        "lookup": {
                            "token": "REDACTED"
                        },
                        "demo_key01": "demo_key01_value01",
                        "demo_key02": {
                            "demo_nestedkey01": "demo_nestedkey01_value",
                            "demo_nestedkey02": "demo_nestedkey02_value"
                        }
                    }
                },
                "salt01.tkclabs.io": {
                    "common": {
                        "demo_key01": "demo_key01_value01",
                        "demo_key02": {
                            "demo_nestedkey01": "demo_nestedkey01_value",
                            "demo_nestedkey02": "demo_nestedkey02_value"
                        },
                        "demo_key04": "demo_key04_value01"
                    },
                    "salt": {
                        "lookup": {
                            "master": "salt.tkclabs.io",
                            "salt_api": {
                                "certificate_contents": "SomeCertContent",
                                "private_key_contents": "SomePrivKeyContent"
                            }
                        }
                    }
                }
            }

        incoming_pillarenv (dict): A dict of the pillar rendered for the
          incoming pillar environment / branch.

          Example:
            .. code-block:: python
            {
                "ghar01.tkclabs.io": {
                    "common": {
                        "demo_key01": "demo_key01_value01 modified",
                        "demo_key02": {
                            "demo_nestedkey01": "demo_nestedkey01_value",
                            "demo_nestedkey02": "demo_nestedkey02_value",
                            "demo_nestedkey02": "demo_nestedkey02_value added"
                        },
                        "demo_key04": "demo_key04_value01"
                    },
                    "ghar": {
                        "lookup": {
                            "token": "REDACTED"
                        },
                        "demo_key01": "demo_key01_value01",
                        "demo_key02": {
                            "demo_nestedkey01": "demo_nestedkey01_value",
                            "demo_nestedkey02": "demo_nestedkey02_value"
                        }
                    }
                },
                "salt01.tkclabs.io": {
                    "common": {
                        "demo_key01": "demo_key01_value01",
                        "demo_key02": {
                            "demo_nestedkey01": "demo_nestedkey01_value",
                            "demo_nestedkey02": "demo_nestedkey02_value"
                        },
                        "demo_key04": "demo_key04_value01"
                    },
                    "salt": {
                        "lookup": {
                            "master": "salt.tkclabs.io",
                            "salt_api": {
                                "certificate_contents": "SomeCertContent",
                                "private_key_contents": "SomePrivKeyContent"
                            }
                        },
                        "demo_key01": "demo_key01_value01",
                        "demo_key02": {
                            "demo_nestedkey01": "demo_nestedkey01_value",
                            "demo_nestedkey02": "demo_nestedkey02_value"
                    }
                }
            }

    Returns:
        dict: The differences between the two environments.

    Example:
        .. code-block:: python
        {'ghar01.tkclabs.io': {'common': {'demo_key01': 'unchanged',
                                        'demo_key02': {'demo_nestedkey01': 'unchanged',
                                                        'demo_nestedkey02': 'modified',
                                                        'demo_nestedkey03': 'added'},
                                        'demo_key04': 'unchanged'},
                            'ghar': {'demo_key01': 'unchanged',
                                        'demo_key02': {'demo_nestedkey01': 'unchanged',
                                                    'demo_nestedkey02': 'unchanged'},
                                        'lookup': {'token': 'unchanged'}}},
        'ghar02.tkclabs.io': {'common': {'demo_key01': 'unchanged',
                                        'demo_key02': {'demo_nestedkey01': 'unchanged',
                                                        'demo_nestedkey02': 'modified',
                                                        'demo_nestedkey03': 'added'},
                                        'demo_key04': 'unchanged'},
                            'ghar': {'demo_key01': 'unchanged',
                                        'demo_key02': {'demo_nestedkey01': 'unchanged',
                                                    'demo_nestedkey02': 'unchanged'},
                                        'lookup': {'token': 'unchanged'}}},
        'ghar03.tkclabs.io': {'common': {'demo_key01': 'unchanged',
                                        'demo_key02': {'demo_nestedkey01': 'unchanged',
                                                        'demo_nestedkey02': 'unchanged'},
                                        'demo_key04': 'unchanged'},
                            'ghar': {'demo_key01': 'unchanged',
                                        'demo_key02': {'demo_nestedkey01': 'unchanged',
                                                    'demo_nestedkey02': 'unchanged'},
                                        'lookup': {'token': 'unchanged'}}},
        'salt01.tkclabs.io': {'common': {'demo_key01': 'unchanged',
                                        'demo_key02': {'demo_nestedkey01': 'unchanged',
                                                        'demo_nestedkey02': 'modified',
                                                        'demo_nestedkey03': 'added'},
                                        'demo_key04': 'unchanged'},
                            'salt': {'demo_key01': 'added',
                                        'demo_key02': {'demo_nestedkey01': 'added',
                                                    'demo_nestedkey02': 'added'},
                                        'lookup': {'master': 'modified',
                                                'salt_api': {'certificate_contents': 'unchanged',
                                                                'private_key_contents': 'unchanged'}}}}}

    """
    changes = {}

    for key in target_pillarenv.keys():
        if key not in incoming_pillarenv:
            changes[key] = "removed"
            continue

        if key in incoming_pillarenv:
            if isinstance(target_pillarenv[key], dict):
                changes[key] = {}
                changes[key].update(
                    determine_changes(target_pillarenv[key], incoming_pillarenv[key])
                )
                continue

            if target_pillarenv[key] != incoming_pillarenv[key]:
                changes[key] = "modified"
            else:
                # del changes[key]
                changes[key] = "unchanged"

    for key in incoming_pillarenv.keys():
        if key not in target_pillarenv:
            if isinstance(incoming_pillarenv[key], dict):
                changes[key] = {}
                for sub_key in incoming_pillarenv[key].keys():
                    changes[key][sub_key] = "added"
            else:
                changes[key] = "added"

    return changes


def validate_pr(minion_ids, target_pillarenv, incoming_pillarenv):
    """
    Validate a PR by comparing the pillar data for the PR's target and incoming environments.

    Args:
        minion_ids (list): The minion IDs to validate.

    Returns:
        dict: The differences between the two environments.

    CLI Example:

      Check for any differences between the base and dev.change_common_pillar
      pillar environments for the web01.local and srv01.local minions

    .. code-block:: bash
     salt-run citools.validate_pr '[web01.local,srv01.local]' base dev.change_common_pillar

    """
    target_pillar = {}
    incoming_pillar = {}

    for id in minion_ids:
        target_pillar_content = get_pillar_for_env(id, target_pillarenv)
        incoming_pillar_content = get_pillar_for_env(id, incoming_pillarenv)

        target_pillar[id] = target_pillar_content
        incoming_pillar[id] = incoming_pillar_content

    compared_pillar = determine_changes(target_pillar, incoming_pillar)
    changes = _remove_unchanged(compared_pillar)
    return changes
