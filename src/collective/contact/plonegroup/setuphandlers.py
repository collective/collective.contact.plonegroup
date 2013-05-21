# -*- coding: utf-8 -*-
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from config import ORGANIZATIONS_REGISTRY, FUNCTIONS_REGISTRY


def postInstall(context):
    """Post install script"""
    if context.readDataFile("collective.contactplonegroup_marker.txt") is None:
        return
    portal = context.getSite()
    registry = getUtility(IRegistry)
    # Initialize the registry content
    registry[ORGANIZATIONS_REGISTRY] = []
    registry[FUNCTIONS_REGISTRY] = []
