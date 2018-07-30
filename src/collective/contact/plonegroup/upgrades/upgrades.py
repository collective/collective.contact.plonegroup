# -*- coding: utf-8 -*-
from collective.contact.plonegroup.config import FUNCTIONS_REGISTRY
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.interfaces import INotPloneGroupContact
from collective.contact.plonegroup.interfaces import IPloneGroupContact
from plone import api
from plone.app.uuid.utils import uuidToObject
from zope.interface import alsoProvides

import logging


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


def v3(context):
    logger.info("Migrate to v3")
    portal = api.portal.getSite()
    pg = portal.portal_groups
    sg = portal.acl_users.source_groups
    reg = api.portal.get_registry_record(name=FUNCTIONS_REGISTRY)
    functions = {}
    for dic in reg:
        functions[dic['fct_id']] = dic['fct_title']
    for group in api.group.get_groups():
        if '_' not in group.id:
            continue
        parts = group.id.split('_')
        org_uid = parts[0]
        function = '_'.join(parts[1:])
        org = uuidToObject(org_uid)
        if not org or function not in functions:
            continue
        full_title = org.get_full_title(separator=' - ', first_index=1)
        group_title = '%s (%s)' % (full_title.encode('utf8'), functions[function].encode('utf8'))
        if group.getProperty('title') != group_title or sg._groups[group.id]['title'] != group_title:
            logger.info("Correcting group %s" % group.id)
            pg.editGroup(group.id, title=group_title)
