# -*- coding: utf-8 -*-
from operator import attrgetter
from operator import methodcaller

from collective.contact.plonegroup.config import FUNCTIONS_REGISTRY
from collective.contact.plonegroup.config import ORGANIZATIONS_REGISTRY
from collective.contact.plonegroup.config import PLONEGROUP_ORG

from Acquisition import aq_get
from Products.CMFPlone.utils import base_hasattr
from config import ORGANIZATIONS_REGISTRY
from config import PLONEGROUP_ORG
from imio.helpers.content import uuidsToObjects
from plone import api
from plone.app.uuid.utils import uuidToObject
from plone.behavior.interfaces import IBehavior
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityFTI
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.schema import getFieldsInOrder
from zope.schema.interfaces import IChoice
from zope.schema.interfaces import ICollection
from zope.schema.interfaces import IText
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
    # make sure we received an str as org_uid, not an org
    if not isinstance(org_uid, (str, unicode)):
        raise TypeError('Parameter org_uid must be str or unicode instance!')
    return '{0}_{1}'.format(org_uid, suffix)


def get_plone_group(org_uid, suffix):
    """
        Return Plone group corresponding to org_uid/suffix.
    """
    plone_group_id = get_plone_group_id(org_uid, suffix)
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


def get_organization(plone_group_id_or_org_uid):
    """
        Return organization corresponding to given plone_group_id_or_org_uid.
        We can receive either a plone_grou_id or an org_uid.
    """
    # there is no '_' in organization UID so when receiving a Plone group id,
    # we are sure that first part is the organization UID
    organization_uid = plone_group_id_or_org_uid.split('_')[0]
    return uuidToObject(organization_uid)


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
            cache = IAnnotations(getRequest())
            orgs = cache.get(key, None)
        else:
            caching = False

    if orgs is None:
        if only_selected:
            org_uids = [org_uid for org_uid in api.portal.get_registry_record(ORGANIZATIONS_REGISTRY)]
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
            org_uids = [org_uid for org_uid in org_uids if org_uid in kept_org_uids]
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
            cache[key] = orgs

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
    own_org = get_own_organization()
    if own_org:
        return '/'.join(own_org.getPhysicalPath())
    return not_found_value


def select_organization(org_uid, remove=False):
    """Select organization in ORGANIZATIONS_REGISTRY."""
    plonegroup_organizations = list(api.portal.get_registry_record(ORGANIZATIONS_REGISTRY))
    if remove:
        plonegroup_organizations.remove(org_uid)
    else:
        plonegroup_organizations.append(org_uid)
    api.portal.set_registry_record(ORGANIZATIONS_REGISTRY, plonegroup_organizations)


def search_value_in_objects(s_obj, ref, p_types=[], type_fields={}):
    """
        Searching a value (reference to an object like id or uid) in fields of objects.
        Parameters:
            * s_obj : the object that is maybe referenced in another objects fields
            * ref : the value to search in field
            * p_types : portal_types that will be only searched
            * type_fields : dict containing as key portal_type and as value a list of fields that must be searched.
                            If a portal_type is not given, all fields will be searched
    """
    # we check all dexterity objects fields to see if ref is used in
    # we can't check only fields using plonegroup vocabulary because maybe another vocabulary name is used
    # this can be long but this operation is not made so often

    request = aq_get(s_obj, 'REQUEST', None)
    if not request:
        return
    try:
        catalog = api.portal.get_tool('portal_catalog')
    except api.portal.CannotGetPortalError:
        # When deleting site, the portal is no more found...
        return

    def list_fields(ptype, filter_interfaces=(IText, ICollection, IChoice)):
        """ return for the portal_type the selected fields """
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

    def check_value(val):
        if isinstance(val, basestring) and val == ref:
            return True
        return False

    def check_attribute(val):
        """ check the attribute value and walk in it """
        if isinstance(val, dict):
            for v in val.values():
                res = check_attribute(v)
                if res:
                    return res
        elif base_hasattr(val, '__iter__'):
            for v in val:
                res = check_attribute(v)
                if res:
                    return res
        elif check_value(val):
            res = [val]
            return res
        return []

    results = set()
    for brain in catalog.unrestrictedSearchResults(portal_types=p_types,
                                                   object_provides=IDexterityContent.__identifier__):
        obj = brain._unrestrictedGetObject()
        ptype = obj.portal_type
        for attr in list_fields(ptype):
            if base_hasattr(obj, attr):
                res = check_attribute(getattr(obj, attr))
                if res:
                    results.add(obj)
                    break

    return list(results)
