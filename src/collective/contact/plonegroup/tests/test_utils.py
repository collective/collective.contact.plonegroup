# -*- coding: utf-8 -*-
""" utils.py tests for this package."""

from collective.contact.plonegroup.config import FUNCTIONS_REGISTRY
from collective.contact.plonegroup.config import ORGANIZATIONS_REGISTRY
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.testing import IntegrationTestCase
from collective.contact.plonegroup.utils import get_selected_org_suffix_users
from collective.contact.plonegroup.utils import organizations_with_suffixes
from collective.contact.plonegroup.utils import voc_selected_org_suffix_users
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.registry.interfaces import IRegistry
from zope.component import getUtility


class TestUtils(IntegrationTestCase):

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        # Organizations creation
        self.portal.invokeFactory('directory', 'contacts')
        self.portal['contacts'].invokeFactory('organization', PLONEGROUP_ORG, title='My organization')
        own_orga = self.portal['contacts'][PLONEGROUP_ORG]
        own_orga.invokeFactory('organization', 'department1', title='Department 1')
        self.uid = own_orga['department1'].UID()
        self.registry = getUtility(IRegistry)
        self.registry[ORGANIZATIONS_REGISTRY] = [self.uid]
        self.registry[FUNCTIONS_REGISTRY] = [{'fct_title': u'Director', 'fct_id': u'director'}]
        api.group.add_user(groupname='%s_director' % self.uid, username=TEST_USER_ID)

    def test_organizations_with_suffixes(self):
        class Dum(object):
            def __init__(self, id):
                self.id = id
        ret = organizations_with_suffixes([], [])
        self.assertListEqual(ret, [])
        ret = organizations_with_suffixes([Dum('a'), Dum('b_1'), Dum('c_1'), Dum('c_2'), Dum('d_2'), Dum('e_3')],
                                          ['1', '3'])
        self.assertListEqual(ret, ['b', 'c', 'e'])
        ret = organizations_with_suffixes([Dum('a'), Dum('b_1_1'), Dum('c_1_1')], ['1_1'])
        self.assertListEqual(ret, ['b', 'c'])

    def test_get_selected_org_suffix_users(self):
        self.assertListEqual(get_selected_org_suffix_users(self.uid, []), [])
        self.assertListEqual([u.getUserName() for u in get_selected_org_suffix_users(self.uid, ['director'])],
                             [api.user.get(username=TEST_USER_ID).getUserName()])

    def test_voc_selected_org_suffix_users(self):
        self.assertEqual(voc_selected_org_suffix_users(None, []).by_token, {})
        self.assertEqual(voc_selected_org_suffix_users(u'--NOVALUE--', []).by_token, {})
        self.assertEqual(voc_selected_org_suffix_users(self.uid, []).by_token, {})
        test_user = api.user.get(username=TEST_USER_NAME)
        test_user.setMemberProperties({'fullname': 'Test User'})
        self.assertEqual(test_user.getProperty('fullname'), 'Test User')
        self.assertListEqual([t.value for t in voc_selected_org_suffix_users(self.uid, ['director'])], [TEST_USER_NAME])
        api.user.create(username='user1', email='t@t.be', properties={'fullname': 'User A'})
        api.user.create(username='user2', email='t@t.be', properties={'fullname': 'User B'})
        api.group.add_user(groupname='%s_director' % self.uid, username='user1')
        api.group.add_user(groupname='%s_director' % self.uid, username='user2')
        self.assertListEqual([t.value for t in voc_selected_org_suffix_users(self.uid, ['director'])],
                             [TEST_USER_NAME, 'user1', 'user2'])
        self.assertListEqual([t.value for t in voc_selected_org_suffix_users(self.uid, ['director'],
                             first_member=api.user.get(username='user1'))],
                             ['user1', TEST_USER_NAME, 'user2'])
        # well ordered by fullname
        test_user.setMemberProperties({'fullname': 'User Test'})
        self.assertListEqual([t.value for t in voc_selected_org_suffix_users(self.uid, ['director'])],
                             ['user1', 'user2', TEST_USER_NAME])
        self.assertListEqual([t.value for t in voc_selected_org_suffix_users(self.uid, ['director'],
                             first_member=api.user.get(username='user1'))],
                             ['user1', 'user2', TEST_USER_NAME])
