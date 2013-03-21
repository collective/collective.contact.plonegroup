# -*- coding: utf-8 -*-

from zope import schema
from zope.interface import Interface
from z3c.form import form
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.autoform.directives import widget
#from plone.formwidget.contenttree import PathSourceBinder
#from plone.formwidget.contenttree import MultiContentTreeFieldWidget
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


class SettingsEditForm(RegistryEditForm):
    """
    Define form logic
    """
    form.extends(RegistryEditForm)
    schema = IContactPlonegroupConfig

SettingsView = layout.wrap_form(SettingsEditForm, ControlPanelFormWrapper)
