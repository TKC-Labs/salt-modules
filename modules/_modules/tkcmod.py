"""
Salt execution module providing a place to test various module operations.

Logic and operations are often tested in this module before being added
to a live module.
"""

import logging
from salt.exceptions import SaltInvocationError

__virtualname__ = 'tkcmod'
log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def test():
    """
    Testing config.get and outputing values in a runner module.
    """
    config = __salt__["config.get"]("tkcmod", {})
    return config


def test_param(minion_id=None):
    """
    Testing config.get and outputing values in a runner module.
    """
    if minion_id == None:
        raise SaltInvocationError("minion_id parameter is required")


    config = __salt__["config.get"]("tkcmod", {})
    ret = {}
    ret[minion_id] = config

    return ret

