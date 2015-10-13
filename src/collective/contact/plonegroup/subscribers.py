# -*- coding: utf-8 -*-
from Acquisition import aq_get
from zope.component import getUtility
from zope.interface import alsoProvides, Interface, noLongerProvides
from zope.lifecycleevent.interfaces import IObjectRemovedEvent
from zope.schema import getFieldsInOrder
from zope.schema.interfaces import ICollection, IText, IChoice

from plone import api
from plone.behavior.interfaces import IBehavior
from plone.dexterity.interfaces import IDexterityContent, IDexterityFTI
from plone.app.linkintegrity.interfaces import ILinkIntegrityInfo
from plone.app.linkintegrity.handlers import referencedObjectRemoved as baseReferencedObjectRemoved

from Products.CMFPlone.utils import base_hasattr

from config import PLONEGROUP_ORG
from interfaces import IPloneGroupContact, INotPloneGroupContact

try:
    from plone.app.referenceablebehavior.referenceable import IReferenceable
except ImportError:
    class IReferenceable(Interface):
        pass


def plonegroupOrganizationRemoved(del_obj, event):
    """
        Store information about the removed organization integrity.
    """
    # inspired from z3c/relationfield/event.py:breakRelations
    # and plone/app/linkintegrity/handlers.py:referenceRemoved
    # if the object the event was fired on doesn't have a `REQUEST` attribute
    # we can safely assume no direct user action was involved and therefore
    # never raise a link integrity exception...
    request = aq_get(del_obj, 'REQUEST', None)
    if not request:
        return

    type_fields = {}
    uid = del_obj.UID()

    def list_fields(ptype, filter_interfaces=(IText, ICollection, IChoice)):
        if ptype not in type_fields:
            type_fields[ptype] = []
            fti = getUtility(IDexterityFTI, name=ptype)
            for name, fld in getFieldsInOrder(fti.lookupSchema()):
                for iface in filter_interfaces:
                    if iface.providedBy(fld):
                        type_fields[ptype].append(name)
                        break
            # also lookup behaviors
            for behavior_id in fti.behaviors:
                behavior = getUtility(IBehavior, behavior_id).interface
                for name, fld in getFieldsInOrder(behavior):
                    for iface in filter_interfaces:
                        if iface.providedBy(fld):
                            type_fields[ptype].append(name)
                            break
        return type_fields[ptype]

    storage = ILinkIntegrityInfo(request)
    catalog = api.portal.get_tool('portal_catalog')
    # we check all dexterity objects fields to see if object uid is used in
    # we can't check following vocabulary because:
    #   - maybe vocabulary not contains anymore the uid
    #   - maybe another vocabulary named differently is used
    # this can be long but this operation is not made so often

    def check_value(val):
        if isinstance(val, basestring) and val == uid:
            return True
        return False

    def test_value_type(val):
        if isinstance(val, dict):
            for v in val.values():
                res = test_value_type(v)
                if res:
                    return res
        elif base_hasattr(val, '__iter__'):
            for v in val:
                res = test_value_type(v)
                if res:
                    return res
        elif check_value(val):
            res = [val]
            return res
        return []

    for brain in catalog.searchResults(object_provides=IDexterityContent.__identifier__):
        obj = brain.getObject()
        if obj.id == 'test1':
            storage.addBreach(obj, del_obj)
        continue
        ptype = obj.portal_type
        for attr in list_fields(ptype):
            if base_hasattr(obj, attr):
                res = test_value_type(getattr(obj, attr))
                if res:
                    storage.addBreach(obj, del_obj)
                    break
    storage.getIntegrityBreaches()


def referencedObjectRemoved(obj, event):
    if not IReferenceable.providedBy(obj):
        baseReferencedObjectRemoved(obj, event)


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
