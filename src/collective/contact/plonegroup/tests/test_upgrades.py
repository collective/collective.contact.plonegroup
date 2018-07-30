# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.interfaces import INotPloneGroupContact
from collective.contact.plonegroup.interfaces import IPloneGroupContact
from collective.contact.plonegroup.testing import IntegrationTestCase
from collective.contact.plonegroup.upgrades.upgrades import v2
from zope.interface import noLongerProvides


class TestUpgrades(IntegrationTestCase):
    """ Test upgrades of collective.contact.plonegroup. """

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        # Organizations creation
        self.portal.invokeFactory('directory', 'contacts')
        self.portal['contacts'].invokeFactory('organization', PLONEGROUP_ORG, title='My organization')
        self.portal['contacts'][PLONEGROUP_ORG].invokeFactory('organization', 'department1', title='Department 1')
        self.portal['contacts'].invokeFactory('organization', 'other', title='External organization')

    def test_v2(self):
        """Test if collective.contact.plonegroup is installed with portal_quickinstaller."""
        noLongerProvides(self.portal['contacts'][PLONEGROUP_ORG]['department1'], IPloneGroupContact)
        noLongerProvides(self.portal['contacts']['other'], INotPloneGroupContact)
        v2(self.portal)
