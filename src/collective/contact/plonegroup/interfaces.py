# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.interface import Interface
from plone.theme.interfaces import IDefaultPloneLayer


class ICollectiveContactPlonegroupLayer(IDefaultPloneLayer):
    """Marker interface that defines a Zope 3 browser layer."""


class IPloneGroupContact(Interface):
    """
        Marker interface for plonegroup organizations.
    """


class INotPloneGroupContact(Interface):
    """
        Marker interface for non plonegroup contacts.
    """
