# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from collective.contact.plonegroup.config import DEFAULT_DIRECTORY_ID
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.config import set_registry_functions
from collective.contact.plonegroup.config import set_registry_organizations
from collective.contact.plonegroup.interfaces import INotPloneGroupContact
from collective.contact.plonegroup.interfaces import IPloneGroupContact
from collective.contact.plonegroup.subscribers import group_deleted
from collective.contact.plonegroup.testing import IntegrationTestCase
from collective.contact.plonegroup.utils import get_own_organization
from plone import api
from plone.app.linkintegrity.exceptions import LinkIntegrityNotificationException
from plone.app.linkintegrity.interfaces import ILinkIntegrityInfo
from Products.statusmessages.interfaces import IStatusMessage
from zExceptions import Redirect


class TestSubscribers(IntegrationTestCase):
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
        self.contacts = [own_orga['department1'], own_orga['department2']]

        set_registry_organizations([c.UID() for c in self.contacts])
        set_registry_functions([{'fct_title': u'Director',
                                 'fct_id': u'director',
                                 'fct_orgs': [],
                                 'fct_management': False,
                                 'enabled': True}])

        self.portal.invokeFactory('acontent',
                                  'acontent1',
                                  title='Content 1',
                                  pg_organization=self.contacts[0].UID())
        self.portal.invokeFactory('acontent',
                                  'acontent2',
                                  title='Content 2',
                                  pg_organization=self.contacts[1].UID())

    def test_plonegroupOrganizationRemoved_1(self):
        """ We cannot remove an organization selected in settings and used in an object """
        view = self.portal.restrictedTraverse(
            '{0}/{1}/department1/delete_confirmation'.format(DEFAULT_DIRECTORY_ID, PLONEGROUP_ORG))
        self.assertRaises(LinkIntegrityNotificationException, view.render)
        storage = ILinkIntegrityInfo(view.REQUEST)
        breaches = storage.getIntegrityBreaches()
        self.assertIn(self.contacts[0], breaches)
        self.assertSetEqual(breaches[self.contacts[0]], set([self.portal['acontent1']]))

    def test_plonegroupOrganizationRemoved_2(self):
        """ We cannot remove an organization no more selected in settings and used in an object """
        set_registry_organizations([self.contacts[0].UID()])  # unselects the contact
        view = self.portal.restrictedTraverse(
            '{0}/{1}/department2/delete_confirmation'.format(DEFAULT_DIRECTORY_ID, PLONEGROUP_ORG))
        self.assertRaises(LinkIntegrityNotificationException, view.render)
        storage = ILinkIntegrityInfo(view.REQUEST)
        breaches = storage.getIntegrityBreaches()
        self.assertIn(self.contacts[1], breaches)
        self.assertSetEqual(breaches[self.contacts[1]], set([self.portal['acontent2']]))

    def test_plonegroupOrganizationRemoved_3(self):
        """ We can remove an organization no more selected in settings and no more used in an object """
        set_registry_organizations([self.contacts[0].UID()])  # unselects the contact
        self.portal['acontent2'].pg_organization = None
        self.portal.restrictedTraverse(
            '{0}/{1}/department2/delete_confirmation'.format(DEFAULT_DIRECTORY_ID, PLONEGROUP_ORG))

    def test_plonegroupOrganizationRemoved_4(self):
        """ We cannot remove an organization selected in settings and used in an object as dict or list """
        # set uid in dict
        self.portal['acontent1'].pg_organization = {'uid': self.contacts[0].UID()}
        view = self.portal.restrictedTraverse(
            '{0}/{1}/department1/delete_confirmation'.format(DEFAULT_DIRECTORY_ID, PLONEGROUP_ORG))
        self.assertRaises(LinkIntegrityNotificationException, view.render)
        storage = ILinkIntegrityInfo(view.REQUEST)
        breaches = storage.getIntegrityBreaches()
        self.assertIn(self.contacts[0], breaches)
        self.assertSetEqual(breaches[self.contacts[0]], set([self.portal['acontent1']]))
        # set uid in list
        self.portal['acontent2'].pg_organization = [self.contacts[1].UID()]
        view = self.portal.restrictedTraverse(
            '{0}/{1}/department2/delete_confirmation'.format(DEFAULT_DIRECTORY_ID, PLONEGROUP_ORG))
        self.assertRaises(LinkIntegrityNotificationException, view.render)
        storage = ILinkIntegrityInfo(view.REQUEST)
        breaches = storage.getIntegrityBreaches()
        self.assertIn(self.contacts[1], breaches)
        self.assertSetEqual(breaches[self.contacts[1]], set([self.portal['acontent2']]))

    def test_plonegroup_contact_transition_1(self):
        """ We cannot deactivate an organization selected in settings """
        self.assertRaises(Redirect, api.content.transition, obj=self.contacts[0], transition='deactivate')
        self.assertEqual(api.content.get_state(obj=self.contacts[0]), 'active')

    def test_plonegroup_contact_transition_2(self):
        """ We cannot deactivate an organization used in objects """
        set_registry_organizations([self.contacts[1].UID()])  # unselects the contact
        self.assertRaises(Redirect, api.content.transition, obj=self.contacts[0], transition='deactivate')
        self.assertEqual(api.content.get_state(obj=self.contacts[0]), 'active')

    def test_plonegroup_contact_transition_3(self):
        """ We can deactivate an organization not at all used """
        set_registry_organizations([self.contacts[1].UID()])  # unselects the contact
        self.portal['acontent1'].pg_organization = None
        api.content.transition(obj=self.contacts[0], transition='deactivate')
        self.assertEqual(api.content.get_state(obj=self.contacts[0]), 'deactivated')

    def test_mark_organization(self):
        """ We test marker interfaces """
        contacts = self.portal.get(DEFAULT_DIRECTORY_ID)
        pg_org = contacts[PLONEGROUP_ORG]
        self.assertTrue(IPloneGroupContact.providedBy(self.contacts[0]))
        self.assertFalse(INotPloneGroupContact.providedBy(self.contacts[0]))
        self.assertTrue(IPloneGroupContact.providedBy(self.contacts[1]))
        self.assertFalse(INotPloneGroupContact.providedBy(self.contacts[1]))

        normal = api.content.create(
            type='organization', id='normal', container=contacts)
        self.assertTrue(INotPloneGroupContact.providedBy(normal))
        self.assertFalse(IPloneGroupContact.providedBy(normal))

        api.content.move(source=contacts['normal'], target=pg_org)
        self.assertTrue(IPloneGroupContact.providedBy(pg_org['normal']))
        self.assertFalse(INotPloneGroupContact.providedBy(pg_org['normal']))

        api.content.move(source=pg_org['department1'], target=contacts)
        self.assertTrue(INotPloneGroupContact.providedBy(contacts['department1']))
        self.assertFalse(IPloneGroupContact.providedBy(contacts['department1']))

    def test_group_deleted(self):
        class Dummy(object):
            def __init__(self, name):
                self.principal = name
        self.assertIsNone(group_deleted(Dummy('no-underscore')))
        request = self.portal.REQUEST
        smi = IStatusMessage(request)
        uid = self.contacts[0].UID()
        self.assertRaises(Redirect, api.group.delete, groupname='%s_director' % uid)
        msgs = smi.show()
        self.assertEqual(msgs[0].message, u"You cannot delete the group '%s_director', "
                         "linked to used organization 'Department 1'." % uid)
        api.group.create(groupname='%s_other' % uid)
        api.group.create(groupname='12345_director')
        api.group.delete(groupname='%s_other' % uid)
        api.group.delete(groupname='12345_director')
