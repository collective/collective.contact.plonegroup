# -*- coding: utf-8 -*-
from collective.contact.plonegroup import _
from collective.contact.plonegroup.config import FUNCTIONS_REGISTRY
from collective.contact.plonegroup.config import ORGANIZATIONS_REGISTRY
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
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.uuid.utils import uuidToObject
from plone.autoform.directives import widget
from plone.memoize import ram
from plone.memoize.interfaces import ICacheChooser
from plone.registry.interfaces import IRecordModifiedEvent
from plone.registry.interfaces import IRegistry
from plone.z3cform import layout
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import form
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
        description=_("Plone group suffix description"),
        required=True)
    fct_title = schema.TextLine(
        title=_("Plone group suffix title"),
        description=_("Plone group title description"),
        required=True)
    fct_orgs = schema.List(
        title=_("Plone group suffix organizations"),
        description=_("Plone group organizations description"),
        value_type=schema.Choice(
            vocabulary='collective.contact.plonegroup.selected_organization_services'),
        required=True)


def voc_cache_key(method, self, context):
    return get_cachekey_volatile("%s.%s" % (self.__class__.__module__, self.__class__.__name__))


class OwnOrganizationServicesVocabulary(object):
    """
        Vocabulary of all plonegroup-organizations services.
    """
    implements(IVocabularyFactory)
    valid_states = ('active',)

    def listSubOrganizations(self, terms, folder, parent_label=''):
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
            term_title = orga.title
            if parent_label:
                term_title = "%s - %s" % (parent_label, term_title)
            terms.append(SimpleTerm(orga.UID(), orga.UID(), term_title))
            self.listSubOrganizations(terms, orga, term_title)

    def __call__(self, context):
        portal = getSite()
        terms = []
        pcat = portal.portal_catalog
        brains = pcat.unrestrictedSearchResults(portal_type='organization', id=PLONEGROUP_ORG)
        if not brains:
            terms.append(SimpleTerm(None, token="unfound",
                                    title=_(u"You must define an organization with id '${pgo}' !",
                                            mapping={'pgo': PLONEGROUP_ORG})))
            return SimpleVocabulary(terms)
        elif len(brains) > 1:
            terms.append(SimpleTerm(None, token="multifound", title=_(u"You must have only one organization "
                                                                      "with id '${pgo}' !",
                                                                      mapping={'pgo': PLONEGROUP_ORG})))
            return SimpleVocabulary(terms)

        own_orga = brains[0]._unrestrictedGetObject()
        self.listSubOrganizations(terms, own_orga)

        return SimpleVocabulary(terms)


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
        stored_functions = api.portal.get_registry_record(FUNCTIONS_REGISTRY)
        old_functions = {dic['fct_id']: {'fct_title': dic['fct_title'], 'fct_orgs': dic['fct_orgs']}
                         for dic in stored_functions}
        new_functions = {dic['fct_id']: {'fct_title': dic['fct_title'], 'fct_orgs': dic['fct_orgs']}
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
                    if plone_group and plone_group.getMemberIds():
                        raise Invalid(
                            _(u"can_not_select_function_orgs_every_other_plone_groups_not_empty",
                              mapping={'function': new_function,
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
    invalidate_cachekey_volatile_for('collective.contact.plonegroup.browser.settings.'
                                     'SelectedOrganizationsElephantVocabulary')


def detectContactPlonegroupChange(event):
    """
        Manage our record changes
    """
    if IRecordModifiedEvent.providedBy(event):  # and event.record.interface == IContactPlonegroupConfig:
        registry = getUtility(IRegistry)
        changes = False
        if event.record.fieldName == 'organizations' and registry[FUNCTIONS_REGISTRY]:
            old_set = set(event.oldValue)
            new_set = set(event.newValue)
            # we detect a new organization
            add_set = new_set.difference(old_set)
            for orga_uid in add_set:
                orga = uuidToObject(orga_uid)
                for fct_dic in registry[FUNCTIONS_REGISTRY]:
                    fct_orgs = fct_dic['fct_orgs']
                    if fct_orgs and orga_uid not in fct_orgs:
                        continue
                    if addOrModifyGroup(orga, fct_dic['fct_id'], fct_dic['fct_title']):
                        changes = True
            # we detect a removed organization. We dont do anything on exsiting groups
            if old_set.difference(new_set):
                changes = True
        elif event.record.fieldName == 'functions' and registry[ORGANIZATIONS_REGISTRY]:
            old_functions = {dic['fct_id']: {'fct_title': dic['fct_title'], 'fct_orgs': dic['fct_orgs']}
                             for dic in event.oldValue}
            old_set = set(old_functions.keys())
            new_functions = {dic['fct_id']: {'fct_title': dic['fct_title'], 'fct_orgs': dic['fct_orgs']}
                             for dic in event.newValue}
            new_set = set(new_functions.keys())
            # we detect a new function
            add_set = new_set.difference(old_set)
            for new_id in add_set:
                new_title = new_functions[new_id]['fct_title']
                new_orgs = new_functions[new_id]['fct_orgs']
                for orga_uid in registry[ORGANIZATIONS_REGISTRY]:
                    if new_orgs and orga_uid not in new_orgs:
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
                old_function = old_functions.get(new_id, None)
                if not new_orgs:
                    # we have to make sure Plone groups are created for every selected organizations
                    for orga_uid in registry[ORGANIZATIONS_REGISTRY]:
                        orga = uuidToObject(orga_uid)
                        if addOrModifyGroup(orga, new_id, new_title):
                            changes = True
                elif (not old_function and new_orgs) or old_functions[new_id]['fct_orgs'] != new_orgs:
                    # fct_orgs changed, we remove every linked Plone groups
                    # except ones defined in new_orgs
                    for orga_uid in get_organizations(only_selected=False, the_objects=False):
                        if orga_uid in new_orgs:
                            # make sure Plone group is created
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
    registry = getUtility(IRegistry)
    changes = False
    for dic in registry[FUNCTIONS_REGISTRY]:
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
    registry = getUtility(IRegistry)
    # when an organization is removed (and its content), we check if it is used in plonegroup configuration
    if IObjectRemovedEvent.providedBy(event) and organization.UID() in registry[ORGANIZATIONS_REGISTRY]:
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
        if orga_uid in registry[ORGANIZATIONS_REGISTRY]:
            if addOrModifyOrganizationGroups(orga, orga_uid):
                changes = True
    if changes:
        invalidate_sopgv_cache()
        invalidate_sov_cache()
        invalidate_soev_cache()


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
    registry = getUtility(IRegistry)
    terms = []
    # if no function given, use all functions
    functions = functions or get_all_suffixes()
    for orga_uid in registry[ORGANIZATIONS_REGISTRY]:
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
    registry = getUtility(IRegistry)
    # needed to get as manager because plone.formwidget.masterselect calls ++widget++ as Anonymous
    if api.user.is_anonymous():
        with api.env.adopt_roles(['Manager']):
            for orga_uid in registry[ORGANIZATIONS_REGISTRY]:
                title = unrestrictedUuidToObject(orga_uid).get_full_title(separator=separator, first_index=first_index)
                ret.append((orga_uid, title))
    else:
        for orga_uid in registry[ORGANIZATIONS_REGISTRY]:
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


class SelectedOrganizationsElephantVocabulary(object):
    """ Vocabulary of selected plonegroup-organizations services. """
    implements(IVocabularyFactory)

    @ram.cache(voc_cache_key)
    def __call__(self, context):
        factory = getUtility(IVocabularyFactory, 'collective.contact.plonegroup.organization_services')
        vocab = factory(context)
        registry = getUtility(IRegistry)
        terms = vocab.by_value
        ordered_terms = []
        for uid in registry[ORGANIZATIONS_REGISTRY]:
            if uid in terms:
                ordered_terms.append(terms[uid])
                del terms[uid]
        extra_uids = terms.keys()
        extra_terms = terms.values()
        # ordered_vocab = SearchableSimpleVocabulary(ordered_terms + extra_terms)  # bug in widget, trac #15186
        ordered_vocab = SimpleVocabulary(ordered_terms + extra_terms)
        wrapped_vocab = wrap_vocabulary(ordered_vocab, hidden_terms=extra_uids)(context)
        # sort by title
        sorted_vocab = sorted(wrapped_vocab.vocab, key=attrgetter('title'))
        wrapped_vocab.vocab = SimpleVocabulary(sorted_vocab)
        return wrapped_vocab
