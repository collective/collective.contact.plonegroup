# -*- coding: utf-8 -*-
""" utils.py tests for this package."""

from ..testing import IntegrationTestCase
from ..utils import organizations_with_suffixes


class TestUtils(IntegrationTestCase):

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']

    def test_organizations_with_suffixes(self):
        class Dum(object):
            def __init__(self, id):
                self.id = id
        ret = organizations_with_suffixes([], [])
        self.assertListEqual(ret, [])
        ret = organizations_with_suffixes([Dum('a'), Dum('b_1'), Dum('c_1'), Dum('c_2'), Dum('d_2'), Dum('e_3')],
                                          ['1', '3'])
        self.assertListEqual(ret, ['b', 'c', 'e'])
        ret = organizations_with_suffixes([Dum('a'), Dum('b_1_1'), Dum('c_1_1')], ['1_1'])
        self.assertListEqual(ret, ['b', 'c'])

    def test_voc_selected_org_suffix_users(self):
        self.assertFalse('Test must be adapted from imio.dms.mail')
