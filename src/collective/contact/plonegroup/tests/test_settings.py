# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from collective.contact.plonegroup.browser import settings
from collective.contact.plonegroup.config import FUNCTIONS_REGISTRY
from collective.contact.plonegroup.config import ORGANIZATIONS_REGISTRY
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.testing import IntegrationTestCase
from plone import api
from plone.registry.interfaces import IRegistry
from zExceptions import Redirect
from zope import event
from zope.component import getUtility
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema.interfaces import IVocabularyFactory


class TestSettings(IntegrationTestCase):
    """Test collective.contact.plonegroup settings."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        # Organizations creation
        self.portal.invokeFactory('directory', 'contacts')
        self.portal['contacts'].invokeFactory('organization', PLONEGROUP_ORG, title='My organization')
        own_orga = self.portal['contacts'][PLONEGROUP_ORG]
        own_orga.invokeFactory('organization', 'department1', title='Department 1')
        own_orga.invokeFactory('organization', 'department2', title='Department 2')
        own_orga['department1'].invokeFactory('organization', 'service1', title='Service 1')
        own_orga.invokeFactory('organization', 'inactive_department', title='Inactive department')
        inactive_department = own_orga['inactive_department']
        api.content.transition(obj=inactive_department, transition='deactivate')

        self.registry = getUtility(IRegistry)
        self.registry['collective.contact.plonegroup.browser.settings.IContactPlonegroupConfig.'
                      'organizations'] = [own_orga['department1'].UID(),
                                          own_orga['department1']['service1'].UID(),
                                          own_orga['department2'].UID()]
        self.registry['collective.contact.plonegroup.browser.settings.IContactPlonegroupConfig.'
                      'functions'] = [{'fct_title': u'Director',
                                       'fct_id': u'director'},
                                      {'fct_title': u'Worker',
                                       'fct_id': u'worker'}]

    def test_OwnOrganizationServicesVocabulary(self):
        """ Test vocabulary """
        services = getUtility(IVocabularyFactory, name=u'collective.contact.plonegroup.organization_services')
        voc_dic = services(self).by_token
        voc_list = [voc_dic[key].title for key in voc_dic.keys()]
        self.assertSetEqual(set(voc_list), set(['Department 1 - Service 1', 'Department 1', 'Department 2']))
        self.assertNotIn('Inactive department', voc_list)
        # When multiple own organizations
        self.portal['contacts'].invokeFactory('organization', 'temporary', title='Temporary')
        self.portal['contacts']['temporary'].invokeFactory('organization', PLONEGROUP_ORG,
                                                           title='Duplicated organization')
        services = getUtility(IVocabularyFactory, name=u'collective.contact.plonegroup.organization_services')
        voc_dic = services(self).by_token
        voc_list = [voc_dic[key].title for key in voc_dic.keys()]
        self.assertEquals(voc_list, [u"You must have only one organization with id '${pgo}' !"])
        self.portal['contacts'].manage_delObjects(ids=['temporary'])
        # When own organization not found
        self.portal['contacts'].manage_delObjects(ids=[PLONEGROUP_ORG])
        services = getUtility(IVocabularyFactory, name=u'collective.contact.plonegroup.organization_services')
        voc_dic = services(self).by_token
        voc_list = [voc_dic[key].title for key in voc_dic.keys()]
        self.assertEquals(voc_list, [u"You must define an organization with id '${pgo}' !"])

    def test_detectContactPlonegroupChange(self):
        """Test if group creation works correctly"""
        group_ids = [group.id for group in api.group.get_groups()]
        organizations = self.registry[ORGANIZATIONS_REGISTRY]
        for uid in organizations:
            self.assertIn('%s_director' % uid, group_ids)
            self.assertIn('%s_worker' % uid, group_ids)
        d1_d_group = api.group.get(groupname='%s_director' % organizations[0])
        self.assertEquals(d1_d_group.getProperty('title'), 'Department 1 (Director)')
        d1s1_d_group = api.group.get(groupname='%s_director' % organizations[1])
        self.assertEquals(d1s1_d_group.getProperty('title'), 'Department 1 - Service 1 (Director)')
        # Changing function title
        self.registry[FUNCTIONS_REGISTRY] = [{'fct_title': u'Directors', 'fct_id': u'director'},
                                             {'fct_title': u'Worker', 'fct_id': u'worker'}]
        d1_d_group = api.group.get(groupname='%s_director' % organizations[0])
        self.assertEquals(d1_d_group.getProperty('title'), 'Department 1 (Directors)')
        d1s1_d_group = api.group.get(groupname='%s_director' % organizations[1])
        self.assertEquals(d1s1_d_group.getProperty('title'), 'Department 1 - Service 1 (Directors)')
        # Adding new organization
        own_orga = self.portal['contacts'][PLONEGROUP_ORG]
        own_orga['department2'].invokeFactory('organization', 'service2', title='Service 2')
        # append() method on the registry doesn't trigger the event. += too
        newValue = self.registry[ORGANIZATIONS_REGISTRY] + [own_orga['department2']['service2'].UID()]
        self.registry[ORGANIZATIONS_REGISTRY] = newValue
        group_ids = [group.id for group in api.group.get_groups()]
        last_uid = self.registry[ORGANIZATIONS_REGISTRY][-1]
        self.assertIn('%s_director' % last_uid, group_ids)
        self.assertIn('%s_worker' % last_uid, group_ids)
        # Adding new function
        newValue = self.registry[FUNCTIONS_REGISTRY] + [{'fct_title': u'Chief', 'fct_id': u'chief'}]
        self.registry[FUNCTIONS_REGISTRY] = newValue
        group_ids = [group.id for group in api.group.get_groups() if '_' in group.id]
        self.assertEquals(len(group_ids), 12)
        for uid in self.registry[ORGANIZATIONS_REGISTRY]:
            self.assertIn('%s_director' % uid, group_ids)
            self.assertIn('%s_chief' % uid, group_ids)
            self.assertIn('%s_worker' % uid, group_ids)

    def test_getOwnOrganizationPath(self):
        """ Test the returned organization path """
        self.assertEquals(settings.getOwnOrganizationPath(), '/plone/contacts/plonegroup-organization')

    def test_adaptPloneGroupDefinition(self):
        """ Test event when an organization is changed """
        organizations = self.registry[ORGANIZATIONS_REGISTRY]
        own_orga = self.portal['contacts'][PLONEGROUP_ORG]
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
        factory_all = getUtility(IVocabularyFactory, 'collective.contact.plonegroup.organization_services')
        vocab_all = factory_all(self.portal)
        vocab_all_values = [v.value for v in vocab_all]
        self.assertEqual(len(vocab_all), 3)
        self.assertListEqual([v.title for v in vocab_all],
                             ['Department 1', 'Department 1 - Service 1', 'Department 2'])
        registry = getUtility(IRegistry)
        registry[ORGANIZATIONS_REGISTRY] = [vocab_all_values[2], vocab_all_values[0]]
        factory_wrp = getUtility(IVocabularyFactory, "collective.contact.plonegroup.selected_organization_services")
        vocab_wrp = factory_wrp(self.portal)
        self.assertEqual(len(vocab_wrp), 3)
        self.assertListEqual([v.value for v in vocab_wrp], registry[ORGANIZATIONS_REGISTRY])
        self.assertListEqual([v.title for v in vocab_wrp], ['Department 2', 'Department 1'])
        self.assertEqual(vocab_wrp.getTerm(vocab_all_values[1]).title, 'Department 1 - Service 1')
