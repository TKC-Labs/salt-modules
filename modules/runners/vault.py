"""
Salt runner module providing HashiCorp Vault tools and utilities.

Provides utility functions for interacting with Vault from the salt controller.
"""

import logging

import hvac
import salt.config
import salt.loader
import salt.pillar

log = logging.getLogger(__name__)


def _get_vault_client():
    """
    Return a Vault client object.
    """

    vault_defaults = {
        "url": "http://vault.local:8200",
        "token": 'root',
        "verify": False,
    }

    config = __salt__['config.get']("vault", vault_defaults)
    client = hvac.Client(**config)
    
    return client



def read_secret(path, key=None):
    """
    Read a secret from Vault.

    path
        The path to the secret in Vault.

    key
        The key within the secret to return. If not provided, the entire secret
        will be returned.
    """

    vault = _get_vault_client()

    if vault.is_authenticated():
       vault.secrets.kv.default_kv_version = 2
       response = vault.secrets.kv.read_secret(path=path, mount_point='kv')

       # TODO: Add key handling and such next

    return response
