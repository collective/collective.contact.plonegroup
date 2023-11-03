# -*- coding: utf-8 -*-

from collective.contact.plonegroup import _
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.interface import alsoProvides


class IPlonegroupUserLink(model.Schema):

    userid = schema.Choice(
        title=_(u'Plone user'),
        required=False,
        vocabulary=u'plone.app.vocabularies.Users',
    )

    directives.read_permission(userid='collective.contact.plonegroup.write_userid_field')
    directives.write_permission(userid='collective.contact.plonegroup.write_userid_field')


alsoProvides(IPlonegroupUserLink, IFormFieldProvider)
