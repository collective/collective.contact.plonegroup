# -*- coding: utf-8 -*-

from collective.contact.core import _ as _ccc
from collective.contact.plonegroup import _
from collective.contact.plonegroup.config import get_registry_functions
from collective.contact.plonegroup.interfaces import IDGFVocabularyField
from collective.contact.plonegroup.interfaces import IOrganizationField, IOrganisationsUsersField
from collective.contact.plonegroup.utils import get_organization
from collective.contact.plonegroup.utils import get_plone_group_id
from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield import DictRow
from OFS.interfaces import IItem
from operator import methodcaller
from plone import api
from Products.CMFPlone import PloneMessageFactory as PMF
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from z3c.form import field
from z3c.form.form import EditForm
from zope import schema
from zope.component import adapts
from zope.interface import implements
from zope.interface import Interface
from z3c.form.widget import FieldWidget
from collective.z3cform.datagridfield import DataGridField
from z3c.form.interfaces import DISPLAY_MODE


class OrganizationField(schema.Choice):
    implements(IOrganizationField)

    def __init__(self, *args, **kwargs):
        kwargs['vocabulary'] = u''
        super(OrganizationField, self).__init__(*args, **kwargs)

#    def bind(self, object):
#        return super(schema.Choice, self).bind(object)


class DGFVocabularyField(schema.Choice):
    implements(IDGFVocabularyField)


class OrganisationsUsersField(schema.List):
    implements(IOrganisationsUsersField)


def organizations_users_widget(field, request):
    return FieldWidget(field, DataGridField(request))


class IOrganisationsUsers(Interface):

    organization = OrganizationField(
        title=_ccc(u'Organization'),
        required=True)

    user = DGFVocabularyField(
        title=PMF('text_user'),
        vocabulary='plone.app.vocabularies.Users',
        required=True)


class GroupsConfigurationAdapter(object):
#    adapts(IPloneSiteRoot)
    adapts(IItem)

    def __init__(self, context, functions_orgs):
        self.__dict__['context'] = context
        self.__dict__['functions_orgs'] = functions_orgs

    def __getattr__(self, name):
        if name.startswith('__'):
            return getattr(self.context, name)
        values = []
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
#    fields = Fields(IPSTAction).select('budget_split')
#    fields['budget_split'].widgetFactory = DataGridFieldFactory

    def __init__(self, context, request):
        self.original_context = context
        self.context = context
        self.request = request
        self.current_user = api.user.get_current()
        self.current_user = api.user.get(userid='chef')
        self.functions = {}  # will contain function title by function id
        self.functions_orgs = {}  # will contain org list by function id

    def get_manageable_functions(self):
        """ get all manageable functions """
        for fct in get_registry_functions(as_copy=False):
            self.functions[fct['fct_id']] = fct['fct_title']
        return self.functions.keys()

    def get_user_manageable_functions(self, user):
        """ get user manageable functions """
        groups = api.group.get_groups(user=user)
        for group in groups:
            parts = group.id.split('_')
            if len(parts) == 1:
                continue
            group_suffix = '_'.join(parts[1:])
            if group_suffix not in self.get_manageable_functions():
                continue
            if group_suffix not in self.functions_orgs:
                self.functions_orgs[group_suffix] = []
            self.functions_orgs[group_suffix].append(get_organization(parts[0]))
        self.functions_orgs

    def getContent(self):
        adapted = GroupsConfigurationAdapter(self.original_context, self.functions_orgs)
        return adapted

    @property
    def fields(self):
        fields = []
        self.get_user_manageable_functions(self.current_user)
        for function in self.functions_orgs:
            fld = OrganisationsUsersField(
                __name__=function,
                title=self.functions[function],
                description=u'',
                required=False,
                value_type=DictRow(title=u"org_users", schema=IOrganisationsUsers, required=False))
            #fld.widgetFactory = DataGridFieldFactory
            fields.append(fld)
        fields = sorted(fields, key=lambda x: x.title)
        return field.Fields(*fields)

    def datagridUpdateWidgets(self, subform, widgets, widget):
        pass

    def updateWidgets(self):
        super(ManageOwnGroupUsers, self).updateWidgets()
        for wid in self.widgets:
            self.widgets[wid].allow_reorder = False
            self.widgets[wid].allow_insert = False
            self.widgets[wid].allow_delete = True
            self.widgets[wid].auto_append = True

    @button.buttonAndHandler(PMF('Save'), name='save')
    def handleAdd(self, action):

        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        #self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(self.successMessage, "info",)

    @button.buttonAndHandler(PMF(u'return_to_view'), name='cancel')
    def handleCancel(self, action):
        self.request.response.redirect(self.request.get('URL1'))
