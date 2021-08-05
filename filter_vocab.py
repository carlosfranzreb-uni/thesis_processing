""" Once all words and n-grams have been extracted from the corpus, we use
these functions to filter out irrelevant words. We do so in four steps.
1. Remove entries that occur either too seldom or too often.  Per default
  we remove words that occur either once or more than a thousand times.
2. Remove entries that occur as often as larger ones that contain them, e.g.
  remove 'supervised' if it occurs as many times as 'supervised learning'.
3. Remove entries that occur once more than larger ones that contain them. 
  The same example as in step 2 applies. 'supervised' would only appear once
  alone and would be removed because it occurs too seldom.
4. Remove entries that either never occur alone or only once. For example, if
  'learning' occurs 10 times, 'supervised learning' occurs 6 times and 
  'unsupervised learning' occurs 4 times, 'learning' should be removed. 

In the last three steps it is important to match only token-wise and not in
terms of strings. The latter would remove 'selling' because it matches with 
'counselling'. """


import json
import logging
from time import time
from multiprocessing import Pool
from sys import getsizeof


class VocabFilterer:
  def __init__(self, vocab_file, bottom=1, top=1000):
    logging.basicConfig(
      filename=f"logs/filter_vocab_{int(time())}.log",
      format='%(asctime)s %(message)s',
      level=logging.INFO
    )
    self.root_name = vocab_file[:-5]
    self.vocab = json.load(open(vocab_file))
    self.remove = []  # stores the entries to be removed in each step.
    self.bottom = bottom
    self.top = top

  def filter(self):
    """ Dump a filtered vocabulary starting with the one in 'vocab_file' by
    executing the four steps explained in the docstring. Each is performed by a
    different function. After each step, an intermediate result is saved, named
    as 'vocab_file' and the step that was just performed appended to it. Store
    also the removed entries in each step. """
    logging.info(f'Starting to filter vocab "{self.root_name}".')
    logging.info(f'Starting size of the vocab: {len(self.vocab)}')
    self.step_1()
    self.step_2()
    self.step_3()
    self.vocab = self.step_4()
  
  def step_1(self):
    """ Remove entries that occur 'bottom' or less times and entries that occur
    'top' or more times. Store those entries as a dictionary with two keys
    '{bottom}_or_less' and '{top}_or_more'. """
    removed = {
      f'{self.bottom}_or_less': [
        k for k, v in self.vocab.items() if v <= self.bottom
      ],
      f'{self.top}_or_more': [k for k, v in self.vocab.items() if v >= self.top]
    }
    self.vocab = {
      k: v for k, v in self.vocab.items() if v > self.bottom and v < self.top
    }
    logging.info(f'Vocab size after removing extrema: {len(self.vocab)}.')
    logging.info(f'Bottom extrema: {len(removed[f"{self.bottom}_or_less"])}.')
    logging.info(f'Top extrema: {len(removed[f"{self.top}_or_more"])}.')
    self.dump(removed, '_step_1_removed')
    self.dump(self.vocab, '_step_1')

  def step_2(self):
    """ Remove entries that occur as often as larger ones that contain them by
    using 'groups', where the entries are grouped by frequency. Store
    the removed words."""
    logging.info(f'Checking for substrings that occur equally.')
    for freq in range(self.bottom+1, self.top):
      logging.info(f'Checking entries with frequency {freq}.')
      for entry in self.iter_group(freq):
        self.remove += self.substring_of_group(entry, freq)
      self.remove_entries(2)
  
  def step_3(self):
    """ Remove entries that occur once more than larger ones that contain them
    by using 'groups', where the entries are grouped by frequency. Store
    the removed words. """
    logging.info(f'Checking for substrings that occur once more.')
    for freq in range(self.bottom+1, self.top-1):
      logging.info(f'Checking entries with frequency {freq}.')
      for entry in self.iter_group(freq):
        self.remove += self.substring_of_group(entry, freq+1)
      self.remove_entries(3)

  def step_4(self):
    """ Remove entries that either never occur alone or only once. For each
    entry, find all the entries that include it. If the sum of their frequences
    equals the frequency of the entry or is off by one (i.e. one less), remove
    the entry. """
    for entry, freq in self.vocab.items():
      self.remove += self.substring_of_more(entry, freq)
    self.remove_entries(4)

  def create_groups(self):
    """ Group the entries of the vocabulary by frequency. Return a dict
    with the frequency as key and a list of its entries as value. """
    groups = {}
    for entry, freq in self.vocab.items():
      if freq in groups:
        groups[freq].append(entry)
      else:
        groups[freq] = [entry]
    logging.info(
      f'Entries grouped by frequency. There are {len(groups)} groups.'
    )
    return groups
  
  def iter_group(self, freq):
    """ Lazily iterate over the entries with the given frequency. """
    for entry, this_freq in self.vocab.items():
      if this_freq == freq:
        yield entry

  def substring_of_group(self, entry, freq):
    """ If the entry is contained in the given group, add it to
    self.remove. """
    for other_entry in self.iter_group(freq):
      if is_included(entry, other_entry):
        logging.info(
          f'Remove "{entry}". It is included in "{other_entry}".'
        )
        return [entry]
    return []
  
  def substring_of_more(self, entry, freq):
    """ Add the frequencies of the entries of which 'entry' is a substring.
    If the sum equals the frequency of 'entry' or is one less, add 'entry' to
    'self.remove' """
    included_sum = 0
    for other_entry, other_freq in self.vocab.items():
      if entry != other_entry and is_included(entry, other_entry):
        included_sum += other_freq
        if included_sum + 1 >= freq:
          return [entry]
    return []

  def remove_entries(self, step_nr):
    """ Remove the entries present in the list 'self.remove' from the vocab.
    Store the removed entries and the resulting vocab with the given step_nr.
    Empty the self.remove array at the end."""
    for entry in self.remove:
      if entry is not None:
        del self.vocab[entry]
    logging.info(f'Vocab size is now {len(self.vocab)}.')
    self.dump(self.remove, f'_step_{step_nr}_removed')
    self.dump(self.vocab, f'_step_{step_nr}')
    self.remove = []

  def dump(self, obj, appendix):
    """ Dump the JSON object 'obj' with the root name plus the appendix
    as the name."""
    json.dump(
      obj, 
      open(f'{self.root_name}{appendix}.json', 'w', encoding='utf-8')
    )


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


def remove(arr, idx):
  """ Return the given arr without the element on the given index. Do so
  without actually removing the element from the array. """
  if idx == 0:
    return arr[1:]
  elif idx == len(arr) - 1:
    return arr[:idx]
  else:
    return arr[:idx] + arr[idx+1:]


if __name__ == "__main__":
  filename = 'data/vocab/repo_vocab.json'
  filename_test = 'data/vocab/test/test_vocab.json'
  filterer = VocabFilterer(filename)
  try:
    filterer.filter()
  except Exception as exc:
    logging.error(exc)
