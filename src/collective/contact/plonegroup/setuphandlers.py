# -*- coding: utf-8 -*-

from collective.contact.plonegroup import logger
from collective.contact.plonegroup.browser.settings import invalidate_soev_cache
from collective.contact.plonegroup.browser.settings import invalidate_ssoev_cache
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
    # set the vocabularies cache keys now: computed on a GET page, it is a write refused by plone.protect
    invalidate_soev_cache()
    invalidate_ssoev_cache()
    if registry[FUNCTIONS_REGISTRY] is None:
        # may fail in tests because a datagridfield is stored, just pass in this case
        try:
            registry[FUNCTIONS_REGISTRY] = []
        except ConnectionStateError:
            logger.warning("!!!Failed to set registry functions to []!!!")
            registry.records[FUNCTIONS_REGISTRY].field.value_type = None
