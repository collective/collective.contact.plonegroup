# -*- coding: utf-8 -*-
"""Base module for unittesting."""

from collective.contact.plonegroup.browser.settings import IContactPlonegroupConfig
from collective.contact.plonegroup.browser.settings import IFunctionSchema
from collective.contact.plonegroup.config import DEFAULT_DIRECTORY_ID
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.config import set_registry_functions
from collective.contact.plonegroup.config import set_registry_groups_mgt
from collective.contact.plonegroup.config import set_registry_organizations
from collective.contact.plonegroup.utils import get_plone_group_id
from collective.z3cform.datagridfield.registry import DictRow
from plone import api
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import login
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.testing import zope
from plone.testing.zope import WSGI_SERVER_FIXTURE
from zope.globalrequest import setLocal

import collective.contact.plonegroup
import collective.eeafaceted.z3ctable
import unittest


class CollectiveContactPlonegroupLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        """Set up Zope."""
        # Load ZCML
        self.loadZCML(package=collective.contact.plonegroup, name="testing.zcml")
        zope.installProduct(app, "collective.contact.plonegroup")

    def setUpPloneSite(self, portal):
        """Set up Plone."""
        # necessary for collective.fingerpointing used
        # when installing "collective.documentgenerator:demo"
        setLocal("request", portal.REQUEST)

        # Install into Plone site using portal_setup
        applyProfile(portal, "collective.contact.plonegroup:testing")

        # Login and create some test content
        setRoles(portal, TEST_USER_ID, ["Manager"])
        login(portal, TEST_USER_NAME)
        portal.invokeFactory("Folder", "folder")

        # Commit so that the test browser sees these objects
        portal.portal_catalog.clearFindAndRebuild()
        import transaction

        transaction.commit()
        # plone.dexterity caches FTIs on the request: a leaked one breaks the layers stacked on this one
        setLocal("request", None)

    def tearDownZope(self, app):
        """Tear down Zope."""
        zope.uninstallProduct(app, "collective.contact.plonegroup")


FIXTURE = CollectiveContactPlonegroupLayer(name="FIXTURE")

INTEGRATION = IntegrationTesting(bases=(FIXTURE,), name="INTEGRATION")

FUNCTIONAL = FunctionalTesting(bases=(FIXTURE,), name="FUNCTIONAL")


class IntegrationTestCase(unittest.TestCase):
    """Base class for integration tests."""

    layer = INTEGRATION

    def setUp(self):
        super(IntegrationTestCase, self).setUp()
        self.portal = self.layer["portal"]


class FunctionalTestCase(unittest.TestCase):
    """Base class for functional tests."""

    layer = FUNCTIONAL


class AcceptanceLayer(PloneSandboxLayer):
    """Robot data: own organization with 2 departments (department1 selected), a manageable 'director' function,
    a manageable 'investigators' global group, Members chef (in both groups) and agent, a content using department2."""

    defaultBases = (FIXTURE,)

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=collective.eeafaceted.z3ctable)  # translations of the tables

    def setUpPloneSite(self, portal):
        # the persistent DictRow of the settings schema was stored by FIXTURE: its connection is closed now
        IContactPlonegroupConfig["functions"].value_type = DictRow(title="Function", schema=IFunctionSchema)
        setLocal("request", portal.REQUEST)  # collective.fingerpointing
        setRoles(portal, TEST_USER_ID, ["Manager"])
        login(portal, TEST_USER_NAME)
        directory = api.content.create(
            portal,
            "directory",
            DEFAULT_DIRECTORY_ID,
            title="Contacts",
            organization_types=[],
            organization_levels=[],
            position_types=[],
        )
        own_orga = api.content.create(directory, "organization", PLONEGROUP_ORG, title="My organization")
        dep1 = api.content.create(own_orga, "organization", "department1", title="Department 1")
        dep2 = api.content.create(own_orga, "organization", "department2", title="Department 2")
        api.content.create(portal, "acontent", "acontent", title="Content of department 2", pg_organization=dep2.UID())
        api.user.create(
            email="chef@example.com", username="chef", password="chefpassword", properties={"fullname": "Chef Boss"}
        )
        api.user.create(
            email="agent@example.com",
            username="agent",
            password="agentpassword",
            properties={"fullname": "Agent Smith"},
        )
        api.group.create("investigators", "Investigators")
        set_registry_organizations([dep1.UID()])
        set_registry_functions(
            [
                {
                    "fct_id": "director",
                    "fct_title": "Director",
                    "fct_orgs": [dep1.UID()],
                    "fct_management": True,
                    "enabled": True,
                }
            ]
        )
        set_registry_groups_mgt(["investigators"])
        api.group.add_user(groupname="investigators", username="chef")
        api.group.add_user(groupname=get_plone_group_id(dep1.UID(), "director"), username="chef")
        setLocal("request", None)


ACCEPTANCE_FIXTURE = AcceptanceLayer(name="ACCEPTANCE_FIXTURE")

ACCEPTANCE = FunctionalTesting(
    bases=(ACCEPTANCE_FIXTURE, REMOTE_LIBRARY_BUNDLE_FIXTURE, WSGI_SERVER_FIXTURE), name="ACCEPTANCE"
)
