# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from collective.contact.plonegroup.testing import IntegrationTestCase
from Products.CMFPlone.utils import get_installer
from Products.GenericSetup.tool import DEPENDENCY_STRATEGY_REAPPLY


class TestInstall(IntegrationTestCase):
    """Test installation of collective.contact.plonegroup into Plone."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = get_installer(self.portal, self.layer['request'])

    def test_product_installed(self):
        """Test if collective.contact.plonegroup is installed with portal_quickinstaller."""
        self.assertTrue(self.installer.is_product_installed('collective.contact.plonegroup'))

    # browserlayer.xml
    def test_browserlayer(self):
        """Test that ICollectiveContactPlonegroupLayer is registered."""
        from collective.contact.plonegroup.interfaces import ICollectiveContactPlonegroupLayer
        from plone.browserlayer import utils
        self.assertTrue(ICollectiveContactPlonegroupLayer in utils.registered_layers())

    def test_reinstall(self):
        """ """
        self.portal.portal_setup.runAllImportStepsFromProfile(
            'collective.contact.plonegroup:default',
            dependency_strategy=DEPENDENCY_STRATEGY_REAPPLY)
