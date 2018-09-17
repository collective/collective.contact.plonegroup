# -*- coding: utf-8 -*-

from collective.contact.plonegroup.config import FUNCTIONS_REGISTRY
from collective.contact.plonegroup.config import ORGANIZATIONS_REGISTRY
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from operator import attrgetter
from operator import methodcaller
from plone import api
from plone.app.uuid.utils import uuidToObject
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


def organizations_with_suffixes(groups, suffixes):
    """
        Return organization uids for given plone groups and without suffixes
    """
    orgs = []
    for group in groups:
        parts = group.id.split('_')
        if len(parts) == 1:
            continue
        group_suffix = '_'.join(parts[1:])
        if group_suffix in suffixes and parts[0] not in orgs:
            orgs.append(parts[0])
    return orgs


def get_plone_group_id(org_uid, suffix):
    """
        Return Plone group id corresponding to org_uid/suffix.
    """
    return '{0}_{1}'.format(org_uid, suffix)


def get_plone_groups(org_uid, ids_only=False, suffixes=[]):
    """
        Return Plone groups linked to given org_uid.
        If ids_only is True, only returns Plone groups ids,
        either returns Plone group objects.
        Only returns Plone groups using suffixes if provided.
    """
    suffixes = suffixes or get_all_suffixes(org_uid)
    plone_groups = [get_plone_group_id(org_uid, suffix) for suffix in suffixes]
    if not ids_only:
        plone_groups = [api.group.get(plone_group) for plone_group in plone_groups]
    return plone_groups


def get_organization(plone_group_id):
    """
        Return organization corresponding to given Plone group id.
    """
    # there is no '_' in organization UID so we are sure that
    # first part is the organization UID
    organization_uid = plone_group_id.split('_')[0]
    return uuidToObject(organization_uid)


def get_organizations(only_selected=True, the_objects=True, not_empty_suffix=None):
    """
        Return every organizations.
    """
    if only_selected:
        orgs = api.portal.get_registry_record(ORGANIZATIONS_REGISTRY)
    else:
        # use the vocabulary to get selectable organizations so if vocabulary
        # is overrided get_organizations is still consistent
        vocab = getUtility(
            IVocabularyFactory,
            name=u'collective.contact.plonegroup.organization_services')
        portal = api.portal.get()
        orgs = [term.value for term in vocab(portal)._terms]

    # we only keep orgs for which Plone group with not_empty_suffix suffix contains members
    if not_empty_suffix:
        filtered_orgs = []
        for org_uid in orgs:
            plone_group_id = get_plone_group_id(org_uid, suffix=not_empty_suffix)
            plone_group = api.group.get(plone_group_id)
            if plone_group and plone_group.getMemberIds():
                filtered_orgs.append(org_uid)
        orgs = filtered_orgs

    if the_objects:
        orgs = [uuidToObject(org) for org in orgs]
    return orgs


def get_all_suffixes(org_uid=None):
    """
        Get every suffixes defined in the configuration.
    """
    functions = api.portal.get_registry_record(FUNCTIONS_REGISTRY)
    return [function['fct_id'] for function in functions
            if not org_uid or not function['fct_orgs'] or org_uid in function['fct_orgs']]


def get_selected_org_suffix_users(org_uid, suffixes):
    """
        Get users that belongs to suffixed groups related to selected organization.
    """
    org_members = []
    # only add to vocabulary users with these functions in the organization
    for function_id in suffixes:
        groupname = "{}_{}".format(org_uid, function_id)
        members = api.user.get_users(groupname=groupname)
        for member in members:
            if member not in org_members:
                org_members.append(member)
    return org_members


def voc_selected_org_suffix_users(org_uid, suffixes, first_member=None):
    """
        Return users vocabulary that belongs to suffixed groups related to selected organization.
    """
    if not org_uid or org_uid == u'--NOVALUE--':
        return SimpleVocabulary([])
    terms = []
    # only add to vocabulary users with these functions in the organization
    for member in sorted(get_selected_org_suffix_users(org_uid, suffixes), key=methodcaller('getUserName')):
        if member == first_member:
            terms.insert(0, SimpleTerm(
                value=member.getUserName(),  # login
                token=member.getId(),  # id
                title=member.getUser().getProperty('fullname') or member.getUserName()))
        else:
            terms.append(SimpleTerm(
                value=member.getUserName(),  # login
                token=member.getId(),  # id
                title=member.getUser().getProperty('fullname') or member.getUserName()))  # title
    if first_member is None:
        terms.sort(key=attrgetter('title'))
    else:
        terms[1:] = sorted(terms[1:], key=attrgetter('title'))
    return SimpleVocabulary(terms)


def get_own_organization():
    """
        get plonegroup-organization object
    """
    catalog = api.portal.get_tool('portal_catalog')
    brains = catalog(portal_type='organization', id=PLONEGROUP_ORG)
    if brains:
        return brains[0].getObject()


def get_own_organization_path(not_found_value=None):
    """
        get plonegroup-organization path
    """
    own_orga = get_own_organization()
    if own_orga:
        return '/'.join(own_orga.getPhysicalPath())
    return not_found_value
