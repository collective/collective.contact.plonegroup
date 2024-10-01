# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from plone.theme.interfaces import IDefaultPloneLayer
from Products.PluggableAuthService.interfaces.events import IPASEvent
from zope.interface import Interface


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


class IPlonegroupGroupCreatedEvent(IPASEvent):
    """
        A new Plone group linked to an organization has been created.
    """


class IGroupField(Interface):
    """
        Interface for the GroupField
    """


class IOrganizationField(Interface):
    """
        Interface for the OrganizationField
    """


class IDGFVocabularyField(Interface):
    """
        Interface for the DGFVocabularyField
    """


class IDGFListField(Interface):
    """
        Interface for the DGFListField
    """
