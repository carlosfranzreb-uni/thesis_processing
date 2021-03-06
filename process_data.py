""" Process the file 'relevant_data.json', created by running the script
'retrieve_relevant_data.py' of the 'repository_analysis' repo. The processing
procedure is the same as for the vocabulary, to enable the comparison among
both sources. """


import json

from flair.data import Sentence
from flair.tokenization import SpacyTokenizer
from flair.models import SequenceTagger
from nltk.stem import WordNetLemmatizer

from create_vocab import process


class DataProcessor:
  def __init__(self, tokenizer, tagger, lemmatizer):
    self.tokenizer = tokenizer
    self.tagger = tagger
    self.lemmatizer = lemmatizer

  def process_data(self, data, func, dump_file):
    processed = {}
    for id, metadata in data.items():
      processed[id] = {}
      for text in ('title', 'abstract'):
        if metadata[text] is not None:
          processed[id][text] = func(metadata[text])
        else:
          processed[id][text] = None
    json.dump(processed, open(dump_file, 'w'))

  def process_text(self, text):
    return process(
      Sentence(text, use_tokenizer=self.tokenizer),
      self.tagger, self.lemmatizer
    )

  def tokenize_text(self, text):
    tokens = Sentence(text, use_tokenizer=self.tokenizer)
    return [token.text for token in tokens]


def process_subjects():
  tokenizer = SpacyTokenizer('en_core_web_sm')
  lemmatizer = WordNetLemmatizer()
  tagger = SequenceTagger.load('upos-fast')
  processor = DataProcessor(tokenizer, tagger, lemmatizer)
  subjects = json.load(open('data/openalex/articles.json', encoding='utf-8'))
  articles = {}
  for subject, article in subjects.items():
    articles[subject] = processor.process_text(article)
  print('Done')
  json.dump(
    articles,
    open('data/openalex/articles_processed.json', 'w', encoding='utf-8')
  )


if __name__ == '__main__':
  data = json.load(open('data/json/dim/all/improved_data.json'))
  tokenizer = SpacyTokenizer('en_core_web_sm')
  lemmatizer = WordNetLemmatizer()
  tagger = SequenceTagger.load('upos-fast')
  processor = DataProcessor(tokenizer, tagger, lemmatizer)
  # processor.process_data(data, processor.process_text, 'data/json/dim/all/data_lemmas.json')
  process_subjects()
