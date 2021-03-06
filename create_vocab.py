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


def remove_ngrams(vocab_file, dump_file):
  """ Given a vocab, remove all entries that comprise more than one word. """
  vocab = json.load(open(vocab_file))
  new_vocab = {}
  for entry in vocab:
    if ' ' not in entry:
      new_vocab[entry] = vocab[entry]
  json.dump(new_vocab, open(dump_file, 'w'))


if __name__ == "__main__":
  # start = int(time())
  # logging.basicConfig(
  #   filename=f"logs/vocab_{start}.log",
  #   format='%(asctime)s %(message)s',
  #   level=logging.INFO
  # )
  # data = json.load(open('data/json/dim/all/data.json'))
  # tokenizer = SpacyTokenizer('en_core_web_sm')
  # lemmatizer = WordNetLemmatizer()
  # tagger = SequenceTagger.load('upos-fast')
  # logging.info('About to create a vocabulary out of the repositories')
  # logging.info('Using the spacy tokenizer with the "en_core_web_sm" model.')
  # logging.info('Using the WordNetLemmatizer of NLTK.')
  # logging.info('Using the upos-fast model of flair for POS-tagging.')
  # logging.info('Extracting N-grams of up to length 4.')
  # vocab = create_vocab(data, tokenizer, tagger, lemmatizer, process)
  # json.dump(vocab, open(f'data/vocab/repo_vocab_{start}.json', 'w'))
  remove_ngrams(
    'data/vocab/repo_vocab_step_1.json',
    'data/vocab/repo_vocab_1grams.json'
  )
