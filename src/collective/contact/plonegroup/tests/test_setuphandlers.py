# -*- coding: utf-8 -*-
"""setuphandlers.py tests for this package."""

from collective.contact.plonegroup.config import FUNCTIONS_REGISTRY
from collective.contact.plonegroup.config import GROUPS_MGT_REGISTRY
from collective.contact.plonegroup.config import ORGANIZATIONS_REGISTRY
from collective.contact.plonegroup.config import set_registry_functions
from collective.contact.plonegroup.testing import IntegrationTestCase
from plone.registry.interfaces import IRegistry
from zope.component import getUtility


class TestSetuphandlers(IntegrationTestCase):

    def test_postInstall(self):
        registry = getUtility(IRegistry)
        # install initialized organizations and functions to an empty list
        self.assertEqual(registry[ORGANIZATIONS_REGISTRY], [])
        self.assertEqual(registry[FUNCTIONS_REGISTRY], [])
        self.assertIsNone(registry[GROUPS_MGT_REGISTRY])
        # reapplying the step initializes a None value and keeps a stored value
        registry[ORGANIZATIONS_REGISTRY] = None
        functions = [
            {"fct_title": "Director", "fct_id": "director", "fct_orgs": [], "fct_management": False, "enabled": True}
        ]
        set_registry_functions(functions)
        self.portal.portal_setup.runImportStepFromProfile(
            "profile-collective.contact.plonegroup:default", "contact-plonegroup-postInstall"
        )
        self.assertEqual(registry[ORGANIZATIONS_REGISTRY], [])
        self.assertEqual(registry[FUNCTIONS_REGISTRY], functions)
