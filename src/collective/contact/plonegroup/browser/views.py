# -*- coding: utf-8 -*-

from collective.contact.core import _ as _ccc
from collective.contact.plonegroup import _
from collective.contact.plonegroup.config import get_registry_functions
from collective.contact.plonegroup.interfaces import IDGFListField
from collective.contact.plonegroup.interfaces import IDGFVocabularyField
from collective.contact.plonegroup.interfaces import IGroupField
from collective.contact.plonegroup.interfaces import IOrganizationField
from collective.contact.plonegroup.utils import get_all_suffixes
from collective.contact.plonegroup.utils import get_organization
from collective.contact.plonegroup.utils import get_plone_group_id
from collective.z3cform.datagridfield import DataGridField
from collective.z3cform.datagridfield import DictRow
from copy import deepcopy
from OFS.interfaces import IItem
from operator import methodcaller
from plone import api
from Products.CMFPlone import PloneMessageFactory as PMF
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from z3c.form import field
from z3c.form.form import EditForm
from z3c.form.widget import FieldWidget
from zope import schema
from zope.component import adapts
from zope.interface import implements
from zope.interface import Interface


class DGFListField(schema.List):
    implements(IDGFListField)


def dgf_list_widget(field, request):
    return FieldWidget(field, DataGridField(request))


class GroupField(schema.Choice):
    implements(IGroupField)

    def __init__(self, *args, **kwargs):
        kwargs['vocabulary'] = u''
        super(GroupField, self).__init__(*args, **kwargs)


class OrganizationField(schema.Choice):
    implements(IOrganizationField)

    def __init__(self, *args, **kwargs):
        kwargs['vocabulary'] = u''
        super(OrganizationField, self).__init__(*args, **kwargs)


class DGFVocabularyField(schema.Choice):
    implements(IDGFVocabularyField)


class IGroupsUsers(Interface):

    group = GroupField(
        title=PMF('text_group'),
        vocabulary='plone.app.vocabularies.Groups',
        required=False)

    user = DGFVocabularyField(
        title=PMF('text_user'),
        vocabulary='plone.app.vocabularies.Users',
        required=False)


class IOrganisationsUsers(Interface):

    organization = OrganizationField(
        title=_ccc(u'Organization'),
        required=False)

    user = DGFVocabularyField(
        title=PMF('text_user'),
        vocabulary='plone.app.vocabularies.Users',
        required=False)


class GroupsConfigurationAdapter(object):
#    adapts(IPloneSiteRoot)
    adapts(IItem)

    def __init__(self, context, functions_orgs, groupids):
        self.__dict__['context'] = context
        self.__dict__['functions_orgs'] = functions_orgs
        self.__dict__['groupids'] = groupids

    def __getattr__(self, name):
        if name.startswith('__'):
            return getattr(self.context, name)
        values = []
        if name == '_groups_':
            for group_id in sorted(self.groupids, key=self.groupids.get):
                users = api.user.get_users(groupname=group_id)
                for user in sorted(users, key=lambda u: u.getProperty('fullname', None) or u.id):
                    values.append({'group': group_id, 'user': user.id})
        else:
            for org in sorted(self.functions_orgs[name], key=methodcaller('get_full_title')):
                org_uid = org.UID()
                group_id = get_plone_group_id(org_uid, name)
                users = api.user.get_users(groupname=group_id)
                for user in sorted(users, key=lambda u: u.getProperty('fullname', None) or u.id):
                    values.append({'organization': org_uid, 'user': user.id})
        return values

    def __setattr__(self, name, value):
        pass


class ManageOwnGroupUsers(EditForm):
    """
        Manage own groups users
    """
    label = _(u'Own groups management')
    successMessage = _(u'Own groups users succesfully updated.')
    noChangesMessage = _(u'No changes were made.')
    buttons = deepcopy(EditForm.buttons)
    buttons['apply'].title = PMF(u'Save')

    def __init__(self, context, request):
        self.original_context = context
        self.context = context
        self.request = request
        self.current_user = api.user.get_current()
        self.current_user = api.user.get(userid='chef')
        self.functions = {}  # will contain function title by function id
        self.functions_orgs = {}  # will contain org list by function id
        self.groupids = {}  # will contain group title by group id
        self.current_user_groups = api.group.get_groups(user=self.current_user)

    def get_manageable_functions(self):
        """ get all manageable functions """
        for fct in get_registry_functions(as_copy=False):
            self.functions[fct['fct_id']] = fct['fct_title']
        return self.functions.keys()

    def get_user_manageable_functions(self, user):
        """ get user manageable functions """
        manageable_functions = self.get_manageable_functions()
        for group in self.current_user_groups:
            parts = group.id.split('_')
            if len(parts) == 1:
                continue
            group_suffix = '_'.join(parts[1:])
            if group_suffix not in manageable_functions:
                continue
            if group_suffix not in self.functions_orgs:
                self.functions_orgs[group_suffix] = []
            self.functions_orgs[group_suffix].append(get_organization(parts[0]))

    def get_manageable_groups(self):
        """ get all manageable groups. Return all groups but suffixed groups """
        all_suffixes = get_all_suffixes()
        ret = []
        for group in api.group.get_groups():
            if group.id in ('Administrators', 'Reviewers', 'Site Administrators', 'AuthenticatedUsers'):
                continue
            parts = group.id.split('_')
            if len(parts) > 1:
                group_suffix = '_'.join(parts[1:])
                if group_suffix in all_suffixes:
                    continue
            ret.append(group.id)
        return ret

    def get_user_manageable_groups(self, user):
        """ get user manageable groups """
        manageable_groups = self.get_manageable_groups()
        for group in self.current_user_groups:
            if group.id not in manageable_groups:
                continue
            self.groupids[group.id] = group.getProperty('title')

    def getContent(self):
        adapted = GroupsConfigurationAdapter(self.original_context, self.functions_orgs, self.groupids)
        return adapted

    @property
    def fields(self):
        fields = []
        self.get_user_manageable_functions(self.current_user)
        for function in self.functions_orgs:
            fld = DGFListField(
                __name__=function,
                title=self.functions[function],
                description=u'',
                required=False,
                value_type=DictRow(title=u"org_users", schema=IOrganisationsUsers, required=False))
            fields.append(fld)
        fields = sorted(fields, key=lambda x: x.title)

        self.get_user_manageable_groups(self.current_user)
        if self.groupids:
            fld = DGFListField(
                __name__='_groups_',
                title=_('Global groups'),
                description=u'',
                required=False,
                value_type=DictRow(title=u"users", schema=IGroupsUsers, required=False))
            fields.insert(0, fld)

        return field.Fields(*fields)

    def datagridInitialise(self, subform, widget):
        pass

    def datagridUpdateWidgets(self, subform, widgets, widget):
        pass

    def updateWidgets(self):
        super(ManageOwnGroupUsers, self).updateWidgets()
        for wid in self.widgets:
            self.widgets[wid].allow_reorder = False
            self.widgets[wid].allow_insert = False
            self.widgets[wid].allow_delete = True
            self.widgets[wid].auto_append = True

    @button.buttonAndHandler(PMF(u'return_to_view'), name='cancel')
    def handleCancel(self, action):
        self.request.response.redirect(self.request.get('URL1'))
