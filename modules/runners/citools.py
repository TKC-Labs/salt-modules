"""
Salt runner module providing CI tools and utilities.

Provides utility functions that CI workflows might find helpful which can be exposed from the salt-api runner client.
"""

import logging

import salt.config
import salt.loader
import salt.pillar

log = logging.getLogger(__name__)


def get_pillar_for_env(minion_id, pillarenv):
    """
    Get the pillar data for a minion in a specific environment.

    Args:
        minion_id (str): The minion ID.
        env (str): The environment.

    Returns:
        dict: The pillar data.
    """
    opts = salt.config.master_config("/etc/salt/master")

    opts["pillarenv"] = pillarenv
    grains = salt.loader.grains(opts)
    pillar = salt.pillar.Pillar(opts, grains, minion_id, pillarenv)
    pillar_data = pillar.compile_pillar()

    return pillar_data


def determine_changes(target_pillarenv, incoming_pillarenv, path=None):
    """
    Compare the pillar data for a minion in two different environments.

    Args:
        target_pillarenv (str): The target environment.
        incoming_pillarenv (str): The incoming environment.

    Returns:
        dict: The differences between the two environments.
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
            changes[key] = "added"

    return changes


def remove_unchanged(data):
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
    changes = remove_unchanged(compared_pillar)
    return changes
