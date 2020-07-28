# -*- coding: utf-8 -*-
""" utils.py tests for this package."""

from collective.contact.plonegroup.config import DEFAULT_DIRECTORY_ID
from collective.contact.plonegroup.config import get_registry_functions
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.config import set_registry_functions
from collective.contact.plonegroup.config import set_registry_organizations
from collective.contact.plonegroup.testing import IntegrationTestCase
from collective.contact.plonegroup.utils import get_all_suffixes
from collective.contact.plonegroup.utils import get_organization
from collective.contact.plonegroup.utils import get_organizations
from collective.contact.plonegroup.utils import get_own_organization
from collective.contact.plonegroup.utils import get_own_organization_path
from collective.contact.plonegroup.utils import get_plone_group
from collective.contact.plonegroup.utils import get_plone_group_id
from collective.contact.plonegroup.utils import get_plone_groups
from collective.contact.plonegroup.utils import get_selected_org_suffix_users
from collective.contact.plonegroup.utils import organizations_with_suffixes
from collective.contact.plonegroup.utils import select_org_for_function
from collective.contact.plonegroup.utils import select_organization
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
        self.portal.invokeFactory('directory', DEFAULT_DIRECTORY_ID)
        self.portal[DEFAULT_DIRECTORY_ID].invokeFactory('organization', PLONEGROUP_ORG, title='My organization')
        self.own_orga = get_own_organization()
        self.dep1 = api.content.create(
            container=self.own_orga, type='organization', id='department1', title='Department 1')
        self.uid = self.dep1.UID()
        self.dep2 = api.content.create(
            container=self.own_orga, type='organization', id='department2', title='Department 2')
        self.registry = getUtility(IRegistry)
        set_registry_organizations([self.uid])
        set_registry_functions([{'fct_title': u'Observers',
                                 'fct_id': u'observer',
                                 'fct_orgs': [],
                                 'fct_management': False,
                                 'enabled': True},
                                {'fct_title': u'Director',
                                 'fct_id': u'director',
                                 'fct_orgs': [],
                                 'fct_management': False,
                                 'enabled': True}, ])
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
        self.assertListEqual([t.value for t in voc_selected_org_suffix_users(self.uid, [u'director'])],
                             [TEST_USER_NAME, 'user1', 'user2'])
        self.assertListEqual([t.value for t in voc_selected_org_suffix_users(self.uid, [u'director'],
                             first_member=api.user.get(username='user1'))],
                             ['user1', TEST_USER_NAME, 'user2'])
        # well ordered by fullname
        test_user.setMemberProperties({'fullname': 'User Test'})
        self.assertListEqual([t.value for t in voc_selected_org_suffix_users(self.uid, [u'director'])],
                             ['user1', 'user2', TEST_USER_NAME])
        self.assertListEqual([t.value for t in voc_selected_org_suffix_users(self.uid, [u'director'],
                             first_member=api.user.get(username='user1'))],
                             ['user1', 'user2', TEST_USER_NAME])

    def test_get_plone_group_id(self):
        self.assertEqual(get_plone_group_id('groupuid', 'suffix'), 'groupuid_suffix')

    def test_get_plone_group(self):
        self.assertIsNone(get_plone_group('groupuid', 'suffix'))
        self.assertEqual(
            get_plone_group(self.uid, 'observer'),
            api.group.get('{0}_{1}'.format(self.uid, 'observer')))

    def test_get_plone_groups(self):
        plone_groups = [get_plone_group(self.uid, 'observer'), get_plone_group(self.uid, 'director')]
        self.assertEqual(get_plone_groups(self.uid, ids_only=False), plone_groups)
        self.assertEqual(get_plone_groups(self.uid, ids_only=True), [g.id for g in plone_groups])
        self.assertEqual(get_plone_groups(self.uid, suffixes=['observer']), [plone_groups[0]])
        self.assertEqual(get_plone_groups(self.uid, suffixes=['unknown_suffix']), [])
        self.assertEqual(get_plone_groups(self.uid, ids_only=True, suffixes=['unknown_suffix']), [])

    def test_get_organization(self):
        suffixed_org = get_plone_group_id(self.uid, 'suffix')
        # get_organization may receive a plone_group_id or an organization uid
        self.assertEqual(get_organization(suffixed_org), self.dep1)
        self.assertEqual(get_organization(self.uid), self.dep1)

    def test_get_organizations(self):
        # only_selected
        self.assertEqual(get_organizations(only_selected=True), [self.dep1])
        self.assertEqual(get_organizations(only_selected=False), [self.dep1, self.dep2])
        # the_objects
        self.assertEqual(get_organizations(the_objects=True), [self.dep1])
        self.assertEqual(get_organizations(the_objects=False), [self.uid])
        # not_empty_suffix
        self.assertEqual(get_organizations(not_empty_suffix=None), [self.dep1])
        self.assertEqual(get_organizations(not_empty_suffix=u'director'), [self.dep1])
        self.assertEqual(get_organizations(not_empty_suffix=u'observer'), [])

    def test_get_organizations_follows_selected_organizations_order(self):
        self.assertEqual(get_organizations(only_selected=True), [self.dep1])
        select_organization(self.dep2.UID())
        self.assertEqual(get_organizations(only_selected=True, caching=False),
                         [self.dep1, self.dep2])
        select_organization(self.dep1.UID(), remove=True)
        select_organization(self.dep2.UID(), remove=True)
        select_organization(self.dep2.UID())
        select_organization(self.dep1.UID())
        self.assertEqual(get_organizations(only_selected=True, caching=False),
                         [self.dep2, self.dep1])

    def test_get_organizations_kept_org_uids(self):
        self.assertEqual(get_organizations(), [self.dep1])
        self.assertEqual(get_organizations(kept_org_uids=['some_unexisting_uid']), [])
        self.assertEqual(get_organizations(kept_org_uids=[self.dep1.UID()]), [self.dep1])
        self.assertEqual(
            get_organizations(kept_org_uids=['some_unexisting_uid', self.dep1.UID()]),
            [self.dep1])
        # make sure order is preserved
        self.assertEqual(
            get_organizations(only_selected=False,
                              kept_org_uids=[self.dep2.UID(), self.dep1.UID()]),
            [self.dep2, self.dep1])

    def test_get_all_suffixes(self):
        self.assertEqual(get_all_suffixes(self.uid), [u'observer', u'director'])
        dep2_uid = self.dep2.UID()
        self.assertEqual(get_all_suffixes(dep2_uid), [u'observer', u'director'])
        self.assertEqual(get_all_suffixes(), [u'observer', u'director'])

    def test_get_all_suffixes_fct_orgs(self):
        dep2_uid = self.dep2.UID()
        self.assertEqual(get_all_suffixes(dep2_uid), [u'observer', u'director'])
        functions = get_registry_functions()
        functions[0]['fct_orgs'] = [self.uid]
        set_registry_functions(functions)
        self.assertEqual(get_all_suffixes(dep2_uid), [u'director'])

    def test_get_all_suffixes_only_enabled(self):
        dep2_uid = self.dep2.UID()
        self.assertEqual(get_all_suffixes(dep2_uid, only_enabled=True), [u'observer', u'director'])
        functions = get_registry_functions()
        functions[0]['enabled'] = False
        set_registry_functions(functions)
        self.assertEqual(get_all_suffixes(dep2_uid, only_enabled=True), [u'director'])
        self.assertEqual(get_all_suffixes(dep2_uid, only_enabled=False), [u'observer', u'director'])

    def test_get_own_organization_path(self):
        """ Test the returned organization path """
        self.assertEqual(get_own_organization(default=True), self.portal[DEFAULT_DIRECTORY_ID][PLONEGROUP_ORG])
        self.assertEqual(get_own_organization(default=False), self.portal[DEFAULT_DIRECTORY_ID][PLONEGROUP_ORG])
        self.assertEqual(get_own_organization_path(default=True), '/plone/contacts/plonegroup-organization')
        self.assertEqual(get_own_organization_path(default=False), '/plone/contacts/plonegroup-organization')
        # remove own organization
        api.content.delete(self.own_orga)
        self.assertIsNone(get_own_organization(default=True))
        self.assertIsNone(get_own_organization(default=False))
        self.assertIsNone(get_own_organization_path(default=True))
        self.assertIsNone(get_own_organization_path(default=False))
        self.assertEqual(get_own_organization_path(not_found_value='unfound'), 'unfound')

    def test_select_org_for_function(self):
        """ """
        self.assertEqual(get_registry_functions(),
                         [{'fct_title': u'Observers',
                           'fct_orgs': [],
                           'fct_id': u'observer',
                           'fct_management': False,
                           'enabled': True},
                          {'fct_title': u'Director',
                           'fct_orgs': [],
                           'fct_id': u'director',
                           'fct_management': False,
                           'enabled': True}])
        select_org_for_function(self.uid, 'director')
        self.assertTrue(self.uid in get_registry_functions()[1]['fct_orgs'])
        select_org_for_function(self.uid, 'director', remove=True)
        self.assertFalse(self.uid in get_registry_functions()[1]['fct_orgs'])
