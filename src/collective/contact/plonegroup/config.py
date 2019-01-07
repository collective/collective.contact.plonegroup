# -*- coding: utf-8 -*-

from plone import api


# Registry keys
ORGANIZATIONS_REGISTRY = 'collective.contact.plonegroup.browser.settings.IContactPlonegroupConfig.organizations'
FUNCTIONS_REGISTRY = 'collective.contact.plonegroup.browser.settings.IContactPlonegroupConfig.functions'
PLONEGROUP_ORG = 'plonegroup-organization'

def get_registry_organizations():
    return api.portal.get_registry_record(ORGANIZATIONS_REGISTRY)


def get_registry_functions():
    return api.portal.get_registry_record(FUNCTIONS_REGISTRY)


def set_registry_organizations(value):
    api.portal.set_registry_record(ORGANIZATIONS_REGISTRY, value)


def set_registry_functions(value):
    api.portal.set_registry_record(FUNCTIONS_REGISTRY, value)
