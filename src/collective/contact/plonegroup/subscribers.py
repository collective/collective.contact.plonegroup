# -*- coding: utf-8 -*-

from Products.CMFPlone.utils import safe_unicode
from collective.contact.plonegroup import _
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.config import get_registry_organizations
from collective.contact.plonegroup.interfaces import INotPloneGroupContact
from collective.contact.plonegroup.interfaces import IPloneGroupContact
from collective.contact.plonegroup.utils import get_all_suffixes
from plone import api
from zExceptions import Redirect
from zope.interface import Interface
from zope.interface import alsoProvides
from zope.interface import noLongerProvides
from zope.lifecycleevent.interfaces import IObjectRemovedEvent

try:
    from plone.app.referenceablebehavior.referenceable import IReferenceable
except ImportError:
    class IReferenceable(Interface):
        pass


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
    org_uid = parts[0]
    group_suffix = '_'.join(parts[1:])
    if org_uid in get_registry_organizations() and group_suffix in get_all_suffixes(org_uid):
        orga = api.content.find(UID=org_uid)[0].getObject()
        api.portal.show_message(message=_("You cannot delete the group '${group}', linked to used organization "
                                          "'${orga}'.", mapping={'group': group, 'orga': safe_unicode(orga.Title())}),
                                request=request, type='error')
        raise Redirect(request.get('ACTUAL_URL'))
