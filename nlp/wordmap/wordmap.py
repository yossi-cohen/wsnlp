import spacy
from spacy.tokens import Doc

SIMILARITY_TRESHOLD = 0.90


class Cluster(object):
    def __init__(self, item=None):
        if item:
            self.leader = item
            self.items = set([item])
        else:
            self.leader = None
            self.items = set([])
        self.merged = False

    def add(self, item):
        self.items.add(item)
        if (not self.leader):
            self.leader = item

    @staticmethod
    def merge(c1, c2):
        if not isinstance(c1, Cluster) or not isinstance(c2, Cluster):
            raise Exception()
        c = Cluster()
        c.items = c1.items.union(c2.items)
        c.leader = Cluster.select_leader(c1, c2)
        return c

    @staticmethod
    def select_leader(c1, c2):
        if not c1.leader:
            return c2.leader
        if not c2.leader:
            return c1.leader

        # lilo:TODO - how should we decide which leader to use?
        if (len(c1.leader) >= len(c2.leader)):
            return c1.leader

        return c2.leader


class Wordmap(object):
    def __init__(self, text, nlp):
        self.create_wordmap(text, nlp)

    def create_wordmap(self, text, nlp):
        self.nlp = nlp
        self.words = []
        with nlp.disable_pipes('nlpy_relations'):
            doc = nlp(text)
            clusters = self.cluster_entities(doc)
            sorted(clusters, key=lambda c: len(c.items), reverse=True)
            doc_len = 0
            for c in clusters:
                doc_len += len(c.items)
            for c in clusters:
                # lilo:print(c.leader, len(c.items))
                self.words.append((c.leader.text, len(c.items) / doc_len))

            # print('lilo ---------------------------- noun_chunks:begin')
            # for chunk in doc.noun_chunks:
            #     print(chunk.text)
                # for t in chunk:
                #     print(t.text, t.pos_)
            # print('lilo ---------------------------- noun_chunks:end')

    def cluster_entities(self, doc):
        '''
        cluster mentions of entities together
        '''
        # lilo:TODO
        # if (not 'mentions' in doc._):
        #     Doc.set_extension('mentions', default=[])

        # start with each entity in its own cluster
        clusters = []
        for e in doc.ents:
            if (e.label_ in ('DATE', 'TIME', 'NORP')):
                continue  # skip some entity types
            clusters.append(Cluster(e))
        clusters = self.cluster(clusters)
        return clusters

    def cluster(self, clusters):
        if not clusters or len(clusters) < 2:
            return clusters

        merge_occured = False
        new_clusters = []
        for c1 in clusters:
            if c1.merged:
                continue
            for c2 in clusters:
                if c2.merged:
                    continue
                if (c1 == c2):
                    continue
                if self.should_merge(c1, c2):
                    new_clusters.append(Cluster.merge(c1, c2))
                    c1.merged = True
                    c2.merged = True
                    merge_occured = True
                    break
            if not c1.merged:
                new_clusters.append(c1)
        if merge_occured:
            return self.cluster(new_clusters)  # recurse here
        return clusters

    def should_merge(self, c1, c2):
        if (c1.leader.label != c2.leader.label):
            return False

        # lilo:TODO - check leader entities similarity
        span1 = c1.leader
        span2 = c2.leader

        # compare entities using similarity function
        sim = span1.similarity(span2)
        if (sim >= SIMILARITY_TRESHOLD):
            return True

        # merge names, e.g: 'Thrun' and 'Sebastian Thrun'
        # but not 'Hillary Clinton' and 'Bill Clinton'
        if (c1.leader.label_ in ('PERSON', 'ORG')):
            set1 = set([t.lower_ for t in span1])
            set2 = set([t.lower_ for t in span2])
            set3 = set1.intersection(set2)
            if (len(set3) / (len(set1) + len(set2)) > 0.3):
                return True

        return False