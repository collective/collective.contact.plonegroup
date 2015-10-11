# -*- coding: utf-8 -*-
from Acquisition import aq_get
from zope.interface import alsoProvides, noLongerProvides
from zope.lifecycleevent.interfaces import IObjectRemovedEvent

from plone import api
from plone.dexterity.interfaces import IDexterityContent
from plone.app.linkintegrity.interfaces import ILinkIntegrityInfo

from config import PLONEGROUP_ORG
from interfaces import IPloneGroupContact, INotPloneGroupContact


def plonegroupOrganizationRemoved(obj, event):
    """
        Store information about the removed organization integrity.
    """
    # inspired from z3c/relationfield/event.py:breakRelations
    # and plone/app/linkintegrity/handlers.py:referenceRemoved
    # if the object the event was fired on doesn't have a `REQUEST` attribute
    # we can safely assume no direct user action was involved and therefore
    # never raise a link integrity exception...
    request = aq_get(obj, 'REQUEST', None)
    if not request:
        return
    storage = ILinkIntegrityInfo(request)
    catalog = api.portal.get_tool('portal_catalog')
    for brain in catalog.searchResults(object_provides=IDexterityContent):
        pass
#            storage.addBreach(rel.from_object, rel.to_object)


def mark_organization(contact, event):
    """ Set a marker interface on contact content. """
    if IObjectRemovedEvent.providedBy(event):
        return
    if '/%s' % PLONEGROUP_ORG in contact.absolute_url_path():
        if not IPloneGroupContact.providedBy(contact):
            alsoProvides(contact, IPloneGroupContact)
        if INotPloneGroupContact.providedBy(contact):
            noLongerProvides(contact, INotPloneGroupContact)
    else:
        if not INotPloneGroupContact.providedBy(contact):
            alsoProvides(contact, INotPloneGroupContact)
        if IPloneGroupContact.providedBy(contact):
            noLongerProvides(contact, IPloneGroupContact)

    contact.reindexObject(idxs='object_provides')
