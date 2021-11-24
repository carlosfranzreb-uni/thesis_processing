""" Compute the SentencePiece vocabulary of our corpus to compare it to the
one of SciBERT. SciVOCAB has 30k terms, same as BERT. """


import json
import sentencepiece as spm
from nltk import sent_tokenize


def create_input():
  """ Input of the trainer must be a TXT file with one sentence of raw text
  in each line. """
  with open('data/txt/raw_text_uncased.txt', 'w', encoding='utf-8') as f:
    for line in load_data():
      f.write(line + '\n')


def load_data():
  """ Lazy load the sentences of all titles and abstracts. """
  all_data = json.load(open(
    'data/json/dim/all/relevant_data.json',
    encoding='utf-8'
  ))
  for data in all_data.values():
    for text in data.values():
      if text is not None:
        for sentence in sent_tokenize(text):
          yield sentence.lower()


def train_sentencepiece():
  """ Train the SP model with the above created data file. """
  spm.SentencePieceTrainer.train(
    input='data/txt/raw_text_uncased.txt',
    model_prefix='data/sentencepiece/bpe_uncased',
    vocab_size=30000,
    model_type='bpe'
  )


if __name__ == "__main__":
  train_sentencepiece()