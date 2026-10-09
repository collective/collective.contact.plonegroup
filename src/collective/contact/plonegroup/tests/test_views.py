# -*- coding: utf-8 -*-
""" utils.py tests for this package."""

from collective.contact.plonegroup.browser.tables import SelectedInPlonegroupColumn
from collective.contact.plonegroup.config import DEFAULT_DIRECTORY_ID
from collective.contact.plonegroup.config import get_registry_functions
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.config import set_registry_functions
from collective.contact.plonegroup.config import set_registry_groups_mgt
from collective.contact.plonegroup.config import set_registry_organizations
from collective.contact.plonegroup.testing import FunctionalTestCase
from collective.contact.plonegroup.utils import get_own_organization
from collective.contact.plonegroup.utils import get_plone_group
from collective.contact.plonegroup.utils import get_plone_group_id
from plone import api
from plone.app.testing import login
from plone.app.testing import TEST_USER_ID
from plone.registry.interfaces import IRegistry
from zExceptions import Redirect
from zope.component import getUtility
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

import re


class TestViews(FunctionalTestCase):

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        # Organizations creation
        self.portal.invokeFactory("directory", DEFAULT_DIRECTORY_ID, organization_levels=[])
        self.portal[DEFAULT_DIRECTORY_ID].invokeFactory("organization", PLONEGROUP_ORG, title="My organization")
        self.own_orga = get_own_organization()
        self.dep1 = api.content.create(
            container=self.own_orga, type="organization", id="department1", title="Department 1"
        )
        self.uid = self.dep1.UID()
        self.dep2 = api.content.create(
            container=self.own_orga, type="organization", id="department2", title="Department 2"
        )
        # users and groups
        api.user.create("dxm@miami.pol", "dexter", properties={"fullname": "Dexter Morgan"})
        api.user.create("dbm@miami.pol", "debra", properties={"fullname": "Debra Morgan"})
        self.inv_group = api.group.create("investigators", "Investigators")
        self.tech_group = api.group.create("technicians", "Technicians")
        # settings
        self.registry = getUtility(IRegistry)
        set_registry_organizations([self.uid])
        set_registry_functions(
            [
                {
                    "fct_title": "Observers",
                    "fct_id": "observer",
                    "fct_orgs": [],
                    "fct_management": False,
                    "enabled": True,
                },
                {
                    "fct_title": "Director",
                    "fct_id": "director",
                    "fct_orgs": [],
                    "fct_management": False,
                    "enabled": True,
                },
            ]
        )

    def test_management_view(self):
        view = self.portal.unrestrictedTraverse("@@manage-own-groups-users")
        # No groups activated
        self.assertListEqual(view.get_manageable_groups(), [])
        self.assertListEqual(view.get_manageable_functions(), [])

        # we activate groups and functions
        functions = get_registry_functions(as_copy=False)
        functions[0]["fct_management"] = True
        set_registry_groups_mgt(["investigators"])
        view.init()
        self.assertListEqual(view.get_manageable_groups(), ["investigators"])
        self.assertListEqual(view.get_manageable_functions(), ["observer"])
        view.get_user_manageable_groups()  # fill in view.groupids
        view.get_user_manageable_functions()  # fill in view.functions_orgs
        self.assertDictEqual(view.groupids, {})
        self.assertDictEqual(view.functions_orgs, {})

        # we add the current user to the activated groups, so he can manage it
        api.group.add_user(groupname="investigators", username=TEST_USER_ID)
        api.group.add_user(groupname="{}_observer".format(self.uid), username=TEST_USER_ID)

        def get_user_groups(userid):
            return sorted([g.id for g in api.group.get_groups(username=userid) if g.id not in ["AuthenticatedUsers"]])

        self.assertListEqual(get_user_groups(TEST_USER_ID), sorted(["{}_observer".format(self.uid), "investigators"]))
        view = self.portal.unrestrictedTraverse("@@manage-own-groups-users")
        view.init()
        self.assertListEqual(view.get_manageable_groups(), ["investigators"])
        self.assertListEqual(view.get_manageable_functions(), ["observer"])
        view.get_user_manageable_groups()  # fill in view.groupids
        view.get_user_manageable_functions()  # fill in view.functions_orgs
        self.assertDictEqual(view.groupids, {"investigators": "Investigators"})
        self.assertDictEqual(view.functions_orgs, {"observer": [self.dep1]})

        # we check the values given to the fields
        view.update()
        self.assertListEqual(view.fieldnames, ["_groups_", "observer", "_old_values_"])
        content = view.getContent()
        self.assertListEqual(content._groups_, [{"group": "investigators", "user": "test_user_1_"}])
        self.assertListEqual(content.observer, [{"group": self.uid, "user": "test_user_1_"}])
        old_values = (
            "{{'_groups_': [{{'group': 'investigators', 'user': 'test_user_1_'}}], 'observer': "
            "[{{'group': '{}', 'user': 'test_user_1_'}}]}}".format(self.uid)
        )
        self.assertEqual(content._old_values_, old_values)

        # applying form : we add users
        self.assertListEqual(get_user_groups("dexter"), [])
        self.assertListEqual(get_user_groups("debra"), [])
        data = {
            "_groups_": content._groups_ + [{"group": "investigators", "user": "debra"}],
            "observer": content.observer + [{"group": self.uid, "user": "dexter"}],
            "_old_values_": old_values,
        }
        view.widgets.extract = lambda *a, **kw: (data, [])
        view.handleApply(view, "apply")
        self.assertListEqual(get_user_groups("dexter"), ["{}_observer".format(self.uid)])
        self.assertListEqual(get_user_groups("debra"), ["investigators"])
        # we add/remove users
        data = {
            "_groups_": [dic for dic in content._groups_ if dic["user"] != "debra"]
            + [{"group": "investigators", "user": "dexter"}],
            "observer": [dic for dic in content.observer if dic["user"] != "dexter"]
            + [{"group": self.uid, "user": "debra"}],
            "_old_values_": content._old_values_,
        }
        view.widgets.extract = lambda *a, **kw: (data, [])
        view.handleApply(view, "apply")
        self.assertListEqual(get_user_groups("dexter"), ["investigators"])
        self.assertListEqual(get_user_groups("debra"), ["{}_observer".format(self.uid)])

        # we cannot remove current user
        data = {
            "_groups_": [dic for dic in content._groups_ if dic["user"] == ""],
            "observer": [dic for dic in content.observer if dic["user"] == ""],
            "_old_values_": content._old_values_,
        }
        view.widgets.extract = lambda *a, **kw: (data, [])
        self.assertRaises(Redirect, view.handleApply, view, "apply")

        # we cannot handle incomplete data
        data = {
            "_groups_": content._groups_ + [{"group": "investigators", "user": None}],
            "observer": content.observer,
            "_old_values_": content._old_values_,
        }
        view.widgets.extract = lambda *a, **kw: (data, [])
        self.assertRaises(Redirect, view.handleApply, view, "apply")

    def test_display_group_users(self):
        # add user "dexter" to dep1 observer Plone group
        observer = get_plone_group_id(self.dep1.UID(), "observer")
        api.group.add_user(groupname=observer, username="dexter")
        view = self.portal.restrictedTraverse("@@display-group-users")
        self.assertTrue("group.png" in view(group_ids=[observer]))
        # when using "*", every groups are displayed
        every_groups = view(group_ids=self.uid + "*")
        self.assertTrue("group.png" in every_groups)
        self.assertTrue("user.png" in every_groups)
        self.assertTrue("Department 1 (Observers)" in every_groups)
        self.assertTrue("Department 1 (Director)" in every_groups)
        # dexter in Department 1 (Observers)
        self.assertTrue("Dexter Morgan (dexter, dxm@miami.pol)" in every_groups)
        # nobody in Department 1 (Director)
        self.assertTrue("No user was found in this group." in every_groups)
        # with parameter "short"
        self.assertTrue(view(group_ids=self.uid + "*", short=True))
        # when called on an organization that is not selected in plonegroup
        not_selected_org = view(group_ids=self.dep2.UID() + "*")
        self.assertTrue("Nothing." in not_selected_org)
        # as non Manager, we do not see user user_id and email
        login(self.portal, "dexter")
        every_groups = view(group_ids=self.uid + "*")
        self.assertTrue("Department 1 (Observers)" in every_groups)
        self.assertTrue("Dexter Morgan</div>" in every_groups)

    def test_display_group_users_group_title(self):
        view = self.portal.restrictedTraverse("@@display-group-users")
        observer = get_plone_group(self.dep1.UID(), "observer")
        view.short = False
        self.assertEqual(view.group_title(observer), "Department 1 (Observers)")
        view.short = True
        self.assertEqual(view.group_title(observer), "Observers")
        # when org title contains parentheses
        self.dep1.setTitle("Department 1 (Sample)")
        notify(ObjectModifiedEvent(self.dep1))
        observer = get_plone_group(self.dep1.UID(), "observer")
        view.short = False
        self.assertEqual(view.group_title(observer), "Department 1 (Sample) (Observers)")
        view.short = True
        self.assertEqual(view.group_title(observer), "Observers")
        # when org title contains several parentheses
        self.dep1.setTitle("Department 1 (Sample) (Additional)")
        notify(ObjectModifiedEvent(self.dep1))
        observer = get_plone_group(self.dep1.UID(), "observer")
        view.short = False
        self.assertEqual(view.group_title(observer), "Department 1 (Sample) (Additional) (Observers)")
        view.short = True
        self.assertEqual(view.group_title(observer), "Observers")

    def test_suborganizations(self):
        own_org = get_own_organization()
        view = own_org.restrictedTraverse("@@suborganizations")
        rendered = view()
        self.assertTrue("actionspanel" in rendered)
        self.assertTrue(self.dep1.absolute_url() in rendered)
        self.assertTrue(self.dep2.absolute_url() in rendered)
        # link to the settings
        self.assertIn('<a href="http://nohost/plone/@@contact-plonegroup-settings">', rendered)
        # columns
        self.assertEqual(
            re.findall(r'<th class="th_header_(\w+)">', rendered),
            ["Title", "PloneGroupUsersGroupsColumn", "SelectedInPlonegroupColumn"],
        )
        rows = rendered.split("<tr  class=")[1:]
        self.assertEqual(len(rows), 2)
        # title: pretty link opened in a new tab, with a tooltip, full title
        # Plone 6: data-base_url is the page loaded by the tooltip (collective.contact.core forms.js)
        self.assertIn(
            "<a class='pretty_link link-tooltip' data-base_url='{0}' href='{0}' target='_blank'>".format(
                self.dep1.absolute_url()
            ),
            rows[0],
        )
        self.assertIn("<span class='pretty_link_content state-active'>Department 1</span>", rows[0])
        # groups and users: collapsible "Details" loading the Plone groups of the organization
        self.assertIn(
            "load_view='@@display-group-users?group_ids={0}_observer&group_ids={0}_director"
            "&short:boolean=True', base_url='http://nohost/plone');\">".format(self.uid),
            rows[0],
        )
        self.assertIn("Details</", rows[0])
        self.assertIn(
            '<div id="collapsible-group-users_{0}" class="collapsible-content" style="display: none;">'.format(
                self.uid
            ),
            rows[0],
        )
        # selected in plonegroup: Yes for department1, No for department2
        self.assertIn('<td class="td_cell_SelectedInPlonegroupColumn bool_value_true">', rows[0])
        self.assertIn('<td class="td_cell_SelectedInPlonegroupColumn bool_value_false">', rows[1])
        # actions: edit, delete, cut, copy, rename
        for action in ('/edit"', "view_name='@@delete_givenuid'", "/object_cut", "/object_copy", "/object_rename"):
            self.assertIn(action, rows[1])
        self.assertIn('id="actions-panel-identifier-{0}"'.format(self.dep2.UID()), rows[1])
        # does not fail to render on an organization containing no organization
        view = self.dep1.restrictedTraverse("@@suborganizations")
        self.assertTrue("There is no organizations in this organization." in view())

    def test_suborganizations_content_icon(self):
        """The organization icon shown in the title column is an existing image."""
        rendered = get_own_organization().restrictedTraverse("@@suborganizations")()
        icon_url = re.search(
            r"<span class='pretty_link_icons'><img title='Organization' src='([^']+)'", rendered
        ).group(1)
        self.assertTrue(self.portal.unrestrictedTraverse(str(icon_url.replace(self.portal.absolute_url() + "/", ""))))

    def test_render_original_suborgs(self):
        """With ajax_load (in a tooltip), the original collective.contact.core list is rendered."""
        own_org = get_own_organization()
        original = own_org.restrictedTraverse("@@original-suborganizations")()
        self.assertIn('id="sub_organizations"', original)
        self.assertIn('<a class="link-tooltip" href="{0}"'.format(self.dep1.absolute_url()), original)
        self.layer["request"].form["ajax_load"] = "1"
        rendered = own_org.restrictedTraverse("@@suborganizations")()
        self.assertIn('id="sub_organizations"', rendered)
        self.assertIn('<a class="link-tooltip" href="{0}"'.format(self.dep2.absolute_url()), rendered)
        self.assertNotIn("suborganizations-listing", rendered)

    def test_renderHeadCell(self):
        """The "Selected in plonegroup" header links to the settings."""
        request = self.layer["request"]
        request.other.pop("LANGUAGE_TOOL", None)
        request.environ["HTTP_ACCEPT_LANGUAGE"] = "fr"
        column = SelectedInPlonegroupColumn(self.own_orga, request, None)
        self.assertEqual(
            column.renderHeadCell(),
            "S\xe9lectionn\xe9 dans <a href='http://nohost/plone/@@contact-plonegroup-settings'>"
            '"Configuration des groupes plone via contact"</a>',
        )

    def test_group_users(self):
        """A Manager sees links, ids and emails, other users only see names."""
        observer = get_plone_group_id(self.uid, "observer")
        api.group.add_user(groupname=observer, username="dexter")
        self.portal.portal_groups.addPrincipalToGroup("technicians", observer)
        api.group.add_user(groupname="technicians", username="debra")
        view = self.portal.restrictedTraverse("@@display-group-users")
        rendered = view(group_ids=[observer])
        self.assertIn(
            '<a target="_parent" href="http://nohost/plone/@@usergroup-groupmembership?groupname={0}">'.format(
                observer
            ),
            rendered.replace("target='_parent'", 'target="_parent"'),
        )
        users = view.group_users(api.group.get(observer))
        self.assertEqual(
            users,
            "<a class='user-or-group-level-0' href='http://nohost/plone/@@user-information?userid=dexter' "
            "title=\"View Plone user\"><acronym><img src='http://nohost/plone/user.png'></acronym></a> "
            "<div class='user-or-group user-or-group-level-0'>Dexter Morgan (dexter, dxm@miami.pol)</div>"
            "<a class='user-or-group-level-1' href='http://nohost/plone/@@usergroup-groupmembership?"
            "groupname=technicians' title=\"View Plone group\"><acronym><img src='http://nohost/plone/group.png'>"
            "</acronym></a> <div class='user-or-group user-or-group-level-1'>Technicians (technicians)</div>"
            "<a class='user-or-group-level-2' href='http://nohost/plone/@@user-information?userid=debra' "
            "title=\"View Plone user\"><acronym><img src='http://nohost/plone/user.png'></acronym></a> "
            "<div class='user-or-group user-or-group-level-2'>Debra Morgan (debra, dbm@miami.pol)</div>",
        )
        # as a simple member
        login(self.portal, "dexter")
        view = self.portal.restrictedTraverse("@@display-group-users")
        rendered = view(group_ids=[observer])
        self.assertNotIn("@@usergroup-groupmembership", rendered)
        self.assertEqual(
            view.group_users(api.group.get(observer)),
            "<img src='http://nohost/plone/user.png'> <div class='user-or-group user-or-group-level-0'>Dexter Morgan"
            "</div><img src='http://nohost/plone/user.png'> <div class='user-or-group user-or-group-level-1'>"
            "Debra Morgan</div>",
        )

    def test_available(self):
        """The own-groups user action is available when groups or functions are manageable."""
        action = self.portal.portal_actions.user["own-groups"]
        self.assertEqual(action.url_expr, "string:${portal_url}/@@manage-own-groups-users")
        self.assertFalse(action.visible)

        def available():
            infos = self.portal.portal_actions.listActionInfos(
                action_chain="user/own-groups", object=self.portal, check_visibility=0
            )
            return infos and infos[0]["available"] or False

        view = self.portal.restrictedTraverse("@@manage-own-groups-users")
        self.assertFalse(view.available())
        self.assertFalse(available())
        set_registry_groups_mgt(["investigators"])
        self.assertTrue(view.available())
        self.assertTrue(available())
        set_registry_groups_mgt([])
        functions = get_registry_functions()
        functions[1]["fct_management"] = True
        set_registry_functions(functions)
        view = self.portal.restrictedTraverse("@@manage-own-groups-users")
        self.assertTrue(view.available())
        self.assertTrue(available())
