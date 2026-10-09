# -*- coding: utf-8 -*-

from collective.contact.plonegroup.config import DEFAULT_DIRECTORY_ID
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.config import set_registry_functions
from collective.contact.plonegroup.config import set_registry_groups_mgt
from collective.contact.plonegroup.config import set_registry_organizations
from collective.contact.plonegroup.testing import IntegrationTestCase
from collective.contact.plonegroup.utils import get_plone_group_id
from plone import api
from plone.app.testing import TEST_USER_ID
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

import re


class TestVocabularies(IntegrationTestCase):

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        # Organizations creation
        self.portal.invokeFactory("directory", DEFAULT_DIRECTORY_ID)
        self.directory = self.portal.get(DEFAULT_DIRECTORY_ID)
        self.directory.position_types = [
            {"token": "default", "name": "Default"},
            {"token": "position1", "name": "Position1"},
            {"token": "position2", "name": "Position2"},
        ]
        self.directory.invokeFactory("organization", PLONEGROUP_ORG, title="My organization")
        self.own_org = self.directory.get(PLONEGROUP_ORG)

    def _render_management_form(self):
        """Render @@manage-own-groups-users for a user managing 'investigators' and his 'director' groups."""
        dep1 = api.content.create(container=self.own_org, type="organization", id="department1", title="Department 1")
        set_registry_organizations([dep1.UID()])
        set_registry_functions(
            [{"fct_title": "Director", "fct_id": "director", "fct_orgs": [], "fct_management": True, "enabled": True}]
        )
        api.group.create("investigators", "Investigators")
        set_registry_groups_mgt(["investigators"])
        api.user.create("dxm@miami.pol", "dexter", properties={"fullname": "Dexter Morgan"})
        api.group.add_user(groupname="investigators", username=TEST_USER_ID)
        api.group.add_user(groupname="investigators", username="dexter")
        api.group.add_user(groupname=get_plone_group_id(dep1.UID(), "director"), username=TEST_USER_ID)
        return dep1, self.portal.restrictedTraverse("@@manage-own-groups-users")()

    def _selects(self, rendered, widget_id):
        """Return the options (value, title) of every select with given p_widget_id, by row."""
        return re.findall(
            r'<option id="form-widgets-{0}-novalue"[^>]*>[^<]*</option>|'
            r'<option id="form-widgets-{0}-\d+"[^>]*value="([^"]*)"[^>]*>([^<]*)</option>'.format(
                widget_id.replace("ROW", r"(?:\d+|AA|TT)")
            ),
            rendered,
        )

    def test_PositionTypesVocabulary(self):
        """When called from outside the directory,
        will return the position_types from the DEFAULT_DIRECTORY_ID."""
        vocab_factory = getUtility(IVocabularyFactory, "PositionTypes")
        # called on element inside the directory
        self.assertEqual(len(vocab_factory(self.own_org)), 3)
        # called on element outside the directory
        self.assertEqual(len(vocab_factory(self.portal)), 3)

    def test_FunctionsVocabulary(self):
        """Every configured function, enabled or not."""
        factory = getUtility(IVocabularyFactory, "collective.contact.plonegroup.functions")
        self.assertEqual(len(factory(self.portal)), 0)
        set_registry_functions(
            [
                {
                    "fct_title": "Director",
                    "fct_id": "director",
                    "fct_orgs": [],
                    "fct_management": False,
                    "enabled": True,
                },
                {"fct_title": "Worker", "fct_id": "worker", "fct_orgs": [], "fct_management": False, "enabled": False},
            ]
        )
        self.assertListEqual(
            [(term.value, term.token, term.title) for term in factory(self.portal)],
            [("director", "director", "Director"), ("worker", "worker", "Worker")],
        )

    def test_GlobalGroupsVocabulary(self):
        """Every group but the special and the suffixed ones."""
        factory = getUtility(IVocabularyFactory, "collective.contact.plonegroup.global_groups")
        dep1 = api.content.create(container=self.own_org, type="organization", id="department1", title="Department 1")
        set_registry_organizations([dep1.UID()])
        set_registry_functions(
            [{"fct_title": "Director", "fct_id": "director", "fct_orgs": [], "fct_management": False, "enabled": True}]
        )
        self.assertTrue(api.group.get(get_plone_group_id(dep1.UID(), "director")))
        api.group.create("investigators", "Investigators")
        api.group.create("no_title")
        api.group.create("{0}_unknown".format(dep1.UID()), "Not a function suffix")
        self.assertListEqual(
            sorted([(term.value, term.title) for term in factory(self.portal)]),
            sorted(
                [
                    ("investigators", "Investigators"),
                    ("no_title", "no_title"),
                    ("{0}_unknown".format(dep1.UID()), "Not a function suffix"),
                ]
            ),
        )

    def test_GroupsTerms(self):
        """Global groups of the management form list the managed groups of the current user."""
        dep1, rendered = self._render_management_form()
        # 2 existing rows, the auto-append row and the template row
        self.assertListEqual(
            self._selects(rendered, "_groups_-ROW-widgets-group"), [("", ""), ("investigators", "Investigators")] * 4
        )

    def test_OrganizationsTerms(self):
        """Function rows of the management form list the organizations of the current user for this function."""
        dep1, rendered = self._render_management_form()
        self.assertListEqual(
            self._selects(rendered, "director-ROW-widgets-group"), [("", ""), (dep1.UID(), "Department 1")] * 3
        )

    def test_DGFVocabularyTerms(self):
        """User columns of the management form use the vocabulary of the field."""
        dep1, rendered = self._render_management_form()
        users = [("", ""), ("dexter", "Dexter Morgan (dexter)"), ("test_user_1_", "test_user_1_ (test_user_1_)")]
        self.assertListEqual(self._selects(rendered, "_groups_-ROW-widgets-user"), users * 4)
        self.assertListEqual(self._selects(rendered, "director-ROW-widgets-user"), users * 3)
