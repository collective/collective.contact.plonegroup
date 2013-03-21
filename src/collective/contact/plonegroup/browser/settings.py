# -*- coding: utf-8 -*-

from zope import schema
from zope.component import getUtility
from zope.interface import Interface
from z3c.form import form
from plone import api
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.autoform.directives import widget
#from plone.formwidget.contenttree import PathSourceBinder
#from plone.formwidget.contenttree import MultiContentTreeFieldWidget
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


class IContactPlonegroupConfig(Interface):
    """
        Configuration schema
    """

    # plone.registry cannot store schema.Choice different from source !
    #organizations = schema.List(
    #    title=_(u'Selected organizations'),
    #    description=_(u"Choose multiple organization levels for which you want to create a plone group."),
    #    value_type=schema.Choice(title=u"Selection",
    #                             source=PathSourceBinder(portal_type='organization')))
    #
    #widget(organizations=MultiContentTreeFieldWidget)

    organizations = schema.List(
        title=_(u'Selected organizations'),
        description=_(u"Choose multiple organization levels for which you want to create a plone group."),
        value_type=DictRow(title=_("Organization"),
                           schema=IOrganizationSchema)
    )
    widget(organizations=DataGridFieldFactory)

    functions = schema.List(
        title=_(u'Function list'),
        description=_(u'Each defined function will suffix each organization plone group.'),
        value_type=DictRow(title=_("Function"),
                           schema=IFunctionSchema)
    )
    widget(functions=DataGridFieldFactory)


def addOrModifyGroup(group_name, organization_title, function_title):
    """
        create a plone group
    """
    if isinstance(organization_title, unicode):
        organization_title = organization_title.encode('utf8')
    if isinstance(function_title, unicode):
        function_title = function_title.encode('utf8')
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
        if event.record.fieldName == 'organizations':
            old_set = set([(dic['org_id'], dic['org_title']) for dic in event.oldValue])
            new_set = set([(dic['org_id'], dic['org_title']) for dic in event.newValue])
            # we detect a new organization
            add_set = new_set.difference(old_set)
            registry = getUtility(IRegistry)
            for (new_id, new_title) in add_set:
                for fct_dic in registry['collective.contact.plonegroup.browser.settings.'
                                        'IContactPlonegroupConfig.functions']:
                    group_name = "%s_%s" % (new_id, fct_dic['fct_id'])
                    addOrModifyGroup(group_name, new_title, fct_dic['fct_title'])


class SettingsEditForm(RegistryEditForm):
    """
    Define form logic
    """
    form.extends(RegistryEditForm)
    schema = IContactPlonegroupConfig

SettingsView = layout.wrap_form(SettingsEditForm, ControlPanelFormWrapper)
