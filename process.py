# -*- coding: utf-8 -*-

import json
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# List indexes for proposals and speeches
PROPOSALS = 0
SPEECHES = 1

congressmen = dict()
with open('data.json', 'r') as data_file:
    congressmen = json.load(data_file)

cm_raw_texts = dict()  # Here we will have an array 0=prop 1=speech
for cm in congressmen:
    cm_raw_texts[cm] = []
    cm_raw_texts[cm].append(", ".join(kw.encode('utf-8') for kw in congressmen[cm]['proposals']))
    cm_raw_texts[cm].append(", ".join(kw.encode('utf-8') for kw in congressmen[cm]['speeches']))

cm_bags_of_words = dict()
for cm in congressmen:
    cm_bags_of_words[cm] = dict()
    cm_bags_of_words[cm]['proposals'] = dict()
    cm_bags_of_words[cm]['speeches'] = dict()
    vectorizer = CountVectorizer(tokenizer=lambda x: x.split(', ')) #  tokenizer to get sentences between commas instead of words
    X = vectorizer.fit_transform(cm_raw_texts[cm])
    for word, count in vectorizer.vocabulary_.iteritems():
        if(X.toarray()[PROPOSALS][count] > 0):
            cm_bags_of_words[cm]['proposals'][word] = X.toarray()[PROPOSALS][count]
        if(X.toarray()[SPEECHES][count] > 0):
            cm_bags_of_words[cm]['speeches'][word] = X.toarray()[SPEECHES][count]
    congressmen[cm]['coherence'] = cosine_similarity(X.toarray())[0][1] #this is the cosine
    congressmen[cm]['proposals'] = cm_bags_of_words[cm]['proposals']
    congressmen[cm]['speeches'] = cm_bags_of_words[cm]['speeches']

# Using json.dump raises encoding problems here, so we are using json.dumps instead
with open('final.json', 'w') as outfile:
    outfile.write(json.dumps(congressmen, ensure_ascii=False).encode('utf-8'))
