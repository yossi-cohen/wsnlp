'''
a pipeline for extracting entities.

you can add entity extraction to nlp.pipeline using:
    pipeline = EntitiesPipeline()
    nlp.add_pipe(pipeline, after='ner')

you can add your relation extrators (one or more) using:
    pipeline.add_pipe(YOUR_EntityExtractor())

'''

import spacy
from spacy.tokens import Span
from .en_term_list import EN_TERM_LIST
from .es_term_list import ES_TERM_LIST
from .term_list_matcher import TermList_Matcher
from .en_ent_rules import EN_EntityRules
from .es_ent_split import ES_EntitySplit


class EntitiesPipeline(object):
    name = 'nlpy_entities'
    pipe_ = []

    def __init__(self, nlp, merge_entity_spans = False):
        if (nlp.lang == 'en'):
            self.add_pipe(EN_EntityRules())
            self.add_pipe(TermList_Matcher(nlp, EN_TERM_LIST))
        elif (nlp.lang == 'es'):
            self.add_pipe(ES_EntitySplit())
            self.add_pipe(TermList_Matcher(nlp, ES_TERM_LIST))
        
        # should we merge entities spans
        self.merge_entity_spans = merge_entity_spans

    def __call__(self, doc):

        entities = []
        for c in self.pipe_:
            doc = c(doc, entities)

        #  add extracted entities to doc.ents
        for e in entities:
            start, end, label = e
            span = Span(doc, start, end, label=label)
            doc.ents = list(doc.ents) + [span]

        # merge entities into one token? (default to False)
        if (self.merge_entity_spans):
            for span in doc.ents:
                span.merge()

        return doc

    def add_pipe(self, component):
        self.pipe_.append(component)
