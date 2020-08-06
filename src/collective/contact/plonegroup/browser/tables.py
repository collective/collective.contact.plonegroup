# -*- coding: utf-8 -*-

from collections import OrderedDict
from collective.contact.core.content.organization import IOrganization
from collective.contact.plonegroup import _
from collective.contact.plonegroup.config import get_registry_organizations
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.interfaces import IPloneGroupContact
from collective.contact.plonegroup.utils import get_plone_groups
from collective.eeafaceted.z3ctable.browser.views import ExtendedCSSTable
from collective.eeafaceted.z3ctable.columns import get_user_fullname
from collective.eeafaceted.z3ctable.columns import ActionsColumn
from collective.eeafaceted.z3ctable.columns import BaseColumn
from collective.eeafaceted.z3ctable.columns import BooleanColumn
from collective.eeafaceted.z3ctable.columns import PrettyLinkWithAdditionalInfosColumn
from plone import api
from Products.CMFPlone.utils import safe_unicode
from Products.Five import BrowserView
from zope.cachedescriptors.property import CachedProperty
from zope.i18n import translate


class SubOrganizationsTable(ExtendedCSSTable):
    """Table that displays templates info."""

    cssClassEven = u'even'
    cssClassOdd = u'odd'
    cssClasses = {'table': 'listing nosort templates-listing icons-on'}

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

        plone_groups = get_plone_groups(org_uid)
        # prepare data
        data = OrderedDict()
        for plone_group in plone_groups:
            group_title = plone_group.getProperty('title')
            group_suffix = group_title[group_title.rfind('(') + 1:-1]
            group_identifier = (plone_group.getId(), group_suffix)
            data[group_identifier] = []
            for member in plone_group.getGroupMembers():
                data[group_identifier].append(
                    "{0} ({1})".format(get_user_fullname(member), member.getId())
                )
        # format data
        res = u''
        portal = api.portal.get()
        portal_url = portal.absolute_url()
        no_members_msg = _('No user was found in this group.')
        no_members_msg = translate(no_members_msg, context=self.request)
        for group_infos, members in sorted(data.items()):
            group_id, group_suffix = group_infos
            res += u'<a href="%s/@@usergroup-groupmembership?groupname=%s">%s</a><br/>' % (
                portal_url, group_id, safe_unicode(group_suffix))
            if not members:
                res += u'<em class="discreet">%s</em><br/>' % no_members_msg
            else:
                res += u'<ul class="discreet">'
                members = sorted(members)
                member_infos = [u'<li>%s</li>' % safe_unicode(member) for member in members]
                res += u''.join(member_infos)
                res += u'</ul>'
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
