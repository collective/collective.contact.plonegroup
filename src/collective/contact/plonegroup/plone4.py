# -*- coding: utf-8 -*-
from collective.contact.plonegroup import _

from Products.statusmessages.interfaces import IStatusMessage
from config import ORGANIZATIONS_REGISTRY
from plone import api
from plone.app.linkintegrity.handlers import referencedObjectRemoved as baseReferencedObjectRemoved
from plone.app.linkintegrity.interfaces import ILinkIntegrityInfo
from plone.registry.interfaces import IRegistry
from zExceptions import Redirect
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.interface import Interface
from .utils import search_value_in_objects

try:
    from plone.app.referenceablebehavior.referenceable import IReferenceable
except ImportError:
    class IReferenceable(Interface):
        pass


def mark_value_in_objects_as_breaches(s_obj, ref, p_types=[], type_fields={}):
    objects = search_value_in_objects(s_obj, ref, p_types=p_types, type_fields=type_fields)
    storage = ILinkIntegrityInfo(s_obj)
    for o in objects:
        storage.addBreach(o, s_obj)


def plonegroupOrganizationRemoved(del_obj, event):
    """
        Store information about the removed organization integrity.
    """
    # inspired from z3c/relationfield/event.py:breakRelations
    # and plone/app/linkintegrity/handlers.py:referenceRemoved
    try:
        pp = api.portal.get_tool('portal_properties')
    except api.portal.CannotGetPortalError:
        # When deleting site, the portal is no more found...
        return
    if pp.site_properties.enable_link_integrity_checks:
        mark_value_in_objects_as_breaches(del_obj, del_obj.UID(), p_types=[], type_fields={})


def referencedObjectRemoved(obj, event):
    if not IReferenceable.providedBy(obj):
        baseReferencedObjectRemoved(obj, event)


def plonegroup_contact_transition(contact, event):
    """
        React when a IPloneGroupContact transition is done
    """
    if event.transition and event.transition.id == 'deactivate':
        # check if the transition is selected
        registry = getUtility(IRegistry)
        pp = api.portal.get_tool('portal_properties')
        errors = []
        if contact.UID() in registry[ORGANIZATIONS_REGISTRY]:
            errors.append(_('This contact is selected in configuration'))
        elif pp.site_properties.enable_link_integrity_checks:
            mark_value_in_objects_as_breaches(contact, contact.UID(), p_types=[], type_fields={})
            storage = ILinkIntegrityInfo(contact.REQUEST)
            breaches = storage.getIntegrityBreaches()
            if contact in breaches:
                errors.append(_("This contact is used in following content: ${items}",
                                mapping={'items': ', '.join(['<a href="%s" target="_blank">%s</a>'
                                                             % (i.absolute_url(), i.Title())
                                                             for i in breaches[contact]])}))
        if errors:
            smi = IStatusMessage(contact.REQUEST)
            smi.addStatusMessage(_('You cannot deactivate this item !'), type='error')
            smi.addStatusMessage(errors[0], type='error')
            view_url = getMultiAdapter((contact, contact.REQUEST), name=u'plone_context_state').view_url()
            # contact.REQUEST['RESPONSE'].redirect(view_url)
            raise Redirect(view_url)
