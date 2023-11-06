# -*- coding: utf-8 -*-

from collective.contact.plonegroup import _
from collective.contact.plonegroup.utils import get_all_suffixes
from collective.contact.plonegroup.utils import organizations_with_suffixes
from imio.helpers import get_cachekey_volatile
from imio.helpers.cache import get_plone_groups_for_user
from plone import api
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.formwidget.masterselect import MasterSelectField
from plone.supermodel import model
from zope import schema
from zope.component import getUtility
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary


def get_principal_suffixes():
    return get_all_suffixes()


def get_organizations_voc_name():
    return 'collective.contact.plonegroup.browser.settings.SelectedOrganizationsElephantVocabulary'


def filter_user_organizations(userid):
    """
        Filter user organizations
    """
    if not userid:
        return SimpleVocabulary([])
    suffixes = get_principal_suffixes()
    # groups = api.group.get_groups(user=user)
    groups = get_plone_groups_for_user(user_id=userid)
    user_orgs = organizations_with_suffixes(groups, suffixes, group_as_str=True)
    factory = getUtility(IVocabularyFactory, get_organizations_voc_name())
    vocab = factory(None)
    return SimpleVocabulary([term for term in vocab._terms if term.value in user_orgs])


class IPlonegroupUserLink(model.Schema):

    userid = MasterSelectField(
        title=_(u'Plone user'),
        required=False,
        vocabulary=u'plone.app.vocabularies.Users',
        slave_fields=(
            {'name': 'IPlonegroupUserLink.primary_organization',
             'action': 'vocabulary',
             'vocab_method': filter_user_organizations,
             'control_param': 'userid',
             'initial_trigger': True,
             },
        )
    )
    directives.read_permission(userid='collective.contact.plonegroup.read_userlink_fields')
    directives.write_permission(userid='collective.contact.plonegroup.write_userlink_fields')

    primary_organization = schema.Choice(
        title=_(u'Primary organization'),
        required=False,
        vocabulary=get_organizations_voc_name(),
    )
    directives.read_permission(primary_organization='collective.contact.plonegroup.read_userlink_fields')
    directives.write_permission(primary_organization='collective.contact.plonegroup.write_userlink_fields')


alsoProvides(IPlonegroupUserLink, IFormFieldProvider)
