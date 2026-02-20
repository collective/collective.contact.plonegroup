# -*- coding: utf-8 -*-
from collective.contact.core.content.held_position import IHeldPosition
from plone.indexer import indexer
from Products.CMFPlone.utils import base_hasattr
from Products.PluginIndexes.common.UnIndex import _marker as common_marker


@indexer(IHeldPosition)
def heldposition_userid_index(obj):
    """Indexer of 'userid' for IHeldPosition. Stores parent userid !"""
    parent = obj.aq_parent
    if base_hasattr(parent, "userid") and parent.userid:
        return parent.userid
    return common_marker
