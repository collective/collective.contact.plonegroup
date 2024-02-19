# -*- coding: utf-8 -*-

from collective.contact.plonegroup import _
from collective.contact.plonegroup.utils import get_all_suffixes
from collective.contact.plonegroup.utils import organizations_with_suffixes
from imio.helpers import get_cachekey_volatile
from imio.helpers.cache import get_plone_groups_for_user
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.formwidget.masterselect import MasterSelectField
from plone.supermodel import model
from zope import schema
from zope.component import getUtility
from zope.interface import implementer
from zope.interface import provider
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary


def filter_user_organizations(userid):
    """
        Filter user organizations
    """
    if not userid:
        return SimpleVocabulary([])
    factory = getUtility(IVocabularyFactory, 'collective.contact.plonegroup.primary_organizations')
    vocab = factory(None, userid=userid)
    return SimpleVocabulary([term for term in vocab._terms])


@provider(IFormFieldProvider)
class IPlonegroupUserLink(model.Schema):

    userid = MasterSelectField(
        title=_(u'Plone user'),
        required=False,
        vocabulary=u'imio.helpers.SortedUsers',
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
        vocabulary='collective.contact.plonegroup.browser.settings.SelectedOrganizationsElephantVocabulary',
    )
    directives.read_permission(primary_organization='collective.contact.plonegroup.read_userlink_fields')
    directives.write_permission(primary_organization='collective.contact.plonegroup.write_userlink_fields')

    model.fieldset('app_parameters',
                   label=_(u"Application parameters"),
                   fields=['userid', 'primary_organization'])


def primary_organizations_vocabulary_cache_key(method, self, context, userid, suffixes, base_voc):
    date = get_cachekey_volatile('_users_groups_value')
    return date, userid, suffixes, base_voc


@implementer(IVocabularyFactory)
class PrimaryOrganizationsVocabulary(object):
    """ Primary organizations vocabulary """

    # @ram.cache(primary_organizations_vocabulary_cache_key)
    def PrimaryOrganizationsVocabulary__call__(self, context, userid=None, suffixes=[],
                                               base_voc='collective.contact.plonegroup.browser.settings.'
                                                        'SelectedOrganizationsElephantVocabulary'):
        if not suffixes:
            suffixes = get_all_suffixes()
        groups = get_plone_groups_for_user(user_id=userid)
        user_orgs = organizations_with_suffixes(groups, suffixes, group_as_str=True)
        factory = getUtility(IVocabularyFactory, base_voc)
        vocab = factory(None)
        return SimpleVocabulary([term for term in vocab._terms if term.value in user_orgs])

    __call__ = PrimaryOrganizationsVocabulary__call__
