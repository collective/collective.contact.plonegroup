# -*- coding: utf-8 -*-
import logging
from zope.interface import alsoProvides
from plone import api

from ..config import PLONEGROUP_ORG
from ..interfaces import IPloneGroupContact, INotPloneGroupContact

logger = logging.getLogger('collective.contact.plonegroup: upgrade. ')


def v2(context):
    catalog = api.portal.get_tool('portal_catalog')
    brains = catalog.searchResults({'object_provides': 'collective.contact.widget.interfaces.IContactContent'})
    for brain in brains:
        obj = brain.getObject()
        if '/%s' % PLONEGROUP_ORG in obj.absolute_url_path():
            if not IPloneGroupContact.providedBy(obj):
                alsoProvides(obj, IPloneGroupContact)
        elif not INotPloneGroupContact.providedBy(obj):
            alsoProvides(obj, INotPloneGroupContact)

        obj.reindexObject(idxs='object_provides')
    setup = api.portal.get_tool('portal_setup')
    setup.runImportStepFromProfile('profile-collective.contact.plonegroup:default', 'jsregistry')
