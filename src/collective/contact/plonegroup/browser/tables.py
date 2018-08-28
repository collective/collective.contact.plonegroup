# -*- coding: utf-8 -*-

from collective.contact.plonegroup.config import ORGANIZATIONS_REGISTRY
from collective.contact.plonegroup.interfaces import IPloneGroupContact
from collective.contact.plonegroup import _
from collective.eeafaceted.z3ctable.columns import ActionsColumn
from collective.eeafaceted.z3ctable.columns import BooleanColumn
from plone import api
from Products.Five import BrowserView
from z3c.table.table import Table
from zope.cachedescriptors.property import CachedProperty


class SubOrganizationsTable(Table):
    """Table that displays templates info."""

    cssClassEven = u'even'
    cssClassOdd = u'odd'
    cssClasses = {'table': 'listing nosort templates-listing icons-on'}

    batchSize = 200
    startBatchingAt = 200
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
            """ Goal: order by level of folder, parent folder, position in folder,"""
            obj = brain.getObject()
            return obj.get_full_title()

        # sort by parent path and by position
        # the catalog search returns also context, remove it
        self.table.results = [brain for brain in sorted(brains, key=keys) if brain.UID != self.context.UID()]
        self.table.update()

    def __call__(self, local_search=None, search_depth=None):
        """
            search_depth = int value (0)
            local_search = bool value
        """
        if search_depth is not None:
            self.depth = search_depth
        else:
            sd = self.request.get('search_depth', '')
            if sd:
                self.depth = int(sd)
        if local_search is not None:
            self.local_search = local_search
        else:
            self.local_search = 'local_search' in self.request or self.local_search
        self.update()
        return self.index()


class SelectedInPlonegroupColumn(BooleanColumn):
    """Column that displays Yes/No depending on fact that
       organization is selected in plonegroup organizations."""

    header = _("Selected in plonegroup")
    weight = 10

    def getValue(self, item):
        """ """
        plonegroup_organizations = api.portal.get_registry_record(ORGANIZATIONS_REGISTRY)
        orga_uid = item.UID
        return bool(orga_uid in plonegroup_organizations)


class PlonegroupActionsColumn(ActionsColumn):
    """
    A column displaying available actions of the listed item.
    Need imio.actionspanel to be used !
    """

    header = _("Actions")
    weight = 20
    params = {'useIcons': True, 'showHistory': False, 'showActions': True, 'showOwnDelete': True,
              'showArrows': False, 'showTransitions': False, 'showPloneGroupLink': True}
    cssClasses = {'td': 'actions-column'}
