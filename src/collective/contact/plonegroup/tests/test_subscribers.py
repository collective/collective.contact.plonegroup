# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from zope.component import getUtility

from plone.app.linkintegrity.interfaces import ILinkIntegrityInfo
from plone.app.linkintegrity.exceptions import LinkIntegrityNotificationException
from plone.registry.interfaces import IRegistry

from collective.contact.plonegroup.testing import IntegrationTestCase

from ..config import ORGANIZATIONS_REGISTRY, FUNCTIONS_REGISTRY, PLONEGROUP_ORG


class TestSubscribers(IntegrationTestCase):
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
        self.contacts = [own_orga['department1'], own_orga['department2']]

        self.registry = getUtility(IRegistry)
        self.registry[ORGANIZATIONS_REGISTRY] = [c.UID() for c in self.contacts]
        self.registry[FUNCTIONS_REGISTRY] = [{'fct_title': u'Director', 'fct_id': u'director'}]

        self.portal.invokeFactory('acontent', 'acontent1', title='Content 1', pg_organization=self.contacts[0].UID())
        self.portal.invokeFactory('acontent', 'acontent2', title='Content 2', pg_organization=self.contacts[1].UID())

    def test_plonegroupOrganizationRemoved_1(self):
        """ We cannot remove an organization selected in settings and used in an object """
        view = self.portal.restrictedTraverse('contacts/%s/department1/delete_confirmation' % PLONEGROUP_ORG)
        self.assertRaises(LinkIntegrityNotificationException, view.render)
        storage = ILinkIntegrityInfo(view.REQUEST)
        breaches = storage.getIntegrityBreaches()
        self.assertIn(self.contacts[0], breaches)
        self.assertSetEqual(breaches[self.contacts[0]], set([self.portal['acontent1']]))

    def test_plonegroupOrganizationRemoved_2(self):
        """ We cannot remove an organization no more selected in settings and used in an object """
        self.registry[ORGANIZATIONS_REGISTRY] = [self.contacts[1].UID()]
        view = self.portal.restrictedTraverse('contacts/%s/department2/delete_confirmation' % PLONEGROUP_ORG)
        self.assertRaises(LinkIntegrityNotificationException, view.render)
        storage = ILinkIntegrityInfo(view.REQUEST)
        breaches = storage.getIntegrityBreaches()
        self.assertIn(self.contacts[1], breaches)
        self.assertSetEqual(breaches[self.contacts[1]], set([self.portal['acontent2']]))

    def test_plonegroupOrganizationRemoved_3(self):
        """ We can remove an organization no more selected in settings and no more used in an object """
        self.registry[ORGANIZATIONS_REGISTRY] = [self.contacts[1].UID()]
        self.portal['acontent2'].pg_organization = None
        self.portal.restrictedTraverse('contacts/%s/department2/delete_confirmation' % PLONEGROUP_ORG)

