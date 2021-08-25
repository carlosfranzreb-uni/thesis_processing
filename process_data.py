""" Process the file 'relevant_data.json', created by running the script
'retrieve_relevant_data.py' of the 'repository_analysis' repo. The processing
procedure is the same as for the vocabulary, to enable the comparison among
both sources. """


import json

from flair.data import Sentence
from flair.tokenization import SpacyTokenizer
from flair.models import SequenceTagger
from nltk.stem import WordNetLemmatizer

from create_vocab import process, filter


class DataProcessor:
  def __init__(self, tokenizer, tagger, lemmatizer):
    self.tokenizer = tokenizer
    self.tagger = tagger
    self.lemmatizer = lemmatizer

  def process_data(self, data, dump_file):
    processed = {}
    for id, metadata in data.items():
      processed[id] = {}
      if metadata['title'] is not None:
        processed[id]['title'] = self.process_text(metadata['title'])
      if metadata['abstract'] is not None:
        processed[id]['abstract'] = self.process_text(metadata['abstract'])
    json.dump(processed, open(dump_file, 'w'))

  def process_text(self, text):
    tokens = process(
      Sentence(text, use_tokenizer=self.tokenizer),
      self.tagger, self.lemmatizer
    )
    indexed_tokens = {w: idx for idx, w in enumerate(tokens)}
    filtered_tokens = filter(tokens)
    res = dict()
    for filtered_token in filtered_tokens:
      res[filtered_token] = indexed_tokens[filtered_token]
    return res


if __name__ == '__main__':
  data = json.load(open('data/json/dim/all/relevant_data.json'))
  tokenizer = SpacyTokenizer('en_core_web_sm')
  lemmatizer = WordNetLemmatizer()
  tagger = SequenceTagger.load('upos-fast')
  processor = DataProcessor(tokenizer, tagger, lemmatizer)
  processor.process_data(data, 'data/json/dim/all/data_processed.json')
