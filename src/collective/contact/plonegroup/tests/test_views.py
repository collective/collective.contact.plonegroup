# -*- coding: utf-8 -*-
""" utils.py tests for this package."""

from collective.contact.plonegroup.config import DEFAULT_DIRECTORY_ID
from collective.contact.plonegroup.config import get_registry_functions
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.config import set_registry_functions
from collective.contact.plonegroup.config import set_registry_groups_mgt
from collective.contact.plonegroup.config import set_registry_organizations
from collective.contact.plonegroup.testing import IntegrationTestCase
from collective.contact.plonegroup.utils import get_own_organization
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.registry.interfaces import IRegistry
from zExceptions import Redirect
from zope.component import getUtility


class TestViews(IntegrationTestCase):

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
        # users and groups
        api.user.create(u'dxm@miami.pol', u'dexter', properties={'fullname': u'Dexter Morgan'})
        api.user.create(u'dbm@miami.pol', u'debra', properties={'fullname': u'Debra Morgan'})
        self.inv_group = api.group.create(u'investigators', u'Investigators')
        self.tech_group = api.group.create(u'technicians', u'Technicians')
        # settings
        self.registry = getUtility(IRegistry)
        set_registry_organizations([self.uid])
        set_registry_functions([{'fct_title': u'Observers', 'fct_id': u'observer', 'fct_orgs': [],
                                 'fct_management': False, 'enabled': True},
                                {'fct_title': u'Director', 'fct_id': u'director', 'fct_orgs': [],
                                 'fct_management': False, 'enabled': True}, ])

    def test_management_view(self):
        view = self.portal.unrestrictedTraverse('@@manage-own-groups-users')
        # No groups activated
        self.assertListEqual(view.get_manageable_groups(), [])
        self.assertListEqual(view.get_manageable_functions(), [])

        # we activate groups and functions
        functions = get_registry_functions(as_copy=False)
        functions[0]['fct_management'] = True
        set_registry_groups_mgt(['investigators'])
        view.init()
        self.assertListEqual(view.get_manageable_groups(), ['investigators'])
        self.assertListEqual(view.get_manageable_functions(), [u'observer'])
        view.get_user_manageable_groups()  # fill in view.groupids
        view.get_user_manageable_functions()  # fill in view.functions_orgs
        self.assertDictEqual(view.groupids, {})
        self.assertDictEqual(view.functions_orgs, {})

        # we add the current user to the activated groups, so he can manage it
        api.group.add_user(groupname='investigators', username=TEST_USER_ID)
        api.group.add_user(groupname='{}_observer'.format(self.uid), username=TEST_USER_ID)

        def get_user_groups(userid):
            return [g.id for g in api.group.get_groups(username=userid) if g.id not in ['AuthenticatedUsers']]

        self.assertListEqual(get_user_groups(TEST_USER_ID), ['{}_observer'.format(self.uid), u'investigators'])
        view = self.portal.unrestrictedTraverse('@@manage-own-groups-users')
        view.init()
        self.assertListEqual(view.get_manageable_groups(), ['investigators'])
        self.assertListEqual(view.get_manageable_functions(), [u'observer'])
        view.get_user_manageable_groups()  # fill in view.groupids
        view.get_user_manageable_functions()  # fill in view.functions_orgs
        self.assertDictEqual(view.groupids, {u'investigators': u'Investigators'})
        self.assertDictEqual(view.functions_orgs, {'observer': [self.dep1]})

        # we check the values given to the fields
        view.update()
        self.assertListEqual(view.fieldnames, ['_groups_', 'observer', '_old_values_'])
        content = view.getContent()
        self.assertListEqual(content._groups_, [{'group': u'investigators', 'user': 'test_user_1_'}])
        self.assertListEqual(content.observer, [{'group': self.uid, 'user': 'test_user_1_'}])
        old_values = ("{{'_groups_': [{{'group': u'investigators', 'user': 'test_user_1_'}}], 'observer': "
                      "[{{'group': '{}', 'user': 'test_user_1_'}}]}}".format(self.uid))
        self.assertEqual(content._old_values_, old_values)

        # applying form : we add users
        self.assertListEqual(get_user_groups('dexter'), [])
        self.assertListEqual(get_user_groups('debra'), [])
        data = {'_groups_': content._groups_ + [{'group': u'investigators', 'user': 'debra'}],
                'observer': content.observer + [{'group': self.uid, 'user': 'dexter'}],
                '_old_values_': old_values}
        view.widgets.extract = lambda *a, **kw: (data, [])
        view.handleApply(view, 'apply')
        self.assertListEqual(get_user_groups('dexter'), ['{}_observer'.format(self.uid)])
        self.assertListEqual(get_user_groups('debra'), [u'investigators'])
        # we add/remove users
        data = {'_groups_': [dic for dic in content._groups_ if dic['user'] != 'debra'] +
                            [{'group': u'investigators', 'user': 'dexter'}],
                'observer': [dic for dic in content.observer if dic['user'] != 'dexter'] +
                            [{'group': self.uid, 'user': 'debra'}],
                '_old_values_': content._old_values_}
        view.widgets.extract = lambda *a, **kw: (data, [])
        view.handleApply(view, 'apply')
        self.assertListEqual(get_user_groups('dexter'), [u'investigators'])
        self.assertListEqual(get_user_groups('debra'), ['{}_observer'.format(self.uid)])

        # we cannot remove current user
        data = {'_groups_': [dic for dic in content._groups_ if dic['user'] == ''],
                'observer': [dic for dic in content.observer if dic['user'] == ''],
                '_old_values_': content._old_values_}
        view.widgets.extract = lambda *a, **kw: (data, [])
        self.assertRaises(Redirect, view.handleApply, view, 'apply')

        # we cannot handle incomplete data
        data = {'_groups_': content._groups_ + [{'group': u'investigators', 'user': None}],
                'observer': content.observer,
                '_old_values_': content._old_values_}
        view.widgets.extract = lambda *a, **kw: (data, [])
        self.assertRaises(Redirect, view.handleApply, view, 'apply')
