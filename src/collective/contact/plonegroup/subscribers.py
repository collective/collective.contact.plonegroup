# -*- coding: utf-8 -*-
from collective.contact.plonegroup import _
from collective.contact.plonegroup.utils import get_all_suffixes

from Products.CMFPlone.utils import safe_unicode
from config import ORGANIZATIONS_REGISTRY
from config import PLONEGROUP_ORG
from interfaces import INotPloneGroupContact
from interfaces import IPloneGroupContact
from plone import api
from plone.registry.interfaces import IRegistry
from zExceptions import Redirect
from zope.component import getUtility
from zope.interface import alsoProvides
from zope.interface import noLongerProvides
from zope.lifecycleevent.interfaces import IObjectRemovedEvent



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


def group_deleted(event):
    """
        Raises exception if group cannot be deleted
    """
    group = event.principal
    portal = api.portal.get()
    request = portal.REQUEST

    parts = group.split('_')
    if len(parts) == 1:
        return
    group_suffix = '_'.join(parts[1:])
    registry = getUtility(IRegistry)
    if parts[0] in registry[ORGANIZATIONS_REGISTRY] and group_suffix in get_all_suffixes(parts[0]):
        orga = api.content.find(UID=parts[0])[0].getObject()
        api.portal.show_message(message=_("You cannot delete the group '${group}', linked to used organization "
                                          "'${orga}'.", mapping={'group': group, 'orga': safe_unicode(orga.Title())}),
                                request=request, type='error')
        raise Redirect(request.get('ACTUAL_URL'))
