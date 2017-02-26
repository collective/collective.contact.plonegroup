# -*- coding: utf-8 -*-
""" utils.py tests for this package."""

from zope.component import getUtility
from plone import api
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME
from plone.registry.interfaces import IRegistry

from ..testing import IntegrationTestCase
from ..utils import organizations_with_suffixes, get_selected_org_suffix_users, voc_selected_org_suffix_users
from ..config import PLONEGROUP_ORG, FUNCTIONS_REGISTRY, ORGANIZATIONS_REGISTRY


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
        self.assertListEqual([t.value for t in voc_selected_org_suffix_users(self.uid, ['director'])], [TEST_USER_NAME])
        api.user.create(username='user1', email='t@t.be')
        api.group.add_user(groupname='%s_director' % self.uid, username='user1')
        self.assertListEqual([t.value for t in voc_selected_org_suffix_users(self.uid, ['director'])],
                             [TEST_USER_NAME, 'user1'])
        self.assertListEqual([t.value for t in voc_selected_org_suffix_users(self.uid, ['director'],
                                                                             first_member=api.user.get(username='user1'))],
                             ['user1', TEST_USER_NAME])
