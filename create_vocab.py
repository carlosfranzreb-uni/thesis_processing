""" Create the vocabulary. The vocab is a dictionary containing the words
and phrases as keys and their number of occurrences as values. """


import json
from string import punctuation
from collections import Counter
from xml.etree import ElementTree as ET
from flair.data import Sentence
from flair.tokenization import SpacyTokenizer
from flair.models import SequenceTagger
from nltk.stem import WordNetLemmatizer
from nltk.util import ngrams
from nltk.corpus import stopwords, wordnet

from load_data import DataLoader


def create_vocab(data, tokenizer, processor=lambda x: x, max_ngrams=4):
  vocab = Counter()
  total = 0
  for record in data:
    phrases = []
    if record['title'][-1] == '.':
      text = f"{record['title']} {record['abstract']}"
    else:
      text = f"{record['title']}. {record['abstract']}"
    tokens = processor(Sentence(text, use_tokenizer=tokenizer))
    for n in range(2, max_ngrams+1):
      phrases += [' '.join(g) for g in ngrams(tokens, n)]
    vocab.update(filter(tokens + phrases))
  return vocab


def process(sentence):
  """ Given a Sentence object, lower-case and lemmatize the words. """
  tagger = SequenceTagger.load('upos')
  lemm = WordNetLemmatizer()
  tagger.predict(sentence)
  tag_dict = {
    'ADJ': wordnet.ADJ,
    'NOUN': wordnet.NOUN,
    'VERB': wordnet.VERB,
    'ADV': wordnet.ADV
  }
  lemmas = []
  for token in sentence:
    if token.labels[0].value in tag_dict:
      lemmas.append(lemm.lemmatize(
        token.text.lower(), tag_dict[token.labels[0].value])
      )
    else:
      lemmas.append(token.text.lower())
  return lemmas

def filter(phrases):
  """ Filter out phrases that contain a punctuation sign or single words
  that are a punctuation signs or stopwords. """
  filtered = []
  signs = ['!', '?', '.', ',']
  exclude = stopwords.words('english') + [c for c in punctuation]
  for p in phrases:
    if p not in exclude:
      keep = True
      for s in signs:
        if s in p:
          keep = False
      if keep is True:
        filtered.append(p)
  return filtered


if __name__ == "__main__":
  data = json.load(open('data/json/dim/all/data.json'))
  tokenizer = SpacyTokenizer('en_core_web_sm')
  vocab = create_vocab(data, tokenizer, process)
  json.dump(vocab, open('data/vocab/repo_vocab.json'))
