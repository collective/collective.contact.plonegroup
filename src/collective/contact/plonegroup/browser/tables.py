# -*- coding: utf-8 -*-

from collective.contact.plonegroup import _
from collective.contact.plonegroup.config import ORGANIZATIONS_REGISTRY
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.interfaces import IPloneGroupContact
from collective.eeafaceted.z3ctable.browser.views import ExtendedCSSTable
from collective.eeafaceted.z3ctable.columns import ActionsColumn
from collective.eeafaceted.z3ctable.columns import BooleanColumn
from collective.eeafaceted.z3ctable.columns import PrettyLinkWithAdditionalInfosColumn
from plone import api
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

    def contentValue(self, item):
        """Display get_full_title instead title."""
        # find first_index relative to PLONEGROUP_ORG organization
        if item.getId() == PLONEGROUP_ORG:
            first_index = 0
        else:
            path = item.getPhysicalPath()
            first_index = len(path) - path.index(PLONEGROUP_ORG)
        return u'{0} <span class="discreet">({1})</span>'.format(
            item.get_full_title(first_index=first_index), item.UID())


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
        plonegroup_organizations = api.portal.get_registry_record(ORGANIZATIONS_REGISTRY)
        orga_uid = item.UID
        return bool(orga_uid in plonegroup_organizations)


class PlonegroupActionsColumn(ActionsColumn):
    """ """

    header = _("Actions")
    weight = 20
    params = {'useIcons': True, 'showHistory': False, 'showActions': True, 'showOwnDelete': True,
              'showArrows': False, 'showTransitions': False, 'showPloneGroupLink': True}
    cssClasses = {'td': 'actions-column'}
