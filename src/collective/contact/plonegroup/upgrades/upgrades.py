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


def v5(context):
    logger.info("Migrate to v5")
    functions = api.portal.get_registry_record(name=FUNCTIONS_REGISTRY)
    res = []
    # XXX we intentionally directly edit the existing "function"
    # so it does not break in the detectContactPlonegroupChange method while looking
    # for 'fct_orgs' in old_functions
    for function in functions:
        if 'fct_orgs' not in function:
            function['fct_orgs'] = []
            res.append(function)
        else:
            # already migrated
            return
    api.portal.set_registry_record(FUNCTIONS_REGISTRY, res)


def v6(context):
    logger.info("Migrate to v6")
    # Cannot run v6 anymore without v7 code


def v7(context):
    """ Combined v6 code when coming from v5 """
    logger.info("Migrate to v7")
    functions = api.portal.get_registry_record(name=FUNCTIONS_REGISTRY)
    res = []
    # XXX we intentionally directly edit the existing "function"
    # so it does not break in the detectContactPlonegroupChange method
    for function in functions:
        if 'enabled' not in function:
            function['enabled'] = True
        if 'fct_management' not in function:
            function['fct_management'] = False
        res.append(function)
    api.portal.set_registry_record(FUNCTIONS_REGISTRY, res)
    setup = api.portal.get_tool('portal_setup')
    setup.runImportStepFromProfile('profile-collective.contact.plonegroup:default', 'plone.app.registry')
    setup.runImportStepFromProfile('profile-collective.contact.plonegroup:default', 'actions')
