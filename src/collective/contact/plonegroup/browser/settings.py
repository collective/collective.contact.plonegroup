# -*- coding: utf-8 -*-

from zope import schema
from zope.app.component.hooks import getSite
from zope.component import getUtility
from zope.interface import Interface, Invalid, invariant
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from z3c.form import form
from five import grok
from plone import api
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.uuid.utils import uuidToObject
from plone.autoform.directives import widget
from plone.registry.interfaces import IRecordModifiedEvent, IRegistry
from plone.z3cform import layout
from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.registry import DictRow
from .. import _


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
    fct_id = schema.TextLine(title=_("Plone group suffix id"), required=True)
    fct_title = schema.TextLine(title=_("Plone group suffix title"), required=True)


class OwnOrganizationServicesVocabulary(grok.GlobalUtility):
    """Vocabulary of own organizations services"""
    grok.name('collective.contact.plonegroup.organization_services')
    grok.implements(IVocabularyFactory)

    def listSubOrganizations(self, terms, folder, parent_label='', parent_id=''):
        for orga in folder.listFolderContents(contentFilter={'portal_type': 'organization'}):
            term_title = orga.Title()
            if parent_label:
                term_title = "%s - %s" % (parent_label, term_title)
            term_token = orga.getId()
            if parent_id:
                term_token = "%s|%s" % (parent_id, term_token)
            terms.append(SimpleTerm(orga.UID(), term_token, term_title))
            self.listSubOrganizations(terms, orga, term_title, term_token)

    def __call__(self, context):
        portal = getSite()
        terms = []
        pcat = portal.portal_catalog
        brains = pcat(portal_type='organization', id='own-organization')
        if not brains:
            terms.append(SimpleTerm(None, token="unfound",
                                    title=_(u"You must define an organization with id 'own-organization' !")))
            return SimpleVocabulary(terms)
        elif len(brains) > 1:
            terms.append(SimpleTerm(None, token="multifound",
                                    title=_(u"You must have only one organization with id 'own-organization' !")))
            return SimpleVocabulary(terms)

        own_orga = brains[0].getObject()
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

    functions = schema.List(
        title=_(u'Function list'),
        description=_(u'Each defined function will suffix each organization plone group.'),
        required=True,
        value_type=DictRow(title=_("Function"),
                           schema=IFunctionSchema)
    )
    widget(functions=DataGridFieldFactory)

    @invariant
    def validateSettings(data):
        if not data.organizations:
            raise Invalid(_(u"You must choose at least one organization !"))
        if len(data.organizations) == 1 and data.organizations[0] is None:
            raise Invalid(_(u"You must correct the organization error first !"))
        if not data.functions:
            raise Invalid(_(u"You must define at least one function !"))


def addOrModifyGroup(group_name, organization_title, function_title):
    """
        create a plone group
    """
    if isinstance(organization_title, unicode):
        organization_title = organization_title.encode('utf8')
    if isinstance(function_title, unicode):
        function_title = function_title.encode('utf8')
    if isinstance(group_name, unicode):
        group_name = group_name.encode('utf8')
    group = api.group.get(groupname=group_name)
    group_title = '%s (%s)' % (organization_title, function_title)
    if group is None:
        group = api.group.create(
            groupname=group_name,
            title=group_title,
        )
    else:
        #group_title is maybe modified
        if group.getProperty('title') != group_title:
            group.setProperties(title=group_title)


def detectContactPlonegroupChange(event):
    """
        Manage our record changes
    """
    if IRecordModifiedEvent.providedBy(event) and event.record.interface == IContactPlonegroupConfig:
        registry = getUtility(IRegistry)
        if event.record.fieldName == 'organizations' and registry['collective.contact.plonegroup.browser'
                                                                  '.settings.IContactPlonegroupConfig.functions']:
            old_set = set(event.oldValue)
            new_set = set(event.newValue)
            # we detect a new organization
            add_set = new_set.difference(old_set)
            for uid in add_set:
                obj = uuidToObject(uid)
                full_title = obj.get_full_title().replace('/', '-')
                for fct_dic in registry['collective.contact.plonegroup.browser.settings.'
                                        'IContactPlonegroupConfig.functions']:
                    group_name = "%s_%s" % (uid, fct_dic['fct_id'])
                    addOrModifyGroup(group_name, full_title, fct_dic['fct_title'])
            # we detect a removed organization
        elif event.record.fieldName == 'functions' and registry['collective.contact.plonegroup.browser.settings.'
                                                                'IContactPlonegroupConfig.organizations']:
            old_set = new_set = set()
            if event.oldValue:
                old_set = set([(dic['fct_id'], dic['fct_title']) for dic in event.oldValue])
            if event.newValue:
                new_set = set([(dic['fct_id'], dic['fct_title']) for dic in event.newValue])
            # we detect a new function
            add_set = new_set.difference(old_set)
            registry = getUtility(IRegistry)
            for (new_id, new_title) in add_set:
                for uid in registry['collective.contact.plonegroup.browser.settings.'
                                    'IContactPlonegroupConfig.organizations']:
                    obj = uuidToObject(uid)
                    group_name = "%s_%s" % (uid, new_id)
                    addOrModifyGroup(group_name, obj.Title(), new_title)
            # we detect a removed function


class SettingsEditForm(RegistryEditForm):
    """
    Define form logic
    """
    form.extends(RegistryEditForm)
    schema = IContactPlonegroupConfig

SettingsView = layout.wrap_form(SettingsEditForm, ControlPanelFormWrapper)
