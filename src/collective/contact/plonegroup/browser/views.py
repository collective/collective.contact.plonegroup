# -*- coding: utf-8 -*-

from collective.contact.core import _ as _ccc
from collective.contact.plonegroup import _
from collective.contact.plonegroup.config import get_registry_functions
from collective.contact.plonegroup.config import get_registry_groups_mgt
from collective.contact.plonegroup.interfaces import IDGFListField
from collective.contact.plonegroup.interfaces import IDGFVocabularyField
from collective.contact.plonegroup.interfaces import IGroupField
from collective.contact.plonegroup.interfaces import IOrganizationField
from collective.contact.plonegroup.utils import get_organization
from collective.contact.plonegroup.utils import get_plone_group_id
from collective.z3cform.datagridfield import DataGridField
from collective.z3cform.datagridfield import DictRow
from operator import methodcaller
from plone import api
from Products.CMFPlone import PloneMessageFactory as PMF
from z3c.form import button
from z3c.form import field
from z3c.form.form import EditForm
from z3c.form.i18n import MessageFactory as _z3cf
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.validator import SimpleFieldValidator
from z3c.form.widget import FieldWidget
from zExceptions import Redirect
from zope import schema
from zope.interface import implements
from zope.interface import Interface
from zope.schema._bootstrapinterfaces import RequiredMissing


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

    group = OrganizationField(
        title=_ccc(u'Organization'),
        required=False)

    user = DGFVocabularyField(
        title=PMF('text_user'),
        vocabulary='plone.app.vocabularies.Users',
        required=False)


class FieldValidator(SimpleFieldValidator):
    """ Not used """

    def validate(self, value, force=False):
        if value is None or value is self.field.missing_value:
            raise RequiredMissing


class GroupsConfigurationAdapter(object):

    def __init__(self, form):
        self.__dict__['context'] = form.context
        self.__dict__['form'] = form
        self.__dict__['old_values'] = {}

    def __getattr__(self, name):
        if name not in self.form.fieldnames:
            return getattr(self.context, name)
        values = []
        if name == '_old_values_':
            values = str(self.old_values)
        elif name == '_groups_':
            for group_id in sorted(self.form.groupids, key=self.form.groupids.get):
                users = api.user.get_users(groupname=group_id)
                for user in sorted(users, key=lambda u: u.getProperty('fullname', None) or u.id):
                    values.append({'group': group_id, 'user': user.id})
            self.old_values[name] = values
        else:
            for org in sorted(self.form.functions_orgs[name], key=methodcaller('get_full_title')):
                org_uid = org.UID()
                group_id = get_plone_group_id(org_uid, name)
                users = api.user.get_users(groupname=group_id)
                for user in sorted(users, key=lambda u: u.getProperty('fullname', None) or u.id):
                    values.append({'group': org_uid, 'user': user.id})
            self.old_values[name] = values
        return values

    def __setattr__(self, name, value):
        pass


class ManageOwnGroupUsers(EditForm):
    """
        Manage own groups users
    """
    label = _(u'Own groups management view')
    description = _(u'Own groups management description')
    successMessage = _(u'Own groups users succesfully updated.')
    noChangesMessage = _(u'No changes were made.')

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.functions = {}  # will contain function title by function id
        self.functions_orgs = {}  # will contain org list by function id
        self.groupids = {}  # will contain group title by group id
        self.fieldnames = []

    def init(self):
        """ user is now recognized """
        self.current_user = api.user.get_current()
#        self.current_user = api.user.get(userid='chef')
        self.current_user_id = self.current_user.getId()
        self.current_user_groups = [g for g in api.group.get_groups(user=self.current_user) if g]

    def get_manageable_functions(self):
        """ get all manageable functions """
        for fct in get_registry_functions(as_copy=False):
            if fct['fct_management']:
                self.functions[fct['fct_id']] = fct['fct_title']
        return self.functions.keys()

    def get_user_manageable_functions(self):
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
            org = get_organization(parts[0])
            if org not in self.functions_orgs[group_suffix]:
                self.functions_orgs[group_suffix].append(get_organization(parts[0]))

    def get_manageable_groups(self):
        """ get selected manageable groups """
        return get_registry_groups_mgt()

    def get_user_manageable_groups(self):
        """ get user manageable groups """
        manageable_groups = self.get_manageable_groups()
        for group in self.current_user_groups:
            if group.id not in manageable_groups:
                continue
            self.groupids[group.id] = group.getProperty('title')

    def getContent(self):
        return GroupsConfigurationAdapter(self)

    @property
    def fields(self):
        self.init()  # second init with user recognized
        fields = []
        description = _(u'You can <span class="cross_icon">remove</span> an assignment with the '
                        u'<span class="cross_icon">cross icon</span>. '
                        u'You can <span class="auto_append">add</span> a new assignment with the '
                        u'<span class="auto_append">blue line</span>. '
                        u'You can <span class="new_line">complete</span> it on the '
                        u'<span class="new_line">brown line</span>.')
        self.get_user_manageable_functions()
        for function in self.functions_orgs:
            fld = DGFListField(
                __name__=function,
                title=_(u"Assignments for groups related to '${function}' function",
                        mapping={'function': self.functions[function]}),
                description=description,
                required=False,
                value_type=DictRow(title=u"org_users", schema=IOrganisationsUsers, required=False))
            fields.append(fld)
        fields = sorted(fields, key=lambda x: x.title)

        self.get_user_manageable_groups()
        if self.groupids:
            fld = DGFListField(
                __name__='_groups_',
                title=_('Global groups assignments.'),
                description=description,
                required=False,
                value_type=DictRow(title=u"users", schema=IGroupsUsers, required=False))
            fields.insert(0, fld)

        fld = schema.TextLine(
            __name__='_old_values_',
            title=u'not_showed',
            required=False,
        )
        fields.append(fld)

        self.fieldnames = [afield.__name__ for afield in fields]
        return field.Fields(*fields)

#    def datagridInitialise(self, subform, widget):
#        pass

#    def datagridUpdateWidgets(self, subform, widgets, widget):
#        pass

    def updateWidgets(self):
        super(ManageOwnGroupUsers, self).updateWidgets()
        for wid in self.widgets:
            if wid == '_old_values_':
                self.widgets[wid].mode = HIDDEN_MODE
            else:
                self.widgets[wid].allow_reorder = False
                self.widgets[wid].allow_insert = False
                self.widgets[wid].allow_delete = True
                self.widgets[wid].auto_append = True

    @button.buttonAndHandler(_z3cf('Apply'), name='apply')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        changes = False
        users = {}
        old_values = eval(data.pop('_old_values_'))
        for name in old_values:
            try:
                new_value = data[name]  # If the field is not in the data, then go on to the next one
            except KeyError:
                continue
            new_value = set([(dic['group'], dic['user']) for dic in data[name]])
            old_value = set([(dic['group'], dic['user']) for dic in old_values[name]])
            if old_value == new_value:
                continue
            for action, result in (('removed', old_value - new_value), ('added', new_value - old_value)):
                for (group_id, user_id) in result:
                    if group_id is None or user_id is None:
                        required_message = _(u"There was a problem in added assignments. "
                                             u"Don't forget to complete the 2 columns! "
                                             u"You have to redo all the manipulations.")
                        api.portal.show_message(message=required_message, request=self.request, type='error')
                        raise Redirect(self.request.get('ACTUAL_URL'))
                    if user_id == self.current_user_id:
                        user_message = _(u"You cannot remove your user from a group!")
                        api.portal.show_message(message=user_message, request=self.request, type='error')
                        raise Redirect(self.request.get('ACTUAL_URL'))
                    if name != '_groups_':
                        group_id = get_plone_group_id(group_id, name)
                    if group_id not in users:
                        users[group_id] = [u.id for u in api.user.get_users(groupname=group_id)]
                    if action == 'removed' and user_id in users[group_id]:
                        api.group.remove_user(groupname=group_id, username=user_id)
                        changes = True
                    elif action == 'added' and user_id not in users[group_id]:
                        api.group.add_user(groupname=group_id, username=user_id)
                        changes = True
        if changes:
            api.portal.show_message(message=self.successMessage, request=self.request)
        else:
            api.portal.show_message(message=self.noChangesMessage, request=self.request, type='warn')
        self.request.response.redirect(self.request.get('ACTUAL_URL'))

    @button.buttonAndHandler(PMF(u'return_to_view'), name='cancel')
    def handleCancel(self, action):
        self.request.response.redirect(self.request.get('URL1'))
