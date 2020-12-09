# -*- coding: utf-8 -*-

from collective.contact.plonegroup.config import DEFAULT_DIRECTORY_ID
from collective.contact.plonegroup.config import PLONEGROUP_ORG
from collective.contact.plonegroup.testing import IntegrationTestCase
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory


class TestVocabularies(IntegrationTestCase):

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        # Organizations creation
        self.portal.invokeFactory('directory', DEFAULT_DIRECTORY_ID)
        self.directory = self.portal.get(DEFAULT_DIRECTORY_ID)
        self.directory.position_types = [
            {'token': u'default', 'name': u'Default'},
            {'token': u'position1', 'name': u'Position1'},
            {'token': u'position2', 'name': u'Position2'}, ]
        self.directory.invokeFactory(
            'organization', PLONEGROUP_ORG, title='My organization')
        self.own_org = self.directory.get(PLONEGROUP_ORG)

    def test_PositionTypesVocabulary(self):
        """When called from outside the directory,
           will return the position_types from the DEFAULT_DIRECTORY_ID."""
        vocab_factory = getUtility(IVocabularyFactory, "PositionTypes")
        # called on element inside the directory
        self.assertEqual(len(vocab_factory(self.own_org)), 3)
        # called on element outside the directory
        self.assertEqual(len(vocab_factory(self.portal)), 3)
