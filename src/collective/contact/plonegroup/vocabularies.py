# -*- coding: utf-8 -*-
from collective.contact.plonegroup.config import get_registry_functions
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
