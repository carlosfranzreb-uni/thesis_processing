""" Create the vocabulary. The vocab is a dictionary containing the words
and phrases as keys and their number of occurrences as values. Even if a
word or phrase appears multiple times in a document, it is counted only
once. This number illustrates how many documents contain a word/phrase. """


import json
from string import punctuation
from collections import Counter
import logging
from time import time

from flair.data import Sentence
from flair.tokenization import SpacyTokenizer
from flair.models import SequenceTagger
from nltk.stem import WordNetLemmatizer
from nltk.util import ngrams
from nltk.corpus import stopwords, wordnet


N_DOCS = 29336  # no. of docs, as seen in repo_vocab_1.log


def create_vocab(data, tokenizer, tagger, lemmatizer,
    processor=lambda x,y,z: x, max_ngrams=4):
  vocab = Counter()
  processed, total = 0, len(data)
  for record in data:
    processed += 1
    phrases = []
    if record['title'] is None:
      if record['abstract'] is None:
        logging.info(f"Empty record: {record['id']} - {processed}/{total}.")
        continue
      else:
        text = record['abstract']
    elif record['abstract'] is None:
      text = record['title']
    else:
      if record['title'][-1] == '.':
        text = f"{record['title']} {record['abstract']}"
      else:
        text = f"{record['title']}. {record['abstract']}"
    tokens = processor(
      Sentence(text, use_tokenizer=tokenizer),
      tagger, lemmatizer
    )
    for n in range(2, max_ngrams+1):
      phrases += [' '.join(g) for g in ngrams(tokens, n)]
    vocab.update(filter(tokens + phrases))
    logging.info(f"Processed {record['id']} - {processed}/{total}.")
  return vocab


def process(sentence, tagger, lemmatizer):
  """ Given a Sentence object, lower-case and lemmatize the words. """
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
      lemmas.append(lemmatizer.lemmatize(
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
      if keep is True and p not in filtered:
        filtered.append(p)
  return filtered


def filter_vocab(vocab, bottom=1, top=int(.8*N_DOCS)):
  """ Return a vocab where the entries that occur 'bottom' or less times are
  removed and also those that occur 'top' or more times. Entries that appear
  as many times as larger entries that contain it should also be removed, as
  they only make sense in their larger context. For example, if 'supervised'
  and 'supervised learning' both occur 100 times, 'supervised' should be
  removed. Also, if 'supervised' occurs 101 times it should also be removed,
  as it only occurs once without being in 'supervised learning'. """
  filtered = {k: v for k, v in vocab.items() if v > bottom and v < top}
  groups = {}
  for entry, freq in filtered.items():
    if freq in groups:
      groups[freq].append(entry)
    else:
      groups[freq] = [entry]
  remove = set()
  for group in groups.values():  # check for substring occuring equally
    for i in range(len(group)):
      for j in range(len(group)):
        if i != j and group[i] in group[j]:
          remove.add(group[i])
  for i in groups.keys():  # check for substring occuring once more
    if i+1 in groups.keys():
      for entry in groups[i+1]:
        for other_entry in groups[i]:
          if entry in other_entry:
            remove.add(entry)
  for entry in remove:
    filtered.pop(entry)
  return filtered


def main_create():
  start = int(time())
  logging.basicConfig(
    filename=f"logs/vocab_{start}.log",
    format='%(asctime)s %(message)s',
    level=logging.INFO
  )
  data = json.load(open('data/json/dim/all/data.json'))
  tokenizer = SpacyTokenizer('en_core_web_sm')
  lemmatizer = WordNetLemmatizer()
  tagger = SequenceTagger.load('upos-fast')
  logging.info('About to create a vocabulary out of the repositories')
  logging.info('Using the spacy tokenizer with the "en_core_web_sm" model.')
  logging.info('Using the WordNetLemmatizer of NLTK.')
  logging.info('Using the upos-fast model of flair for POS-tagging.')
  logging.info('Extracting N-grams of up to length 4.')
  vocab = create_vocab(data, tokenizer, tagger, lemmatizer, process)
  json.dump(vocab, open(f'data/vocab/repo_vocab_{start}.json', 'w'))


def main_filter(vocab_file, filtered_file):
  vocab = json.load(open(vocab_file))
  filtered = filter_vocab(vocab)
  json.dump(filtered, open(filtered_file, 'w'))


if __name__ == "__main__":
  vocab_file = ''
  filtered_file = ''
  main_filter(vocab_file, filtered_file)
