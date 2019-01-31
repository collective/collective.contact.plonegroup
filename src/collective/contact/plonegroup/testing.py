# -*- coding: utf-8 -*-
"""Base module for unittesting."""
import collective.contact.plonegroup

import pkg_resources
import unittest2 as unittest
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import applyProfile
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.testing import z2

try:
    pkg_resources.get_distribution('plone.app.contenttypes')
except pkg_resources.DistributionNotFound:
    HAS_PA_CONTENTTYPES = False
else:
    HAS_PA_CONTENTTYPES = True


class CollectiveContactPlonegroupLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        """Set up Zope."""
        # Load ZCML
        self.loadZCML(package=collective.contact.plonegroup,
                      name='testing.zcml')
        z2.installProduct(app, 'collective.contact.plonegroup')

    def setUpPloneSite(self, portal):
        """Set up Plone."""
        # Install into Plone site using portal_setup

        # Plone 5 support
        if HAS_PA_CONTENTTYPES:
            self.applyProfile(portal, 'plone.app.contenttypes:default')

        applyProfile(portal, 'collective.contact.plonegroup:testing')

        # Login and create some test content
        setRoles(portal, TEST_USER_ID, ['Manager'])
        login(portal, TEST_USER_NAME)
        portal.invokeFactory('Folder', 'folder')

        # Commit so that the test browser sees these objects
        portal.portal_catalog.clearFindAndRebuild()
        import transaction
        transaction.commit()

    def tearDownZope(self, app):
        """Tear down Zope."""
        z2.uninstallProduct(app, 'collective.contact.plonegroup')


FIXTURE = CollectiveContactPlonegroupLayer(
    name="FIXTURE"
)

INTEGRATION = IntegrationTesting(
    bases=(FIXTURE,),
    name="INTEGRATION"
)

FUNCTIONAL = FunctionalTesting(
    bases=(FIXTURE,),
    name="FUNCTIONAL"
)


class IntegrationTestCase(unittest.TestCase):
    """Base class for integration tests."""

    layer = INTEGRATION

    def setUp(self):
        super(IntegrationTestCase, self).setUp()
        self.portal = self.layer['portal']


class FunctionalTestCase(unittest.TestCase):
    """Base class for functional tests."""

    layer = FUNCTIONAL
