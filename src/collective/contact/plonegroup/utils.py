# -*- coding: utf-8 -*-

from operator import attrgetter
from operator import methodcaller
from plone import api
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
