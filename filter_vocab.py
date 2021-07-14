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
import os
import logging
from time import time


def filter_vocab(vocab_file, bottom=1, top=1000):
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
  vocab = json.load(open(vocab_file))
  logging.info(f'Starting size of the vocab: {len(vocab)}')
  remove_file = f'{vocab_file[:-5]}_removed.json'
  if os.path.isfile(remove_file):
    remove = json.load(open(remove_file))
  else:
    remove = []
  filtered = {k: v for k, v in vocab.items() if v > bottom and v < top}
  logging.info(f'Vocab size after removing extrema: {len(filtered)}.')
  if len(remove) == 0:
    remove = [k for k, v in vocab.items() if v <= bottom or v >= top]
    json.dump(remove, open(f'{vocab_file[:-5]}_extrema.json', 'w'))
  else:
    logging.info(f'{len(remove)} phrases have already been removed.')
    filtered = {k: v for k, v in filtered.items() if k not in remove}
    logging.info(f'Vocab size after the last run: {len(filtered)}.')
    remove_file += '_1'
  remove = []
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


def main_filter(vocab_file):
  start = int(time())
  logging.basicConfig(
    filename=f"logs/filter_vocab_{start}.log",
    format='%(asctime)s %(message)s',
    level=logging.INFO
  )
  logging.info(f'Starting to filter vocab "{vocab_file}".')
  filtered = filter_vocab(vocab_file)
  logging.info('Filtering completed.')
  filtered_file = f'{vocab_file[:-5]}_filtered.json'
  json.dump(filtered, open(filtered_file, 'w'))
  logging.info(f'Filtered vocab dumped to "{filtered_file}"')


def test_filter():
  """ Test the filtering procedure with the test vocabulary. """
  vocab_file = 'data/vocab/test_vocab.json'
  main_filter(vocab_file)


if __name__ == "__main__":
  # main_filter('data/vocab/repo_vocab_1.json')
  test_filter()