# -*- coding: utf-8 -*-

from collective.contact.plonegroup import logger
from collective.contact.plonegroup.config import FUNCTIONS_REGISTRY
from collective.contact.plonegroup.config import ORGANIZATIONS_REGISTRY
from plone.registry.interfaces import IRegistry
from ZODB.POSException import ConnectionStateError
from zope.component import getUtility


def postInstall(context):
    """Post install script"""
    if context.readDataFile("collective.contactplonegroup_marker.txt") is None:
        return
    registry = getUtility(IRegistry)
    # Initialize the registry content if nothing is stored
    if registry[ORGANIZATIONS_REGISTRY] is None:
        registry[ORGANIZATIONS_REGISTRY] = []
    if registry[FUNCTIONS_REGISTRY] is None:
        # may fail in tests because a datagridfield is stored, just pass in this case
        try:
            registry[FUNCTIONS_REGISTRY] = []
        except ConnectionStateError:
            logger.warn('!!!Failed to set registry functions to []!!!')
            registry.records[FUNCTIONS_REGISTRY].field.value_type = None
