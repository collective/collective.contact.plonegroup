# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from collective.contact.plonegroup.browser import settings
from collective.contact.plonegroup.config import DEFAULT_DIRECTORY_ID
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.config import get_registry_functions
from collective.contact.plonegroup.config import get_registry_organizations
from collective.contact.plonegroup.config import set_registry_functions
from collective.contact.plonegroup.config import set_registry_organizations
from collective.contact.plonegroup.testing import IntegrationTestCase
from collective.contact.plonegroup.utils import get_own_organization
from collective.contact.plonegroup.utils import get_plone_group_id
from plone import api
from plone.app.testing import TEST_USER_ID
from z3c.form import validator
from zExceptions import Redirect
from zope import event
from zope.component import getUtility
from zope.i18n import translate
from zope.interface import Invalid
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema.interfaces import IVocabularyFactory


class TestSettings(IntegrationTestCase):
    """Test collective.contact.plonegroup settings."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        # Organizations creation
        self.portal.invokeFactory('directory', DEFAULT_DIRECTORY_ID)
        self.portal[DEFAULT_DIRECTORY_ID].invokeFactory('organization', PLONEGROUP_ORG, title='My organization')
        own_orga = get_own_organization()
        own_orga.invokeFactory('organization', 'department1', title='Department 1')
        own_orga.invokeFactory('organization', 'department2', title='Department 2')
        own_orga['department1'].invokeFactory('organization', 'service1', title='Service 1')
        own_orga.invokeFactory('organization', 'inactive_department', title='Inactive department')
        inactive_department = own_orga['inactive_department']
        api.content.transition(obj=inactive_department, transition='deactivate')

        set_registry_organizations([own_orga['department1'].UID(),
                                   own_orga['department1']['service1'].UID(),
                                   own_orga['department2'].UID()])
        set_registry_functions([{'fct_title': u'Director',
                                 'fct_id': u'director',
                                 'fct_orgs': [],
                                 'fct_management': False,
                                 'enabled': True},
                                {'fct_title': u'Worker',
                                 'fct_id': u'worker',
                                 'fct_orgs': [],
                                 'fct_management': False,
                                 'enabled': True}])

    def test_OwnOrganizationServicesVocabulary(self):
        """ Test vocabulary """
        services = getUtility(IVocabularyFactory, name=u'collective.contact.plonegroup.organization_services')
        voc_dic = services(self).by_token
        voc_list = [voc_dic[key].title for key in voc_dic.keys()]
        self.assertSetEqual(set(voc_list), set(['Department 1 - Service 1', 'Department 1', 'Department 2']))
        self.assertNotIn('Inactive department', voc_list)
        # When multiple own organizations
        self.portal[DEFAULT_DIRECTORY_ID].invokeFactory('organization', 'temporary', title='Temporary')
        self.portal[DEFAULT_DIRECTORY_ID]['temporary'].invokeFactory(
            'organization', PLONEGROUP_ORG, title='Duplicated organization')
        services = getUtility(IVocabularyFactory, name=u'collective.contact.plonegroup.organization_services')
        voc_dic = services(self).by_token
        voc_list = [voc_dic[key].title for key in voc_dic.keys()]
        self.assertEqual(len(voc_list), 1)
        self.assertEqual(
            translate(voc_list[0]),
            u"You must have only one 'organization' with id 'plonegroup-organization' !")
        self.portal[DEFAULT_DIRECTORY_ID].manage_delObjects(ids=['temporary'])
        # When own organization not found
        self.portal[DEFAULT_DIRECTORY_ID].manage_delObjects(ids=[PLONEGROUP_ORG])
        services = getUtility(IVocabularyFactory, name=u'collective.contact.plonegroup.organization_services')
        voc_dic = services(self).by_token
        voc_list = [voc_dic[key].title for key in voc_dic.keys()]
        self.assertEqual(len(voc_list), 1)
        self.assertEqual(
            translate(voc_list[0]),
            u"You must define one 'organization' with id 'plonegroup-organization' !")

    def test_detectContactPlonegroupChange(self):
        """Test if group creation works correctly"""
        group_ids = [group.id for group in api.group.get_groups()]
        organizations = get_registry_organizations()
        for uid in organizations:
            self.assertIn('%s_director' % uid, group_ids)
            self.assertIn('%s_worker' % uid, group_ids)
        d1_d_group = api.group.get(groupname='%s_director' % organizations[0])
        self.assertEquals(d1_d_group.getProperty('title'), 'Department 1 (Director)')
        d1s1_d_group = api.group.get(groupname='%s_director' % organizations[1])
        self.assertEquals(d1s1_d_group.getProperty('title'), 'Department 1 - Service 1 (Director)')
        # Changing function title
        set_registry_functions([{'fct_title': u'Directors',
                                 'fct_id': u'director',
                                 'fct_orgs': [],
                                 'fct_management': False,
                                 'enabled': True},
                                {'fct_title': u'Worker',
                                 'fct_id': u'worker',
                                 'fct_orgs': [],
                                 'fct_management': False,
                                 'enabled': True}])
        d1_d_group = api.group.get(groupname='%s_director' % organizations[0])
        self.assertEquals(d1_d_group.getProperty('title'), 'Department 1 (Directors)')
        d1s1_d_group = api.group.get(groupname='%s_director' % organizations[1])
        self.assertEquals(d1s1_d_group.getProperty('title'), 'Department 1 - Service 1 (Directors)')
        # Adding new organization
        own_orga = get_own_organization()
        own_orga['department2'].invokeFactory('organization', 'service2', title='Service 2')
        # append() method on the registry doesn't trigger the event. += too
        newValue = get_registry_organizations() + [own_orga['department2']['service2'].UID()]
        set_registry_organizations(newValue)
        group_ids = [group.id for group in api.group.get_groups()]
        last_uid = get_registry_organizations()[-1]
        self.assertIn('%s_director' % last_uid, group_ids)
        self.assertIn('%s_worker' % last_uid, group_ids)
        # Adding new function
        newValue = get_registry_functions() + [{'fct_title': u'Chief',
                                                'fct_id': u'chief',
                                                'fct_orgs': [],
                                                'fct_management': False,
                                                'enabled': True}]
        set_registry_functions(newValue)
        group_ids = [group.id for group in api.group.get_groups() if '_' in group.id]
        self.assertEquals(len(group_ids), 12)
        for uid in get_registry_organizations():
            self.assertIn('%s_director' % uid, group_ids)
            self.assertIn('%s_chief' % uid, group_ids)
            self.assertIn('%s_worker' % uid, group_ids)

    def test_detectContactPlonegroupChangeRemoveFunction(self):
        """When a function is removed, every linked Plone groups are deleted as well.
           This is protected by validateSettings that checks first that every Plone groups are empty."""
        own_orga = get_own_organization()
        dep1 = own_orga['department1']
        plone_group_id = get_plone_group_id(dep1.UID(), 'director')
        self.assertTrue(api.group.get(plone_group_id))
        functions = get_registry_functions()
        # remove 'director'
        functions.pop(0)
        set_registry_functions(functions)
        # the linked Plone groups are deleted
        self.assertFalse(api.group.get(plone_group_id))

    def test_detectContactPlonegroupChangeDisableFunction(self):
        """When a function is disabled (enabled=False), every linked Plone groups are deleted as well.
           This is protected by validateSettings that checks first that every Plone groups are empty."""
        own_orga = get_own_organization()
        dep1 = own_orga['department1']
        plone_group_id = get_plone_group_id(dep1.UID(), 'director')
        self.assertTrue(api.group.get(plone_group_id))
        functions = get_registry_functions()
        # disable 'director'
        functions[0]['enabled'] = False
        set_registry_functions(functions)
        # the linked Plone groups are deleted
        self.assertFalse(api.group.get(plone_group_id))

    def test_detectContactPlonegroupChangeSelectOrgs(self):
        """When selecting 'fct_orgs' on a function, Plone groups are create/deleted depending
           on the fact that 'fct_orgs' is empty or contains some organization uids."""
        own_orga = get_own_organization()
        dep1 = own_orga['department1']
        dep1_uid = dep1.UID()
        dep2 = own_orga['department2']
        dep2_uid = dep2.UID()
        dep1_plone_group_id = get_plone_group_id(dep1_uid, 'director')
        dep2_plone_group_id = get_plone_group_id(dep2_uid, 'director')
        self.assertTrue(api.group.get(dep1_plone_group_id))
        self.assertTrue(api.group.get(dep2_plone_group_id))
        # select dep2_uid for 'director'
        functions = get_registry_functions()
        functions[0]['fct_orgs'] = [dep2_uid]
        set_registry_functions(functions)
        # dep1 director Plone group is deleted
        self.assertFalse(api.group.get(dep1_plone_group_id))
        self.assertTrue(api.group.get(dep2_plone_group_id))
        # select dep1_uid for 'director'
        functions = get_registry_functions()
        functions[0]['fct_orgs'] = [dep1_uid]
        set_registry_functions(functions)
        self.assertTrue(api.group.get(dep1_plone_group_id))
        self.assertFalse(api.group.get(dep2_plone_group_id))
        # select nothing for 'director', every groups are created
        functions = get_registry_functions()
        functions[0]['fct_orgs'] = []
        set_registry_functions(functions)
        self.assertTrue(api.group.get(dep1_plone_group_id))
        self.assertTrue(api.group.get(dep2_plone_group_id))
        # select both dep1 and dep2, every groups are created
        functions = get_registry_functions()
        functions[0]['fct_orgs'] = [dep1_uid, dep2_uid]
        set_registry_functions(functions)
        self.assertTrue(api.group.get(dep1_plone_group_id))
        self.assertTrue(api.group.get(dep2_plone_group_id))
        # Changing function title
        dep1_plone_group = api.group.get(dep1_plone_group_id)
        self.assertEquals(dep1_plone_group.getProperty('title'), 'Department 1 (Director)')
        dep2_plone_group = api.group.get(dep2_plone_group_id)
        self.assertEquals(dep2_plone_group.getProperty('title'), 'Department 2 (Director)')
        functions[0]['fct_title'] = u'New title'
        set_registry_functions(functions)
        dep1_plone_group = api.group.get(dep1_plone_group_id)
        self.assertEquals(dep1_plone_group.getProperty('title'), 'Department 1 (New title)')
        dep2_plone_group = api.group.get(dep2_plone_group_id)
        self.assertEquals(dep2_plone_group.getProperty('title'), 'Department 2 (New title)')

    def test_validateSettingsRemoveFunction(self):
        """A function may only be removed if every linked Plone groups are empty."""
        # add a user to group department1 director
        own_orga = get_own_organization()
        dep1 = own_orga['department1']
        plone_group_id = get_plone_group_id(dep1.UID(), 'director')
        api.group.add_user(groupname=plone_group_id, username=TEST_USER_ID)
        invariants = validator.InvariantsValidator(
            None, None, None, settings.IContactPlonegroupConfig, None)
        orgs = get_registry_organizations()
        functions = get_registry_functions()
        data = {'organizations': orgs, 'functions': functions}
        # for now it validates correctly
        self.assertFalse(invariants.validate(data))
        # remove 'director'
        functions.pop(0)
        errors = invariants.validate(data)
        self.assertTrue(isinstance(errors[0], Invalid))
        error_msg = translate(
            msgid=u"can_not_remove_function_every_plone_groups_not_empty",
            domain='collective.contact.plonegroup',
            mapping={'removed_function': 'director',
                     'plone_group_id': plone_group_id})
        self.assertEqual(translate(errors[0].message), error_msg)
        # remove user from plone group, now it validates
        api.group.remove_user(groupname=plone_group_id, username=TEST_USER_ID)
        self.assertFalse(invariants.validate(data))

    def test_validateSettingsDisableFunction(self):
        """A function may only be disabled (enabled=False)
           if every linked Plone groups are empty."""
        # add a user to group department1 director
        own_orga = get_own_organization()
        dep1 = own_orga['department1']
        plone_group_id = get_plone_group_id(dep1.UID(), 'director')
        api.group.add_user(groupname=plone_group_id, username=TEST_USER_ID)
        invariants = validator.InvariantsValidator(
            None, None, None, settings.IContactPlonegroupConfig, None)
        orgs = get_registry_organizations()
        functions = get_registry_functions()
        data = {'organizations': orgs, 'functions': functions}
        # for now it validates correctly
        self.assertFalse(invariants.validate(data))
        # disable 'director'
        functions[0]['enabled'] = False
        errors = invariants.validate(data)
        self.assertTrue(isinstance(errors[0], Invalid))
        error_msg = translate(
            msgid=u"can_not_disable_suffix_plone_groups_not_empty",
            domain='collective.contact.plonegroup',
            mapping={'removed_function': 'director',
                     'plone_group_id': plone_group_id})
        self.assertEqual(translate(errors[0].message), error_msg)
        # remove user from plone group, now it validates
        api.group.remove_user(groupname=plone_group_id, username=TEST_USER_ID)
        self.assertFalse(invariants.validate(data))

    def test_validateSettingsSelectFunctionOrgsOnExistingFunction(self):
        """Selecting 'fct_orgs' for an existing function (so for which Plone groups are already created),
           is only possible if groups that will be deleted (Plone groups of organizations not selected
           as 'fct_orgs') are empty."""
        # add a user to group department1 director
        own_orga = get_own_organization()
        dep1 = own_orga['department1']
        dep2 = own_orga['department2']
        plone_group_id = get_plone_group_id(dep1.UID(), 'director')
        api.group.add_user(groupname=plone_group_id, username=TEST_USER_ID)
        invariants = validator.InvariantsValidator(
            None, None, None, settings.IContactPlonegroupConfig, None)
        orgs = get_registry_organizations()
        functions = get_registry_functions()
        data = {'organizations': orgs, 'functions': functions}
        # set dep2 as 'fct_orgs' of 'director' function
        director = functions[0]
        director['fct_orgs'] = [dep2.UID()]
        errors = invariants.validate(data)
        self.assertTrue(isinstance(errors[0], Invalid))
        error_msg = translate(
            msgid=u"can_not_select_function_orgs_every_other_plone_groups_not_empty",
            domain='collective.contact.plonegroup',
            mapping={'function': 'director',
                     'plone_group_id': plone_group_id})
        self.assertEqual(translate(errors[0].message), error_msg)
        # remove user from plone group, now it validates
        api.group.remove_user(groupname=plone_group_id, username=TEST_USER_ID)
        self.assertFalse(invariants.validate(data))

    def test_adaptPloneGroupDefinition(self):
        """ Test event when an organization is changed """
        organizations = get_registry_organizations()
        own_orga = get_own_organization()
        # an organization is modified
        own_orga['department1'].title = 'Department 1 changed'
        event.notify(ObjectModifiedEvent(own_orga['department1']))
        d1_d_group = api.group.get(groupname='%s_director' % organizations[0])
        self.assertEquals(d1_d_group.getProperty('title'), 'Department 1 changed (Director)')
        d1s1_d_group = api.group.get(groupname='%s_director' % organizations[1])
        self.assertEquals(d1s1_d_group.getProperty('title'), 'Department 1 changed - Service 1 (Director)')
        # an organization is moved (service1 in department2)
        clipboard = own_orga['department1'].manage_cutObjects(['service1'])
        own_orga['department2'].manage_pasteObjects(clipboard)
        # the event IObjectMovedEvent is triggered
        d1s1_d_group = api.group.get(groupname='%s_director' % organizations[1])
        self.assertEquals(d1s1_d_group.getProperty('title'), 'Department 2 - Service 1 (Director)')
        # a configured organization is deleted. Exception raised
        self.assertRaises(Redirect, own_orga['department2'].manage_delObjects, ids=['service1'])
        # THIS IS A KNOWN ERROR: the organization is deleted despite the exception !!!!!!!
        self.assertFalse('service1' in own_orga['department2'])
        # an unused organization is deleted. No exception
        own_orga['department2'].invokeFactory('organization', 'service3', title='Service 3')
        own_orga['department2'].manage_delObjects(ids=['service3'])
        self.assertFalse('service3' in own_orga['department2'])

    def test_onlyRelevantPloneGroupsCreatedWhenFunctionRestrictedToSelectedOrgs(self):
        """Test using 'fct_orgs' when defining functions."""
        # create a new suffix and restrict it to department1
        own_orga = get_own_organization()
        dep1 = own_orga['department1']
        dep1_uid = dep1.UID()
        dep2 = own_orga['department2']
        dep2_uid = dep2.UID()
        functions = get_registry_functions()
        new_function = {'fct_id': u'new',
                        'fct_title': u'New',
                        'fct_orgs': [dep1_uid],
                        'fct_management': False,
                        'enabled': True}
        functions.append(new_function)
        set_registry_functions(functions)
        # 'new' suffixed Plone group was created only for dep1
        self.assertTrue(api.group.get(get_plone_group_id(dep1_uid, u'new')))
        self.assertFalse(api.group.get(get_plone_group_id(dep2_uid, u'new')))

    def test_selectedOrganizationsPloneGroupsVocabulary(self):
        """ Test plone groups vocabulary """
        groups = settings.selectedOrganizationsPloneGroupsVocabulary()
        voc_dic = groups.by_token
        voc_list = [voc_dic[key].title for key in voc_dic.keys()]
        self.assertEquals(set(voc_list), set(['Department 1 - Service 1 (Director)', 'Department 2 (Worker)',
                                              'Department 1 - Service 1 (Worker)', 'Department 1 (Worker)',
                                              'Department 2 (Director)', 'Department 1 (Director)']))
        groups = settings.selectedOrganizationsPloneGroupsVocabulary(functions=['worker'], group_title=False)
        voc_dic = groups.by_token
        voc_list = [voc_dic[key].title for key in voc_dic.keys()]
        self.assertEquals(set(voc_list), set(['Department 2', 'Department 1', 'Department 1 - Service 1']))

    def test_selectedOrganizationsVocabulary(self):
        """ Test registry vocabulary """
        self.assertListEqual([v.title for v in settings.selectedOrganizationsVocabulary()],
                             ['Department 1', 'Department 1 - Service 1', 'Department 2'])

    def test_SelectedOrganizationsElephantVocabulary(self):
        """ Test elephant vocabulary """
        factory_all = getUtility(
            IVocabularyFactory, 'collective.contact.plonegroup.organization_services')
        vocab_all = factory_all(self.portal)
        vocab_all_values = [v.value for v in vocab_all]
        self.assertEqual(len(vocab_all), 3)
        self.assertListEqual([v.title for v in vocab_all],
                             ['Department 1', 'Department 1 - Service 1', 'Department 2'])
        set_registry_organizations([vocab_all_values[2], vocab_all_values[0]])
        factory_wrp = getUtility(
            IVocabularyFactory,
            'collective.contact.plonegroup.browser.settings.SelectedOrganizationsElephantVocabulary')
        vocab_wrp = factory_wrp(self.portal)
        self.assertEqual(len(vocab_wrp), 3)
        # values are shown as selected in plonegroup organizations
        self.assertListEqual([v.title for v in vocab_wrp], ['Department 2', 'Department 1'])
        self.assertListEqual([v.token for v in vocab_wrp], get_registry_organizations())
        self.assertEqual(vocab_wrp.getTerm(vocab_all_values[1]).title, 'Department 1 - Service 1')
        # vocabulary use caching, when new values added, the vocabulary is correct
        own_orga = get_own_organization()
        own_orga.invokeFactory('organization', 'department3', title='Department 3')
        set_registry_organizations(
            [vocab_all_values[0],
             vocab_all_values[2],
             vocab_all_values[1],
             own_orga['department3'].UID()])
        vocab_wrp = factory_wrp(self.portal)
        self.assertListEqual(
            [v.title for v in vocab_wrp],
            [u'Department 1', u'Department 2', u'Department 1 - Service 1', u'Department 3'])
        self.assertListEqual(
            [v.token for v in vocab_wrp],
            get_registry_organizations())

    def test_SortedSelectedOrganizationsElephantVocabulary(self):
        """ Test sorted elephant vocabulary """
        factory_all = getUtility(
            IVocabularyFactory, 'collective.contact.plonegroup.organization_services')
        vocab_all = factory_all(self.portal)
        vocab_all_values = [v.value for v in vocab_all]
        self.assertEqual(len(vocab_all), 3)
        self.assertListEqual([v.title for v in vocab_all],
                             ['Department 1', 'Department 1 - Service 1', 'Department 2'])
        set_registry_organizations([vocab_all_values[2], vocab_all_values[0]])
        factory_wrp = getUtility(
            IVocabularyFactory,
            'collective.contact.plonegroup.browser.settings.SortedSelectedOrganizationsElephantVocabulary')
        vocab_wrp = factory_wrp(self.portal)
        self.assertEqual(len(vocab_wrp), 3)
        # values are shown sorted, no matter how it is selected in plonegroup organizations
        self.assertListEqual([v.title for v in vocab_wrp], [u'Department 1', u'Department 2'])
        self.assertListEqual(sorted([v.token for v in vocab_wrp]),
                             sorted(get_registry_organizations()))
        self.assertEqual(vocab_wrp.getTerm(vocab_all_values[1]).title, u'Department 1 - Service 1')
        # vocabulary use caching, when new values added, the vocabulary is correct
        own_orga = get_own_organization()
        own_orga.invokeFactory('organization', 'department3', title='Department 3')
        set_registry_organizations(
            [vocab_all_values[2],
             vocab_all_values[0],
             own_orga['department3'].UID()])
        vocab_wrp = factory_wrp(self.portal)
        self.assertListEqual(
            [v.title for v in vocab_wrp],
            [u'Department 1', u'Department 2', u'Department 3'])
        self.assertListEqual(
            sorted([v.token for v in vocab_wrp]),
            sorted(get_registry_organizations()))
