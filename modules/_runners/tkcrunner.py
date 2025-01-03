"""
Salt runner module providing a place to test various module operations.

Logic and operations are often tested in this module before being added
to a live module.
"""

import logging

import salt.loader
from salt.exceptions import SaltInvocationError


log = logging.getLogger(__name__)


def test():
    """
    Testing config.get and outputing values in a runner module.
    """
    config = __salt__["config.get"]("tkcrunner", {})
    return config


def test_param(minion_id=None):
    """
    Testing config.get and outputing values in a runner module.
    """
    if minion_id == None:
        raise SaltInvocationError("minion_id parameter is required")


    config = __salt__["config.get"]("tkcrunner", {})
    ret = {}
    ret[minion_id] = config

    return ret


def tkcmod_test():
    """
    Load and use an execution module from a runner module.
    """
    mods = salt.loader.minion_mods(__opts__)
    return mods["tkcmod.test"]()


def tkcmod_test_param(minion_id):
    """
    Load and use an execution module from a runner module.
    """
    mods = salt.loader.minion_mods(__opts__)
    return mods["tkcmod.test_param"](minion_id)
