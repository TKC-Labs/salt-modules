"""
Salt runner module providing a place to test various module operations.

Logic and operations are often tested in this module before being added
to a live module.
"""

import logging
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

