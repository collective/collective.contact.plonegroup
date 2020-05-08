# -*- coding: utf-8 -*-
from collective.contact.plonegroup.config import get_registry_functions
from operator import methodcaller
from z3c.form.term import ChoiceTermsVocabulary
from zope.component import getUtility
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class FunctionsVocabulary(object):
    """Vocabulary of existing functions."""

    implements(IVocabularyFactory)

    def __call__(self, context):
        functions = get_registry_functions()
        terms = []
        for function in functions:
            terms.append(
                SimpleTerm(function['fct_id'],
                           function['fct_id'],
                           function['fct_title']))
        return SimpleVocabulary(terms)


class GroupsTerms(ChoiceTermsVocabulary):

    def __init__(self, context, request, form, field, widget):
        self.context = context
        self.request = request
        self.form = form
        self.field = field
        self.widget = widget
        # see DataGridFieldObjectSubForm
        mainform = self.form.parentForm
        terms = []
        for group_id in sorted(mainform.groupids, key=mainform.groupids.get):
            terms.append(SimpleTerm(group_id, title=mainform.groupids[group_id]))
        self.terms = SimpleVocabulary(terms)
        field.vocabulary = self.terms


class OrganizationsTerms(ChoiceTermsVocabulary):

    def __init__(self, context, request, form, field, widget):
        self.context = context
        self.request = request
        self.form = form
        self.field = field
        self.widget = widget
        # see DataGridFieldObjectSubForm
        mainform = self.form.parentForm
        # like 'form.widgets.encodeur.0'
        fieldname = self.form.__parent__.name.split('.')[2]
        terms = []
        for org in sorted(mainform.functions_orgs[fieldname], key=methodcaller('get_full_title')):
            terms.append(SimpleTerm(org.UID(), title=org.get_full_title(separator=' - ', first_index=1)))
        self.terms = SimpleVocabulary(terms)
        field.vocabulary = self.terms


class DGFVocabularyTerms(ChoiceTermsVocabulary):

    def __init__(self, context, request, form, field, widget):
        self.context = context
        self.request = request
        self.form = form
        self.field = field
        self.widget = widget
        # see DataGridFieldObjectSubForm
        mainform = self.form.parentForm
        self.terms = getUtility(IVocabularyFactory, field.vocabularyName)(mainform.context)
        field.vocabulary = self.terms
