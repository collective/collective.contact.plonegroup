# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from zope.component import getUtility
from plone import api
from plone.registry.interfaces import IRegistry
from collective.contact.plonegroup.testing import IntegrationTestCase


class TestInstall(IntegrationTestCase):
    """Test installation of collective.contact.plonegroup into Plone."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.registry = getUtility(IRegistry)
        self.registry['collective.contact.plonegroup.browser.settings.IContactPlonegroupConfig.'
                      'organizations'] = [{'org_title': u'Work department',
                                           'org_id': u'work'},
                                          {'org_title': u'Citizen department',
                                           'org_id': u'citizen'}]
        self.registry['collective.contact.plonegroup.browser.settings.IContactPlonegroupConfig.'
                      'functions'] = [{'fct_title': u'Director',
                                       'fct_id': u'director'},
                                      {'fct_title': u'Worker',
                                       'fct_id': u'worker'}]

    def test_detectContactPlonegroupChange(self):
        """Test if group creation works correctly"""
        group_ids = [group.id for group in api.group.get_groups()]
        self.assertIn('work_director', group_ids)
        self.assertIn('work_worker', group_ids)
        self.assertIn('citizen_director', group_ids)
        self.assertIn('citizen_worker', group_ids)
        w_d_group = api.group.get(groupname='work_director')
        self.assertTrue(w_d_group.getProperty('title'), 'Work department (Director)')
        # Changing organization title
        self.registry['collective.contact.plonegroup.browser.settings.IContactPlonegroupConfig.'
                      'organizations'] = [{'org_title': u'Work service',
                                           'org_id': u'work'},
                                          {'org_title': u'Citizen department',
                                           'org_id': u'citizen'}]
        self.assertTrue(w_d_group.getProperty('title'), 'Work service (Director)')
        # Changing function title
        self.registry['collective.contact.plonegroup.browser.settings.IContactPlonegroupConfig.'
                      'functions'] = [{'fct_title': u'Directors',
                                       'fct_id': u'director'},
                                      {'fct_title': u'Worker',
                                       'fct_id': u'worker'}]
        self.assertTrue(w_d_group.getProperty('title'), 'Work service (Directors)')
        # Adding new organization
        self.registry['collective.contact.plonegroup.browser.settings.IContactPlonegroupConfig.'
                      'organizations'] = [{'org_title': u'Work service',
                                           'org_id': u'work'},
                                          {'org_title': u'Citizen department',
                                           'org_id': u'citizen'},
                                          {'org_title': u'Informatic department',
                                           'org_id': u'informatic'}]
        # Adding new function
        self.registry['collective.contact.plonegroup.browser.settings.IContactPlonegroupConfig.'
                      'functions'] = [{'fct_title': u'Directors',
                                       'fct_id': u'director'},
                                      {'fct_title': u'Worker',
                                       'fct_id': u'worker'},
                                      {'fct_title': u'Chief',
                                       'fct_id': u'chief'}]
        group_ids = [group.id for group in api.group.get_groups()]
        self.assertIn('informatic_director', group_ids)
        self.assertIn('informatic_worker', group_ids)
        self.assertIn('informatic_chief', group_ids)
        self.assertIn('work_chief', group_ids)
