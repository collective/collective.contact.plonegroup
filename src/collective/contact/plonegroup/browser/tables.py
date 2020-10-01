# -*- coding: utf-8 -*-

from collective.contact.core.content.organization import IOrganization
from collective.contact.plonegroup import _
from collective.contact.plonegroup.config import get_registry_organizations
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.interfaces import IPloneGroupContact
from collective.contact.plonegroup.utils import get_all_suffixes
from collective.contact.plonegroup.utils import get_plone_group_id
from collective.eeafaceted.z3ctable.browser.views import ExtendedCSSTable
from collective.eeafaceted.z3ctable.columns import ActionsColumn
from collective.eeafaceted.z3ctable.columns import BaseColumn
from collective.eeafaceted.z3ctable.columns import BooleanColumn
from collective.eeafaceted.z3ctable.columns import PrettyLinkWithAdditionalInfosColumn
from plone import api
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import _checkPermission
from Products.CMFPlone.utils import base_hasattr
from Products.Five import BrowserView
from zope.cachedescriptors.property import CachedProperty
from zope.i18n import translate


class SubOrganizationsTable(ExtendedCSSTable):
    """Table that displays templates info."""

    cssClassEven = u'even'
    cssClassOdd = u'odd'
    cssClasses = {'table': 'listing nosort suborganizations-listing icons-on'}

    batchSize = 999
    startBatchingAt = 999
    sortOn = None
    results = []

    def __init__(self, context, request):
        super(SubOrganizationsTable, self).__init__(context, request)
        self.portal = api.portal.getSite()
        self.context_path = self.context.absolute_url_path()
        self.context_path_level = len(self.context_path.split('/'))
        self.paths = {'.': '-'}
        self.portal_url = self.portal.absolute_url()

    @CachedProperty
    def values(self):
        return self.results


class SubOrganizationsTableView(BrowserView):

    __table__ = SubOrganizationsTable
    provides = [IPloneGroupContact.__identifier__]
    depth = None
    local_search = True

    def __init__(self, context, request):
        super(SubOrganizationsTableView, self).__init__(context, request)

    def query_dict(self):
        crit = {'object_provides': self.provides}
        if self.local_search:
            container_path = '/'.join(self.context.getPhysicalPath())
            crit['path'] = {'query': container_path}
            if self.depth is not None:
                crit['path']['depth'] = self.depth
        return crit

    def update(self):
        self.table = self.__table__(self.context, self.request)
        self.table.__name__ = u'suborganizations'
        catalog = api.portal.get_tool('portal_catalog')
        brains = catalog.searchResults(**self.query_dict())

        def keys(brain):
            """Order by get_full_title that displays organizations and sub organizations."""
            obj = brain.getObject()
            return obj.get_full_title()

        # sort by parent path and by position
        # the catalog search returns also context, remove it
        self.table.results = [brain for brain in sorted(brains, key=keys) if brain.UID != self.context.UID()]
        self.table.update()

    def render_original_suborgs(self):
        """Render suborganizations like it is originally made in collective.contact.core."""
        original_suborgs_view = self.context.restrictedTraverse('@@original-suborganizations')
        return original_suborgs_view()

    def __call__(self):
        """ """
        self.update()
        return self.index()


class OrgaPrettyLinkWithAdditionalInfosColumn(PrettyLinkWithAdditionalInfosColumn):
    """ """

    params = {
        'showContentIcon': True,
        'target': '_blank',
        'additionalCSSClasses': ['link-tooltip'],
        'display_tag_title': False}

    def contentValue(self, item):
        """Display get_full_title instead title."""
        if IOrganization.providedBy(item):
            # find first_index relative to PLONEGROUP_ORG organization
            path = item.getPhysicalPath()
            if item.getId() == PLONEGROUP_ORG or PLONEGROUP_ORG not in path:
                first_index = 0
            else:
                # 1 considering that PLONEGROUP is at 1st level.
                # Otherwise must use get_organizations_chain
                first_index = 1
            return item.get_full_title(first_index=first_index)
        else:
            return item.get_full_title()


class DisplayGroupUsersView(BrowserView):
    """
      View that display the users of a Plone group.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.portal_url = api.portal.get().absolute_url()

    def _check_auth(self, group_id):
        """When using '*' make it possible to check if authorized."""
        return

    def _get_suffixes(self, group_id):
        """Make it possible to ignore some suffixes for p_group_id."""
        suffixes = get_all_suffixes(group_id)
        return suffixes

    def __call__(self, group_ids, short=False):
        """p_groups_ids is a list of group ids.
           If p_group_ids is a string :
           - if ends with '*', it is an organization UID, we return every suffixed groups;
           - if a simple str, we turn it into a list."""
        self.short = short
        self.is_manager = self._is_manager
        if not hasattr(group_ids, '__iter__'):
            if group_ids.endswith('*'):
                # remove ending '*'
                group_id = group_ids[:-1]
                self._check_auth(group_id)
                # me received a organization UID, get the Plone group ids
                suffixes = self._get_suffixes(group_id)
                group_ids = [get_plone_group_id(group_id, suffix)
                             for suffix in suffixes]
            else:
                group_ids = [group_ids]
        self.groups = [api.group.get(tmp_group_id) for tmp_group_id in group_ids]
        return self.index()

    def group_title(self, group):
        """ """
        group_title = group.getProperty('title')
        if self.short:
            group_title = group_title.split('(')[-1][:-1]
        return group_title

    def _get_groups_and_members(self, group, index=0, keep_subgroups=False):
        """ """
        members = []
        if keep_subgroups and index != 0:
            members.append((index, group))
            index += 1
        for principal in group.getAllGroupMembers():
            isGroup = base_hasattr(principal, 'isGroup') and principal.isGroup() or 0
            if isGroup:
                members += self._get_groups_and_members(principal, index + 1, keep_subgroups)
            else:
                # avoid 2 times same member whith sub groups and keep_subgroups=False
                if keep_subgroups or (principal not in [p for i, p in members]):
                    members.append((index, principal))
        return members

    def group_users(self, group):
        """ """
        res = []
        patterns = {}
        # use _ for i18ndude machinery
        user_tag_title = _('View Plone user')
        user_tag_title = translate(user_tag_title, context=self.request)
        group_tag_title = _('View Plone group')
        group_tag_title = translate(group_tag_title, context=self.request)
        patterns[0] = "<img src='%s/user.png'> " % self.portal_url
        patterns[1] = "<img src='%s/group.png'> " % self.portal_url
        if self.is_manager:
            patterns[0] = "<a class='user-or-group-level-{{index}}' href='{portal_url}/" \
                "@@user-information?userid={{member_id}}' " \
                "title=\"{user_tag_title}\"><acronym>{pattern}</acronym></a> ".format(
                **{'portal_url': self.portal_url,
                   'pattern': patterns[0].strip(),
                   'user_tag_title': user_tag_title})
            patterns[1] = "<a class='user-or-group-level-{{index}}' href='{portal_url}/" \
                "@@usergroup-groupmembership?groupname={{member_id}}' " \
                "title=\"{group_tag_title}\"><acronym>{pattern}</acronym></a> ".format(
                **{'portal_url': self.portal_url,
                   'pattern': patterns[1].strip(),
                   'group_tag_title': group_tag_title})
        for index, principal in self._get_groups_and_members(group, keep_subgroups=self.is_manager):
            # member may be a user or group
            isGroup = base_hasattr(principal, 'isGroup') and principal.isGroup() or 0
            principal_title = principal.getProperty('fullname') or \
                principal.getProperty('title') or principal.getId()
            if self.is_manager:
                principal_title = principal_title + " ({0})".format(principal.id)
            principal_title = "<div class='user-or-group user-or-group-level-{0}'>{1}</div>".format(
                index, principal_title)
            value = patterns[isGroup].format(**{'member_id': principal.id,
                                                'index': index}) + principal_title
            res.append((index, principal_title, value))
        # sort on member_title
        res = sorted(res)
        # just keep values
        return "".join([v[2] for v in res])

    @property
    def _is_manager(self):
        """ """
        return _checkPermission(ManagePortal, self.context)


class PloneGroupUsersGroupsColumn(BaseColumn):
    """Column that displays Plone groups and users linked to an organization."""

    header = _("Groups and users")
    weight = 5

    def renderCell(self, item):
        """ """
        plonegroup_organizations = get_registry_organizations()
        org_uid = item.UID
        if org_uid not in plonegroup_organizations:
            return "-"

        suffixes = get_all_suffixes(org_uid)
        group_ids = [get_plone_group_id(org_uid, suffix)
                     for suffix in suffixes]
        url_group_ids = '&group_ids='.join(group_ids)
        # use _ for i18ndude machinery
        details_msg = _('Details')
        details_msg = translate(details_msg, context=self.request)
        res = u"<div id=\"group-users\" class=\"collapsible\" onclick=\"toggleDetails(" \
            u"'collapsible-group-users_{0}', toggle_parent_active=false, parent_tag=null, " \
            u"load_view='@@display-group-users?group_ids={1}', base_url='{2}');\"> {3}</div>" \
            u"<div id=\"collapsible-group-users_{0}\" class=\"collapsible-content\" style=\"display: none;\">" \
            u"<div class=\"collapsible-inner-content\">" \
            u"<img src=\"{2}/spinner_small.gif\" /></div></div>".format(
                org_uid, url_group_ids, self.table.portal_url, details_msg)
        return res


class SelectedInPlonegroupColumn(BooleanColumn):
    """Column that displays Yes/No depending on fact that
       organization is selected in plonegroup organizations."""

    header = _("Selected in plonegroup")
    weight = 10

    def renderHeadCell(self):
        """ """
        portal = api.portal.get()
        plonegroup_url = '{0}/@@contact-plonegroup-settings'.format(portal.absolute_url())
        return translate("Selected in plonegroup",
                         domain='collective.contact.plonegroup',
                         mapping={'plonegroup_url': plonegroup_url},
                         context=self.request)

    def getValue(self, item):
        """ """
        plonegroup_organizations = get_registry_organizations()
        org_uid = item.UID
        return bool(org_uid in plonegroup_organizations)


class PlonegroupActionsColumn(ActionsColumn):
    """ """

    header = _("Actions")
    weight = 20
    params = {'useIcons': True, 'showHistory': False, 'showActions': True, 'showOwnDelete': True,
              'showArrows': False, 'showTransitions': False, 'showPloneGroupLink': True}
    cssClasses = {'td': 'actions-column'}
