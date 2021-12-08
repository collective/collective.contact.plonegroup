# -*- coding: utf-8 -*-
from collective.contact.plonegroup import _

from Products.statusmessages.interfaces import IStatusMessage
from config import ORGANIZATIONS_REGISTRY
from plone import api
from plone.registry.interfaces import IRegistry
from zExceptions import Redirect
from zope.component import getMultiAdapter
from zope.component import getUtility
from .utils import search_value_in_objects


def plonegroup_contact_transition(contact, event):
    """
        React when a IPloneGroupContact transition is done
    """
    if event.transition and event.transition.id == 'deactivate':
        # check if the transition is selected
        registry = getUtility(IRegistry)
        errors = []
        if contact.UID() in registry[ORGANIZATIONS_REGISTRY]:
            errors.append(_('This contact is selected in configuration'))
        elif api.portal.get_registry_record('plone.enable_link_integrity_checks', default=False):
            breaches = search_value_in_objects(contact, contact.UID(), p_types=[], type_fields={})
            if len(breaches) > 0:
                errors.append(_("This contact is used in following content: ${items}",
                                mapping={'items': ', '.join(['<a href="%s" target="_blank">%s</a>'
                                                             % (i.absolute_url(), i.Title())
                                                             for i in breaches])}))
        if errors:
            smi = IStatusMessage(contact.REQUEST)
            smi.addStatusMessage(_('You cannot deactivate this item !'), type='error')
            smi.addStatusMessage(errors[0], type='error')
            view_url = getMultiAdapter((contact, contact.REQUEST), name=u'plone_context_state').view_url()
            raise Redirect(view_url)
