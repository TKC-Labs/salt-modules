"""
Salt runner module providing CI tools and utilities.

Provides utility functions that CI workflows might find helpful which can be exposed from the salt-api runner client.
"""
import logging
from pprint import pprint

# This lets us python -m pydoc modules/runners/citools.py and not need
# to worry about the salt dependency in the available python environment.
try:
    import salt.config
    import salt.loader
    import salt.pillar
except ImportError:
    salt = None

log = logging.getLogger(__name__)


def _determine_pillar_changes(target_pillarenv, incoming_pillarenv):
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
                    _determine_pillar_changes(
                        target_pillarenv[key], incoming_pillarenv[key]
                    )
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


def _remove_unchanged_pillar(data):
    """
    Removes dict tree nodes that are marked as "unchanged".

    This is a helper function to adjust the final output produced by the
    validate_pillar_pr function.

    Args:
        data (dict): The dictionary to remove unchanged nodes from.

    Returns:
        dict: The dictionary with unchanged nodes removed.
    """
    if isinstance(data, dict):
        keys_to_remove = []
        for key, value in data.items():
            if isinstance(value, dict):
                _remove_unchanged_pillar(value)
                if not value:  # if the dictionary is empty after removing unchanged
                    keys_to_remove.append(key)
            elif value == "unchanged":
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del data[key]
    return data


def update_local_git_content():
    """Attempt to get the latest Git content

    This function will attempt to update the fileserver and git_pillar
    content by running the fileserver.update and git_pillar.update
    """
    opts = salt.config.master_config("/etc/salt/master")

    # Run a fileserver.update
    opts["fun"] = "fileserver.update"
    opts["arg"] = []  # No arguments
    runner = salt.runner.Runner(opts)
    runner.run()

    # Run a git_pillar.update
    opts["fun"] = "git_pillar.update"
    opts["arg"] = []  # No arguments
    runner = salt.runner.Runner(opts)
    runner.run()


def get_lowstate_for_env(minion_id, saltenv):
    """
    Get the lowstate data for a minion in a specific environment.

    Args:
        minion_id (str): The minion ID. (hostname, fqdn, etc.)
        saltenv (str): The environment. (base, dev.<change_id>)

    Returns:
        list: The lowstate ids for the minion_id and saltenv
    """
    opts = salt.config.master_config("/etc/salt/master")

    opts["saltenv"] = saltenv
    grains = salt.loader.grains(opts)
    pillar = salt.pillar.Pillar(opts, grains, minion_id, saltenv)
    pillar.compile_pillar()

    # Create a state object and gather the lowstate
    state = salt.state.HighState(opts)
    low_chunks = state.compile_low_chunks()
    pprint(low_chunks)

    # Gather just the state_ids that are in the saltenv
    state_ids_to_run = [
        item["__id__"] for item in low_chunks if item.get("__env__", None) == saltenv
    ]

    return state_ids_to_run


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


def validate_pillar_pr(minion_ids, target_pillarenv, incoming_pillarenv):
    """
    Validate a pillar PR by comparing the pillar data for the PR's target and incoming environments.

    Args:
        minion_ids (list): The minion IDs to validate.

    Returns:
        dict: The differences between the two environments.

    CLI Example:

      Check for any differences between the base and dev.change_common_pillar
      pillar environments for the web01.local and srv01.local minions

    .. code-block:: bash
     salt-run citools.validate_pillar_pr '[web01.local,srv01.local]' base dev.change_common_pillar

    """
    target_pillar = {}
    incoming_pillar = {}

    for id in minion_ids:
        target_pillar_content = get_pillar_for_env(id, target_pillarenv)
        incoming_pillar_content = get_pillar_for_env(id, incoming_pillarenv)

        target_pillar[id] = target_pillar_content
        incoming_pillar[id] = incoming_pillar_content

    compared_pillar = _determine_pillar_changes(target_pillar, incoming_pillar)
    changes = _remove_unchanged_pillar(compared_pillar)
    return changes


def validate_state_pr(minion_ids, target_saltenv, incoming_saltenv):
    """ 
    Validate a state PR by comparing the lowstate data for the PR's target and incoming environments.
    """
    lowstate_changes = {}

    for id in minion_ids:
        target_lowstate_content = get_lowstate_for_env(id, target_saltenv)
        incoming_lowstate_content = get_lowstate_for_env(id, incoming_saltenv)

        state_ids_added = set(incoming_lowstate_content) - set(target_lowstate_content)
        state_ids_removed = set(target_lowstate_content) - set(
            incoming_lowstate_content
        )

        lowstate_changes[id] = {}
        if len(state_ids_added) > 0:
            lowstate_changes[id]["added"] = list(state_ids_added)
        if len(state_ids_removed) > 0:
            lowstate_changes[id]["removed"] = list(state_ids_removed)

    return lowstate_changes
