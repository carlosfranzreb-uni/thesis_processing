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


def filter_vocab(vocab, remove_file, bottom=1, top=1000):
  """ Return a vocab where the entries that occur 'bottom' or less times are
  removed and also those that occur 'top' or more times. Entries that appear
  as many times as larger entries that contain it should also be removed, as
  they only make sense in their larger context. For example, if 'supervised'
  and 'supervised learning' both occur 100 times, 'supervised' should be
  removed. Also, if 'supervised' occurs 101 times it should also be removed,
  as it only occurs once without being in 'supervised learning'. The entries
  that should be removed are written to 'remove_file' to avoid losing
  progress if the program is terminated. 
  The file 'remove_file' may contain removed phrases. If it does, they 
  should be removed from the vocab before starting again. """
  remove = json.load(open(remove_file))
  filtered = {k: v for k, v in vocab.items() if v > bottom and v < top}
  logging.info(f'Vocab size after removing extrema: {len(filtered)}.')
  if len(remove) == 0:
    remove = [k for k, v in vocab.items() if v <= bottom or v >= top]
    json.dump(remove, open(remove_file, 'w'))
  else:
    logging.info(f'{len(remove)} phrases have already been removed.')
    filtered = {k: v for k, v in filtered.items() if k not in remove}
    logging.info(f'Vocab size after the last run: {len(filtered)}.')
    remove = []
    remove_file += '_1'
  groups = {}
  for entry, freq in filtered.items():
    if freq in groups:
      groups[freq].append(entry)
    else:
      groups[freq] = [entry]
  logging.info(f'Entries grouped by frequency. There are {len(groups)} groups.')
  logging.info(f'Checking for substrings that occur equally.')
  for key in groups.keys():
    logging.info(f'Checking group with frequency {key}.')
    group = groups[key]
    for i in range(len(group)):
      for j in range(len(group)):
        if i != j and is_included(group[i], group[j]):
          logging.info(
            f'Remove "{group[i]}". It is a substring of "{group[j]}".'
          )
          if group[i] not in remove:
            remove.append(group[i])
            json.dump(remove, open(remove_file, 'w'))
          break
  logging.info(f'Vocab size is now {len(filtered) - len(remove)}.')
  logging.info(f'Checking for substrings that occur once more.')
  for i in groups.keys():
    logging.info(f'Checking group with frequency {key}.')
    if i+1 in groups.keys():
      logging.info(f'A group with frequency {i+1} exists.')
      for entry in groups[i+1]:
        for other_entry in groups[i]:
          if is_included(entry, other_entry):
            logging.info(
              f'Remove "{entry}". It is a substring of "{other_entry}".'
            )
          if group[i] not in remove:
            remove.append(group[i])
            json.dump(remove, open(remove_file, 'w'))
          break
    else:
      logging.info(f'There is no group with frequency {i+1}.')
  logging.info(f'Vocab size is now {len(filtered) - len(remove)}.')
  for entry in remove:
    filtered.pop(entry)
  return filtered


def is_included(included, includes):
  """ Return True if the string 'included' is an n-gram that is part of
  'includes', a larger n-gram. The tokens of the smaller n-grams must be 
  part of the larger n-gram. Matching subwords such as 'selling' and 
  'counselling' should be avoided. """
  if includes[:len(included)+1] == included + ' ':  # match at the beginning
    return True
  elif includes[-len(included)-1:] == ' ' + included:  # match at the end
    return True
  elif f' {included} ' in includes:  # match in the middle
    return True
  return False


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


def main_filter(vocab_file, filtered_file, remove_file):
  start = int(time())
  logging.basicConfig(
    filename=f"logs/filter_vocab_{start}.log",
    format='%(asctime)s %(message)s',
    level=logging.INFO
  )
  vocab = json.load(open(vocab_file))
  logging.info(f'Starting to filter vocab "{vocab_file}".')
  logging.info(f'Starting size of the vocab: {len(vocab)}')
  filtered = filter_vocab(vocab, remove_file)
  logging.info('Filtering completed.')
  json.dump(filtered, open(filtered_file, 'w'))
  logging.info(f'Filtered vocab dumped to "{filtered_file}"')


if __name__ == "__main__":
  vocab_file = 'data/vocab/repo_vocab_1.json'
  filtered_file = 'data/vocab/repo_vocab_1_filtered.json'
  remove_file = 'data/vocab/repo_vocab_1_removed.json'
  main_filter(vocab_file, filtered_file, remove_file)
