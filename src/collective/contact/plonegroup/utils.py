# -*- coding: utf-8 -*-

from collective.contact.plonegroup.config import DEFAULT_DIRECTORY_ID
from collective.contact.plonegroup.config import get_registry_functions
from collective.contact.plonegroup.config import get_registry_organizations
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.config import set_registry_functions
from collective.contact.plonegroup.config import set_registry_organizations
from imio.helpers.content import uuidsToObjects
from operator import attrgetter
from operator import methodcaller
from plone import api
from plone.api.exc import GroupNotFoundError
from plone.app.uuid.utils import uuidToObject
from Products.CMFPlone.utils import base_hasattr
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


def organizations_with_suffixes(groups, suffixes, group_as_str=False):
    """
        Return organization uids for given plone groups and without suffixes
    """
    orgs = []
    for group in groups:
        parts = (group_as_str and group or group.id).split('_')
        if len(parts) == 1:
            continue
        group_suffix = '_'.join(parts[1:])
        if group_suffix in suffixes and parts[0] not in orgs:
            orgs.append(parts[0])
    return orgs


def get_plone_group_id(prefix, suffix):
    """
        Return Plone group id corresponding to prefix/suffix.
    """
    # make sure we received an str as org_uid, not an org
    if not isinstance(prefix, (str, unicode)):
        raise TypeError('Parameter prefix must be str or unicode instance!')
    return '{0}_{1}'.format(prefix, suffix)


def get_plone_group(prefix, suffix):
    """
        Return Plone group corresponding to prefix/suffix.
    """
    plone_group_id = get_plone_group_id(prefix, suffix)
    plone_group = api.group.get(plone_group_id)
    return plone_group


def get_plone_groups(org_uid, ids_only=False, suffixes=[]):
    """
        Return Plone groups linked to given org_uid.
        If ids_only is True, only returns Plone groups ids,
        either returns Plone group objects.
        Only returns Plone groups using suffixes if provided.
    """
    suffixes = suffixes or get_all_suffixes(org_uid)
    plone_groups = [get_plone_group_id(org_uid, suffix) for suffix in suffixes]
    plone_groups = [api.group.get(plone_group) for plone_group in plone_groups]
    # remove None values
    plone_groups = [v for v in plone_groups if v]
    if ids_only:
        plone_groups = [plone_group.getId() for plone_group in plone_groups]
    return plone_groups


def get_organization(plone_group_id_or_org_uid, caching=True):
    """
        Return organization corresponding to given plone_group_id_or_org_uid.
        We can receive either a plone_grou_id or an org_uid.
    """
    # there is no '_' in organization UID so when receiving a Plone group id,
    # we are sure that first part is the organization UID
    organization_uid = plone_group_id_or_org_uid.split('_')[0]

    org = None
    if caching:
        request = getRequest()
        if request:
            # in some cases like in tests, request can not be retrieved
            key = "plonegroup-utils-get_organization-{0}".format(organization_uid)
            cache = IAnnotations(request)
            org = cache.get(key, None)
        else:
            caching = False

    if not org:
        org = uuidToObject(organization_uid)
        if caching:
            cache[key] = org

    return org


def get_organizations(only_selected=True,
                      the_objects=True,
                      not_empty_suffix=None,
                      kept_org_uids=[],
                      caching=True):
    """
        Return organizations.
        If only_selected, check registry if org is selected.
        If the objects, return organization objects, either return UIDs.
        If not_empty_suffix, return organizations for which Plone group using
        given suffix is not empty.
        If kept_org_uids, return only organizations with these UIDs.
        If caching, use REQUEST caching.
    """
    orgs = None
    if caching:
        request = getRequest()
        if request:
            # in some cases like in tests, request can not be retrieved
            key = "plonegroup-utils-get_organizations-{0}-{1}-{2}-{3}".format(
                not_empty_suffix or '',
                str(only_selected),
                str(the_objects),
                '_'.join(sorted(kept_org_uids)))
            cache = IAnnotations(request)
            orgs = cache.get(key, None)
        else:
            caching = False

    if orgs is None:
        if only_selected:
            org_uids = get_registry_organizations()
        else:
            # use the vocabulary to get selectable organizations so if vocabulary
            # is overrided get_organizations is still consistent
            vocab = getUtility(
                IVocabularyFactory,
                name=u'collective.contact.plonegroup.organization_services')
            portal = api.portal.get()
            org_uids = [term.value for term in vocab(portal)._terms]
        # filter out regarding parameter kept_org_uids
        if kept_org_uids:
            # make sure order defined by kept_org_uids is kept
            org_uids = [kept_org_uid for kept_org_uid in kept_org_uids
                        if kept_org_uid in org_uids]
        # we only keep orgs for which Plone group with not_empty_suffix suffix contains members
        if not_empty_suffix:
            filtered_orgs = []
            for org_uid in org_uids:
                plone_group_id = get_plone_group_id(org_uid, suffix=not_empty_suffix)
                plone_group = api.group.get(plone_group_id)
                if plone_group and plone_group.getMemberIds():
                    filtered_orgs.append(org_uid)
            org_uids = filtered_orgs

        # return org uids or org objects
        if the_objects:
            orgs = uuidsToObjects(org_uids, ordered=True)
        else:
            orgs = org_uids

        if caching:
            # store a new list in cache so it can not be modified
            cache[key] = list(orgs)

    return orgs


def get_all_suffixes(org_uid=None, only_enabled=True):
    """
        Get every suffixes defined in the configuration.
    """
    functions = get_registry_functions()
    return [function['fct_id'] for function in functions
            if (not only_enabled or function['enabled']) and
               (not org_uid or not function['fct_orgs'] or org_uid in function['fct_orgs'])]


def get_selected_org_suffix_users(org_uid, suffixes):
    """
        Get users that belongs to suffixed groups related to selected organization.
    """
    org_members = []
    # only add to vocabulary users with these functions in the organization
    for function_id in suffixes:
        groupname = "{}_{}".format(org_uid, function_id)
        try:
            members = api.user.get_users(groupname=groupname)
        except GroupNotFoundError:  # suffix can be limited to some organization...
            continue
        for member in members:
            if base_hasattr(member, "isGroup") and member.isGroup():
                continue
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


def get_own_organization(default=True):
    """
        get plonegroup-organization object
        If p_default is True, we get it in a "contacts" directory added to the portal root.
    """
    if default:
        portal = api.portal.get()
        return portal.get(DEFAULT_DIRECTORY_ID).get(PLONEGROUP_ORG)
    else:
        catalog = api.portal.get_tool('portal_catalog')
        brains = catalog(portal_type='organization', id=PLONEGROUP_ORG)
        if brains:
            return brains[0].getObject()


def get_own_organization_path(not_found_value=None, default=True):
    """
        get plonegroup-organization path
    """
    own_org = get_own_organization(default=default)
    if own_org:
        return '/'.join(own_org.getPhysicalPath())
    return not_found_value


def select_organization(org_uid, remove=False):
    """Select organization in ORGANIZATIONS_REGISTRY."""
    plonegroup_organizations = get_registry_organizations()
    if remove:
        plonegroup_organizations.remove(org_uid)
    else:
        plonegroup_organizations.append(org_uid)
    set_registry_organizations(plonegroup_organizations)


def select_org_for_function(org_uid, function_id, remove=False):
    """Select an organization UID in the list of fct_orgs of a function."""
    functions = get_registry_functions()
    for function in functions:
        if function['fct_id'] == function_id:
            if remove and org_uid in function['fct_orgs']:
                function['fct_orgs'].remove(org_uid)
            elif org_uid not in function['fct_orgs']:
                function['fct_orgs'].append(org_uid)
    set_registry_functions(functions)
