# -*- coding: utf-8 -*-
from config import FUNCTIONS_REGISTRY
from config import ORGANIZATIONS_REGISTRY
from plone.registry.interfaces import IRegistry
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
        registry[FUNCTIONS_REGISTRY] = []
