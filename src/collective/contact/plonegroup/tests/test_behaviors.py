# -*- coding: utf-8 -*-
"""Module tests for this package."""
from collective.contact.plonegroup.behaviors import filter_user_organizations
from collective.contact.plonegroup.config import DEFAULT_DIRECTORY_ID
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.config import set_registry_functions
from collective.contact.plonegroup.config import set_registry_organizations
from collective.contact.plonegroup.testing import IntegrationTestCase
from collective.contact.plonegroup.utils import get_own_organization
from plone import api
from plone.app.testing import TEST_USER_ID
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory


class TestBehaviors(IntegrationTestCase):
    """Test collective.contact.plonegroup behaviors module."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        # Organizations creation
        self.portal.invokeFactory('directory', DEFAULT_DIRECTORY_ID)
        self.directory = self.portal[DEFAULT_DIRECTORY_ID]
        self.directory.invokeFactory('organization', 'department3', title='Department 3')
        self.directory.invokeFactory('organization', PLONEGROUP_ORG, title='My organization')
        self.own_orga = get_own_organization()
        self.own_orga.invokeFactory('organization', 'department1', title='Department 1')
        self.own_orga.invokeFactory('organization', 'department2', title='Department 2')
        set_registry_organizations([self.own_orga['department1'].UID(),
                                   self.own_orga['department2'].UID()])
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

    def test_filter_user_organizations(self):
        """ Test slave filter method """
        self.assertEqual(len(filter_user_organizations(None)._terms), 0)
        self.assertEqual(len(filter_user_organizations('')._terms), 0)
        self.assertEqual(len(filter_user_organizations('unknown')._terms), 0)
        self.assertEqual(len(filter_user_organizations(TEST_USER_ID)._terms), 0)
        # groups
        api.group.add_user(groupname='{}_director'.format(self.own_orga['department1'].UID()), username=TEST_USER_ID)
        api.group.add_user(groupname='{}_worker'.format(self.own_orga['department2'].UID()), username=TEST_USER_ID)
        self.assertEqual(len(filter_user_organizations(TEST_USER_ID)._terms), 2)

    def test_PrimaryOrganizationsVocabulary(self):
        """ Test vocabulary """
        voc = getUtility(IVocabularyFactory, name=u'collective.contact.plonegroup.primary_organizations')
        # no userid
        self.assertEqual(len(voc(self)._terms), 0)
        self.assertEqual(len(voc(self, userid='unknown')._terms), 0)
        # no groups
        self.assertEqual(len(voc(self, userid=TEST_USER_ID)._terms), 0)
        # user groups
        api.group.add_user(groupname='{}_director'.format(self.own_orga['department1'].UID()), username=TEST_USER_ID)
        api.group.add_user(groupname='{}_worker'.format(self.own_orga['department2'].UID()), username=TEST_USER_ID)
        self.assertIsNone(api.group.get('{}_director'.format(self.directory['department3'].UID())))
        api.group.create(groupname='{}_director'.format(self.directory['department3'].UID()))
        api.group.add_user(groupname='{}_director'.format(self.directory['department3'].UID()), username=TEST_USER_ID)
        voc_dic = voc(self, userid=TEST_USER_ID).by_token
        self.assertSetEqual(set([voc_dic[key].title for key in voc_dic.keys()]), {'Department 1', 'Department 2'})
        # not all suffixes
        voc_dic = voc(self, userid=TEST_USER_ID, suffixes=['director']).by_token
        self.assertSetEqual(set([voc_dic[key].title for key in voc_dic.keys()]), {'Department 1'})
        voc_dic = voc(self, userid=TEST_USER_ID, suffixes=['worker']).by_token
        self.assertSetEqual(set([voc_dic[key].title for key in voc_dic.keys()]), {'Department 2'})
        # other base vocabulary
        voc_dic = voc(self, userid=TEST_USER_ID, suffixes=['director'],
                      base_voc='collective.contact.plonegroup.every_organizations').by_token
        self.assertSetEqual(set([voc_dic[key].title for key in voc_dic.keys()]),
                            {'Department 3', u'My organization - Department 1'})
        # other base vocabulary and all suffixes
        voc_dic = voc(self, userid=TEST_USER_ID, base_voc='collective.contact.plonegroup.every_organizations').by_token
        self.assertSetEqual(set([voc_dic[key].title for key in voc_dic.keys()]),
                            {'Department 3', u'My organization - Department 1', u'My organization - Department 2'})
