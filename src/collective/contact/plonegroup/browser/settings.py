# -*- coding: utf-8 -*-
from collective.contact.plonegroup import _
from collective.contact.plonegroup.config import DEFAULT_DIRECTORY_ID
from collective.contact.plonegroup.config import get_registry_functions
from collective.contact.plonegroup.config import get_registry_organizations
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.events import PlonegroupGroupCreatedEvent
from collective.contact.plonegroup.utils import get_all_suffixes
from collective.contact.plonegroup.utils import get_organizations
from collective.contact.plonegroup.utils import get_own_organization_path
from collective.contact.plonegroup.utils import get_plone_group_id
from collective.elephantvocabulary import wrap_vocabulary
from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.registry import DictRow
from imio.helpers.cache import get_cachekey_volatile
from imio.helpers.cache import invalidate_cachekey_volatile_for
from imio.helpers.content import safe_encode
from operator import attrgetter
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.uuid.utils import uuidToObject
from plone.autoform.directives import widget
from plone.memoize import ram
from plone.memoize.interfaces import ICacheChooser
from plone.registry.interfaces import IRecordModifiedEvent
from plone.z3cform import layout
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import form
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zExceptions import Redirect
from zope import schema
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.container.interfaces import IContainerModifiedEvent
from zope.container.interfaces import IObjectRemovedEvent
from zope.event import notify
from zope.interface import implements
from zope.interface import Interface
from zope.interface import Invalid
from zope.interface import invariant
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import re


class IOrganizationSchema(Interface):
    """
        Organization identification schema
    """
    org_id = schema.TextLine(title=_("Organization id"), required=True)
    org_title = schema.TextLine(title=_("Organization title"), required=True)


class IFunctionSchema(Interface):
    """
        Function identification schema
    """
    fct_id = schema.TextLine(
        title=_("Plone group suffix id"),
        # description=_("Plone group suffix description"),
        required=True)
    fct_title = schema.TextLine(
        title=_("Plone group suffix title"),
        # description=_("Plone group title description"),
        required=True)
    fct_orgs = schema.List(
        title=_("Plone group suffix organizations"),
        description=_("Plone group organizations description"),
        value_type=schema.Choice(
            vocabulary='collective.contact.plonegroup.browser.settings.'
                       'SortedSelectedOrganizationsElephantVocabulary'),
        required=True)
    fct_management = schema.Bool(
        title=_("Manageable function groups?"),
        required=False,
        default=False,
    )
    enabled = schema.Bool(
        title=_(u'Enabled?'),
        default=True,
        required=False,)


def voc_cache_key(method, self, context):
    return get_cachekey_volatile("%s.%s" % (self.__class__.__module__, self.__class__.__name__))


class BaseOrganizationServicesVocabulary(object):
    """
        Base vocabulary returning organizations from a particular root level.
    """
    implements(IVocabularyFactory)
    valid_states = ('active',)

    def listSubOrganizations(self, terms, folder, parent_label=''):
        # query sub organizations if any to query
        if folder.objectIds():
            catalog = api.portal.get_tool('portal_catalog')
            folder_path = '/'.join(folder.getPhysicalPath())
            brains = catalog.unrestrictedSearchResults(
                portal_type='organization',
                review_state=self.valid_states,
                path={'query': folder_path, 'depth': 1},
                sort_on='getObjPositionInParent'
            )
            for brain in brains:
                orga = brain._unrestrictedGetObject()
                term_title = self._term_title(orga, parent_label)
                term_value = self._term_value(orga)
                term_token = self._term_token(orga)
                terms.append(SimpleTerm(term_value, term_token, term_title))
                self.listSubOrganizations(terms, orga, term_title)

    def _term_value(self, orga):
        '''Method that render term value, separated to ease override.'''
        return orga.UID()

    def _term_token(self, orga):
        '''Method that render term token, separated to ease override.'''
        return orga.UID()

    def _term_title(self, orga, parent_label):
        '''Method that render term title, separated to ease override.'''
        term_title = orga.title
        if parent_label:
            term_title = "%s - %s" % (parent_label, term_title)
        return term_title

    def __call__(self, context, root_portal_type='organization', root_id=PLONEGROUP_ORG):
        portal = getSite()
        terms = []
        pcat = portal.portal_catalog
        brains = pcat.unrestrictedSearchResults(portal_type=root_portal_type, id=root_id)
        if not brains:
            terms.append(SimpleTerm(None, token="unfound",
                                    title=_(u"You must define one '${root_portal_type}' with id '${pgo}' !",
                                            mapping={'root_portal_type': root_portal_type,
                                                     'pgo': root_id, })))
            return SimpleVocabulary(terms)
        elif len(brains) > 1:
            terms.append(SimpleTerm(None, token="multifound",
                                    title=_(u"You must have only one '${root_portal_type}' "
                                            "with id '${pgo}' !",
                                            mapping={'root_portal_type': root_portal_type,
                                                     'pgo': root_id})))
            return SimpleVocabulary(terms)

        own_orga = brains[0]._unrestrictedGetObject()
        self.listSubOrganizations(terms, own_orga)

        return SimpleVocabulary(terms)


class OwnOrganizationServicesVocabulary(BaseOrganizationServicesVocabulary):
    """
        Returns every organiztions stored in PLONEGROUP_ORG.
    """

    def __call__(self, context):
        return super(OwnOrganizationServicesVocabulary, self).__call__(context)


class EveryOrganizationsVocabulary(BaseOrganizationServicesVocabulary):
    """
        Returns every organizations stored in DEFAULT_DIRECTORY_ID directory,
        so inside and outside the PLONEGROUP_ORG.
    """

    def __call__(self, context):
        return super(EveryOrganizationsVocabulary, self).__call__(
            context, root_portal_type='directory', root_id=DEFAULT_DIRECTORY_ID)


class IContactPlonegroupConfig(Interface):
    """
        Configuration schema
    """

    # plone.registry cannot store schema.Choice different from named vocabularies !
    organizations = schema.List(
        title=_(u'Selected organizations'),
        description=_(u"Choose multiple organization levels for which you want to create a plone group."),
        required=True,
        value_type=schema.Choice(vocabulary=u'collective.contact.plonegroup.organization_services',))
    widget('organizations', size=15)

    functions = schema.List(
        title=_(u'Function list'),
        description=_(u'Each defined function will suffix each organization plone group.'),
        required=True,
        value_type=DictRow(title=_("Function"),
                           schema=IFunctionSchema)
    )
    widget('functions', DataGridFieldFactory, auto_append=False)

    groups_management = schema.List(
        title=_(u'Selected global groups can be managed by a contained user'),
        required=False,
        value_type=schema.Choice(vocabulary=u'collective.contact.plonegroup.global_groups'),
    )
    widget('groups_management', CheckBoxFieldWidget, multiple='multiple', size=15)

    @invariant
    def validateSettings(data):
        if not data.organizations:
            raise Invalid(_(u"You must choose at least one organization !"))
        if len(data.organizations) == 1 and data.organizations[0] is None:
            raise Invalid(_(u"You must correct the organization error first !"))
        if not data.functions:
            raise Invalid(_(u"You must define at least one function !"))

        # only able to delete a function (suffix) if every linked Plone groups are empty
        stored_suffixes = get_all_suffixes()
        saved_suffixes = [func['fct_id'] for func in data.functions]
        removed_suffixes = list(set(stored_suffixes) - set(saved_suffixes))
        for removed_suffix in removed_suffixes:
            # check that every organizations including not selected
            # linked suffixed Plone group is empty
            for org_uid in get_organizations(only_selected=False, the_objects=False):
                plone_group_id = get_plone_group_id(org_uid, removed_suffix)
                plone_group = api.group.get(plone_group_id)
                if plone_group and plone_group.getMemberIds():
                    raise Invalid(
                        _(u"can_not_remove_function_every_plone_groups_not_empty",
                          mapping={'removed_function': removed_suffix,
                                   'plone_group_id': plone_group_id}))

        # only able to select orgs for an existing function (suffix) if
        # every linked Plone groups of not selected orgs are empty
        stored_functions = get_registry_functions()
        old_functions = {dic['fct_id']: {'fct_title': dic['fct_title'],
                                         'fct_orgs': dic['fct_orgs'],
                                         'enabled': dic['enabled']}
                         for dic in stored_functions}
        new_functions = {dic['fct_id']: {'fct_title': dic['fct_title'],
                                         'fct_orgs': dic['fct_orgs'],
                                         'enabled': dic['enabled']}
                         for dic in data.functions}
        for new_function, new_function_infos in new_functions.items():
            if new_function_infos['fct_orgs'] and \
               old_functions[new_function]['fct_orgs'] != new_function_infos['fct_orgs']:
                # check that Plone group is empty for not selected fct_orgs
                for org_uid in get_organizations(only_selected=False, the_objects=False):
                    if org_uid in new_function_infos['fct_orgs']:
                        continue
                    plone_group_id = get_plone_group_id(org_uid, new_function)
                    plone_group = api.group.get(plone_group_id)
                    # use getGroupMembers to ignore '<not found>' users
                    if plone_group and plone_group.getGroupMembers():
                        raise Invalid(
                            _(u"can_not_select_function_orgs_every_other_plone_groups_not_empty",
                              mapping={'function': new_function,
                                       'plone_group_id': plone_group_id}))
            elif new_function_infos['enabled'] is False:
                # check that Plone groups are all empty
                for org_uid in get_organizations(only_selected=False, the_objects=False):
                    plone_group_id = get_plone_group_id(org_uid, new_function)
                    plone_group = api.group.get(plone_group_id)
                    # use getGroupMembers to ignore '<not found>' users
                    if plone_group and plone_group.getGroupMembers():
                        raise Invalid(
                            _(u"can_not_disable_suffix_plone_groups_not_empty",
                              mapping={'disabled_function': new_function,
                                       'plone_group_id': plone_group_id}))


def addOrModifyGroup(orga, function_id, function_title):
    """
        create a plone group
    """
    organization_title = orga.get_full_title(separator=' - ', first_index=1)
    organization_title = safe_encode(organization_title)
    function_title = safe_encode(function_title)
    group_name = get_plone_group_id(orga.UID(), function_id)
    group = api.group.get(groupname=group_name)
    group_title = '%s (%s)' % (organization_title, function_title)
    if group is None:
        group = api.group.create(
            groupname=group_name,
            title=group_title,
        )
        notify(PlonegroupGroupCreatedEvent(group))
        return True
    else:
        # group_title is maybe modified
        # portal_groups.editGroup(group_name, utf8)
        pg = api.portal.get_tool('portal_groups')
        if group.getProperty('title') != group_title:
            pg.editGroup(group_name, title=group_title)
            # group.setProperties(title=group_title)  # not good !!
            return True
    return False


def invalidate_sopgv_cache():
    """
        invalidate cache of selectedOrganizationsPloneGroupsVocabulary
    """
    cache_chooser = getUtility(ICacheChooser)
    thecache = cache_chooser('collective.contact.plonegroup.browser.settings.'
                             'selectedOrganizationsPloneGroupsVocabulary')
    thecache.ramcache.invalidate('collective.contact.plonegroup.browser.settings.'
                                 'selectedOrganizationsPloneGroupsVocabulary')


def invalidate_sov_cache():
    """
        invalidate cache of selectedOrganizationsVocabulary
    """
    cache_chooser = getUtility(ICacheChooser)
    thecache = cache_chooser('collective.contact.plonegroup.browser.settings.selectedOrganizationsVocabulary')
    thecache.ramcache.invalidate('collective.contact.plonegroup.browser.settings.selectedOrganizationsVocabulary')


def invalidate_soev_cache():
    """
        invalidate cache of SelectedOrganizationsElephantVocabulary
    """
    invalidate_cachekey_volatile_for(
        'collective.contact.plonegroup.browser.settings.SelectedOrganizationsElephantVocabulary')


def invalidate_ssoev_cache():
    """
        invalidate cache of SortedSelectedOrganizationsElephantVocabulary
    """
    invalidate_cachekey_volatile_for(
        'collective.contact.plonegroup.browser.settings.SortedSelectedOrganizationsElephantVocabulary')


def detectContactPlonegroupChange(event):
    """
        Manage our record changes
    """
    if IRecordModifiedEvent.providedBy(event):  # and event.record.interface == IContactPlonegroupConfig:
        changes = False
        # this can be called before plonegroup is installed and registry contains relevant keys
        try:
            registry_orgs = get_registry_organizations()
        except InvalidParameterError:
            registry_orgs = []
        if event.record.fieldName == 'organizations' and registry_orgs:
            old_set = set(event.oldValue)
            new_set = set(event.newValue)
            # we detect a new organization
            add_set = new_set.difference(old_set)
            for orga_uid in add_set:
                orga = uuidToObject(orga_uid)
                for fct_dic in get_registry_functions():
                    enabled = fct_dic['enabled']
                    if enabled is False:
                        continue
                    fct_orgs = fct_dic['fct_orgs']
                    if fct_orgs and orga_uid not in fct_orgs:
                        continue
                    if addOrModifyGroup(orga, fct_dic['fct_id'], fct_dic['fct_title']):
                        changes = True
            # we detect a removed organization. We dont do anything on exsiting groups
            if old_set.difference(new_set):
                changes = True
        elif event.record.fieldName == 'functions' and registry_orgs:
            old_functions = {dic['fct_id']: {'fct_title': dic['fct_title'],
                                             'fct_orgs': dic['fct_orgs'],
                                             'enabled': dic['enabled']}
                             for dic in event.oldValue}
            old_set = set(old_functions.keys())
            new_functions = {dic['fct_id']: {'fct_title': dic['fct_title'],
                                             'fct_orgs': dic['fct_orgs'],
                                             'enabled': dic['enabled']}
                             for dic in event.newValue}
            new_set = set(new_functions.keys())
            # we detect a new function
            add_set = new_set.difference(old_set)
            for new_id in add_set:
                new_title = new_functions[new_id]['fct_title']
                new_orgs = new_functions[new_id]['fct_orgs']
                enabled = new_functions[new_id]['enabled']
                for orga_uid in registry_orgs:
                    if new_orgs and orga_uid not in new_orgs:
                        continue
                    if enabled is False:
                        continue
                    orga = uuidToObject(orga_uid)
                    if addOrModifyGroup(orga, new_id, new_title):
                        changes = True
            # we detect a removed function
            # We may remove Plone groups as we checked before that every are empty
            removed_set = old_set.difference(new_set)
            for removed_id in removed_set:
                for orga_uid in get_organizations(only_selected=False, the_objects=False):
                    plone_group_id = get_plone_group_id(orga_uid, removed_id)
                    plone_group = api.group.get(plone_group_id)
                    if plone_group:
                        api.group.delete(plone_group_id)
                        changes = True
            # we detect existing functions for which 'fct_orgs' changed
            for new_id, new_function_infos in new_functions.items():
                new_title = new_function_infos['fct_title']
                new_orgs = new_function_infos['fct_orgs']
                enabled = new_function_infos['enabled']
                if not new_orgs and enabled is True:
                    # we have to make sure Plone groups are created for every selected organizations
                    for orga_uid in registry_orgs:
                        orga = uuidToObject(orga_uid)
                        if addOrModifyGroup(orga, new_id, new_title):
                            changes = True
                else:
                    # fct_orgs changed, we remove every linked Plone groups
                    # except ones defined in new_orgs
                    for orga_uid in get_organizations(only_selected=False, the_objects=False):
                        if enabled is True and orga_uid in new_orgs:
                            # make sure Plone group is created or updated if suffix title changed
                            orga = uuidToObject(orga_uid)
                            if addOrModifyGroup(orga, new_id, new_title):
                                changes = True
                        else:
                            # make sure Plone group is deleted
                            plone_group_id = get_plone_group_id(orga_uid, new_id)
                            plone_group = api.group.get(plone_group_id)
                            if plone_group:
                                api.group.delete(plone_group_id)
                                changes = True

        if changes:
            invalidate_sopgv_cache()
            invalidate_sov_cache()
            invalidate_soev_cache()
            invalidate_ssoev_cache()


class SettingsEditForm(RegistryEditForm):
    """
    Define form logic
    """
    form.extends(RegistryEditForm)
    schema = IContactPlonegroupConfig


SettingsView = layout.wrap_form(SettingsEditForm, ControlPanelFormWrapper)


def addOrModifyOrganizationGroups(organization, uid):
    """
        Modify groups linked to an organization
    """
    changes = False
    for dic in get_registry_functions():
        if addOrModifyGroup(organization, dic['fct_id'], dic['fct_title']):
            changes = True
    return changes


def adaptPloneGroupDefinition(organization, event):
    """
        Manage an organization change
    """
    # zope.lifecycleevent.ObjectRemovedEvent : delete
    # zope.lifecycleevent.ObjectModifiedEvent : edit, rename
    # is the container who's modified at creation ?
    # bypass if we are removing the Plone Site
    if IContainerModifiedEvent.providedBy(event) or \
       event.object.portal_type == 'Plone Site':
        return
    # is the current organization a part of own organization
    organization_path = '/'.join(organization.getPhysicalPath())
    if not organization_path.startswith(
       get_own_organization_path(not_found_value='unfound')):  # can be unfound too
        return
    portal = getSite()
    # when an organization is removed (and its content), we check if it is used in plonegroup configuration
    registry_orgs = get_registry_organizations()
    if IObjectRemovedEvent.providedBy(event) and organization.UID() in registry_orgs:
        smi = IStatusMessage(organization.REQUEST)
        smi.addStatusMessage(_('You cannot delete this item !'), type='error')
        smi.addStatusMessage(_("This organization or a contained organization is used in plonegroup "
                               "configuration ! Remove it first from the configuration !"), type='error')
        view_url = getMultiAdapter((organization, organization.REQUEST), name=u'plone_context_state').view_url()
        organization.REQUEST['RESPONSE'].redirect(view_url)
        raise Redirect(view_url)
        return
    pcat = portal.portal_catalog
    brains = pcat(portal_type='organization', path=organization_path)
    changes = False
    for brain in brains:
        orga = brain.getObject()
        orga_uid = orga.UID()
        if orga_uid in registry_orgs:
            if addOrModifyOrganizationGroups(orga, orga_uid):
                changes = True
    if changes:
        invalidate_sopgv_cache()
        invalidate_sov_cache()
        invalidate_soev_cache()
        invalidate_ssoev_cache()


def sopgv_cache_key(function, functions=[], group_title=True):
    """
        calculate the cache key
    """
    return (set(functions), group_title)


@ram.cache(sopgv_cache_key)  # not used
def selectedOrganizationsPloneGroupsVocabulary(functions=[], group_title=True):
    """
        Returns a vocabulary of selected organizations corresponding plone groups
    """
    terms = []
    # if no function given, use all functions
    functions = functions or get_all_suffixes()
    for orga_uid in get_registry_organizations():
        for fct_id in functions:
            group_id = "%s_%s" % (orga_uid, fct_id)
            group = api.group.get(groupname=group_id)
            if group is not None:
                if group_title:
                    title = group.getProperty('title')
                else:
                    title = uuidToObject(orga_uid).get_full_title(separator=' - ', first_index=1)
                terms.append(SimpleTerm(group_id, token=group_id, title=title))
    return SimpleVocabulary(terms)


def unrestrictedUuidToObject(uid):
    portal = getSite()
    pc = portal.portal_catalog
    res = pc.unrestrictedSearchResults(UID=uid)
    if res:
        return res[0].getObject()
    return None


def getSelectedOrganizations(separator=' - ', first_index=1):
    """ Return a list of tuples (uid, title) """
    ret = []
    registry_orgs = get_registry_organizations()
    # needed to get as manager because plone.formwidget.masterselect calls ++widget++ as Anonymous
    if api.user.is_anonymous():
        with api.env.adopt_roles(['Manager']):
            for orga_uid in registry_orgs:
                title = unrestrictedUuidToObject(orga_uid).get_full_title(separator=separator, first_index=first_index)
                ret.append((orga_uid, title))
    else:
        for orga_uid in registry_orgs:
            title = uuidToObject(orga_uid).get_full_title(separator=separator, first_index=first_index)
            ret.append((orga_uid, title))
    return ret


@ram.cache(lambda *args: True)  # not used
def selectedOrganizationsVocabulary():
    """
        Returns a vocabulary of selected organizations
    """
    terms = [SimpleTerm(t[0], title=t[1]) for t in getSelectedOrganizations()]
    return SimpleVocabulary(terms)


class SearchableSimpleVocabulary(SimpleVocabulary):

    def search(self, query, limit=50):
        # transform query in a regexp
        regexp = u' '.join([u'{}.*'.format(p) for p in query.split(' ')])
        regexp = re.compile(regexp, re.I)
        return [
            term for term in self._terms if re.search(regexp, term.title)
        ]


class SelectedOrganizationsElephantVocabulary(OwnOrganizationServicesVocabulary):
    """ Vocabulary of selected plonegroup-organizations services. """

    @ram.cache(voc_cache_key)
    def __call__(self, context):
        vocab = super(SelectedOrganizationsElephantVocabulary, self).__call__(context)
        terms = vocab.by_value
        ordered_terms = []
        for uid in get_registry_organizations():
            if uid in terms:
                ordered_terms.append(terms[uid])
                del terms[uid]
        extra_uids = terms.keys()
        extra_terms = terms.values()
        # ordered_vocab = SearchableSimpleVocabulary(ordered_terms + extra_terms)  # bug in widget, trac #15186
        ordered_vocab = SimpleVocabulary(ordered_terms + extra_terms)
        wrapped_vocab = wrap_vocabulary(ordered_vocab, hidden_terms=extra_uids)(context)
        return wrapped_vocab


class SortedSelectedOrganizationsElephantVocabulary(SelectedOrganizationsElephantVocabulary):
    """ Vocabulary of selected plonegroup-organizations services sorted on title. """

    @ram.cache(voc_cache_key)
    def __call__(self, context):
        wrapped_vocab = super(SortedSelectedOrganizationsElephantVocabulary, self).__call__(context)
        # sort by title
        sorted_vocab = sorted(wrapped_vocab.vocab, key=attrgetter('title'))
        wrapped_vocab.vocab = SimpleVocabulary(sorted_vocab)
        return wrapped_vocab
