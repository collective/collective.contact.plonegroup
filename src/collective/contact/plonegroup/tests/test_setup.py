# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from collective.contact.plonegroup.testing import IntegrationTestCase
from plone import api
from plone.base.utils import get_installer
from Products.GenericSetup.tool import DEPENDENCY_STRATEGY_REAPPLY


class TestInstall(IntegrationTestCase):
    """Test installation of collective.contact.plonegroup into Plone."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        self.installer = get_installer(self.portal, self.layer["request"])

    def test_product_installed(self):
        """Test if collective.contact.plonegroup is installed."""
        self.assertTrue(self.installer.is_product_installed("collective.contact.plonegroup"))

    def test_uninstall(self):
        """Test if collective.contact.plonegroup is cleanly uninstalled."""
        self.assertIn("own-groups", self.portal.portal_actions.user)
        self.installer.uninstall_product("collective.contact.plonegroup")
        self.assertFalse(self.installer.is_product_installed("collective.contact.plonegroup"))
        self.assertNotIn("own-groups", self.portal.portal_actions.user)
        self.assertIsNone(
            api.portal.get_registry_record("plone.bundles/collective-contact-plonegroup.enabled", default=None)
        )

    # browserlayer.xml
    def test_browserlayer(self):
        """Test that ICollectiveContactPlonegroupLayer is registered."""
        from collective.contact.plonegroup.interfaces import ICollectiveContactPlonegroupLayer
        from plone.browserlayer import utils

        self.assertTrue(ICollectiveContactPlonegroupLayer in utils.registered_layers())

    def test_resources(self):
        """Test that CSS and JS resources are registered and served.
        Plone 6: in a bundle of the resource registry instead of portal_css/portal_javascripts."""
        bundle = "plone.bundles/collective-contact-plonegroup."
        self.assertTrue(api.portal.get_registry_record(bundle + "enabled"))
        self.assertEqual(
            api.portal.get_registry_record(bundle + "csscompilation"),
            "++resource++collective.contact.plonegroup/plonegroup.css",
        )
        self.assertEqual(
            api.portal.get_registry_record(bundle + "jscompilation"),
            "++resource++collective.contact.plonegroup/plonegroup.js",
        )
        for name in ("plonegroup.css", "plonegroup.js"):
            self.assertTrue(self.portal.restrictedTraverse("++resource++collective.contact.plonegroup/" + name))

    def test_reinstall(self):
        """ """
        self.portal.portal_setup.runAllImportStepsFromProfile(
            "collective.contact.plonegroup:default", dependency_strategy=DEPENDENCY_STRATEGY_REAPPLY
        )
