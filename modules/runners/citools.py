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


def compare_incoming_to_target(target_pillarenv, incoming_pillarenv, path=None):
    """
    Compare the pillar data for a minion in two different environments.

    Args:
        target_pillarenv (str): The target environment.
        incoming_pillarenv (str): The incoming environment.
        path (str): The path to compare. If None, the entire pillar will be compared.

    Returns:
        dict: The differences between the two environments.
    """
    if path is None:
        path = []

    changes = []
    for key in target_pillarenv.keys():
        if key not in incoming_pillarenv:
            if path:
                changes.append(":".join(path + [key]) + ";removed")
                continue

        if key in incoming_pillarenv:
            if isinstance(target_pillarenv[key], dict):
                changes.extend(
                    compare_incoming_to_target(
                        target_pillarenv[key], incoming_pillarenv[key], path + [key]
                    )
                )
                continue

            if target_pillarenv[key] != incoming_pillarenv[key]:
                changes.append(":".join(path + [key]) + ";modified")

    for key in incoming_pillarenv.keys():
        if key not in target_pillarenv:
            if path:
                # Skipping top level keys, added minions output elsewhere
                changes.append(":".join(path + [key]) + ";added")

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

    return compare_incoming_to_target(target_pillar, incoming_pillar)
