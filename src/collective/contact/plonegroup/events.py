# -*- coding: utf-8 -*-

from collective.contact.plonegroup.interfaces import IPlonegroupGroupCreatedEvent
from Products.PluggableAuthService.events import PASEvent
from zope.interface import implementer


@implementer(IPlonegroupGroupCreatedEvent)
class PlonegroupGroupCreatedEvent(PASEvent):
    pass
