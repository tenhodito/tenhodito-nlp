# -*- coding: utf-8 -*-

import json
import logging
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

LOG_FILE = 'word-processing.log'
logging.basicConfig(filename=LOG_FILE, level=logging.WARNING)

def tokenizer(keywords):
    """
    tokenizer to get sentences between commas instead of words
    """
    tokens = keywords.split(', ')
    tokens = filter(lambda x: not x.isspace(), tokens)
    tokens = filter(lambda x: len(x) > 0, tokens)
    return tokens

# List indexes for proposals and speeches
PROPOSALS = 0
SPEECHES = 1

congressmen = dict()
with open('data.json', 'r') as data_file:
    congressmen = json.load(data_file)

cm_raw_texts = dict()
for cm in congressmen:
    cm_raw_texts[cm] = []  # list: [0] for prop [1] for speech
    cm_raw_texts[cm].append(", ".join(kw.encode('utf-8') for kw in congressmen[cm]['proposals']))
    cm_raw_texts[cm].append(", ".join(kw.encode('utf-8') for kw in congressmen[cm]['speeches']))

cm_bags_of_words = dict()
for cm in congressmen:
    cm_bags_of_words[cm] = dict()
    cm_bags_of_words[cm]['proposals'] = dict()
    cm_bags_of_words[cm]['speeches'] = dict()
    vectorizer = CountVectorizer(tokenizer=tokenizer)
    try:
        vector = vectorizer.fit_transform(cm_raw_texts[cm])
        for word, count in vectorizer.vocabulary_.iteritems():
            if(vector.toarray()[PROPOSALS][count] > 0):
                cm_bags_of_words[cm]['proposals'][word] = vector.toarray()[PROPOSALS][count]
            if(vector.toarray()[SPEECHES][count] > 0):
                cm_bags_of_words[cm]['speeches'][word] = vector.toarray()[SPEECHES][count]
        # The lists indexes point to the calculated cosine
        congressmen[cm]['coherence'] = cosine_similarity(vector.toarray())[0][1]
    except ValueError as e:
        logging.warning(e)
    congressmen[cm]['proposals'] = cm_bags_of_words[cm]['proposals']
    congressmen[cm]['speeches'] = cm_bags_of_words[cm]['speeches']

# json.dump raises encoding problems here: use json.dumps instead
with open('final.json', 'w') as outfile:
    outfile.write(json.dumps(congressmen, ensure_ascii=False).encode('utf-8'))
