""" Functions related to the creation of the ERT of a referee. get_theses()
creates a file that maps theses (list of values) to referees (keys).
create_ert(these, sample_size) concatenates the SRTs of a sample of theses
from the given referee. """


import json
from random import sample


def get_referees():
  """ Retrieve the referees of the files in the 'data/processed' folder and
  dump them in a file with them as keys and a list of their theses as values."""
  referees = {}
  for repo in ('depositonce', 'edoc', 'refubium'):
    data = json.load(open(f'../data/processed/dim/{repo}.json'))
    for doc in data:
      if doc['type'][1] == 'thesis':
        for contributor in doc['authors']:
          if contributor[1] == 'referee':
            if contributor[0] not in referees:
              referees[contributor[0]] = []
            referees[contributor[0]].append(doc['id'])
  json.dump(referees, open('../data/json/dim/all/ert/referees.json', 'w'))


def get_erts():
  """ For each referee in 'referees' (the file created by get_referees()), call
  create_ert(). Dump the results in a file. """
  referees = json.load(open('../data/json/dim/all/ert/referees.json'))
  data = json.load(open('../data/json/dim/all/relevant_data.json'))
  erts = {referee: create_ert(ids, data) for referee, ids in referees.items()}
  json.dump(erts, open('../data/json/dim/all/ert/referee_erts.json', 'w'))


def create_ert(theses, data, sample_size=4):
  """ Given the theses of a venue and a sample size, concatenate the SRTs
  (i.e. title and abstract) of 'sample_size' random theses of the venue.
  Separate the texts of the theses with three slashes '///', so no ngrams
  are formed using tokens of different texts. Return the concantenated texts as
  well as a list with the IDs of the used theses. """
  if len(theses) <= sample_size:
    ids = theses
  else:
    ids = sample(theses, sample_size)
  ert = ''
  for id in ids:
    for text in data[id].values():
      if text is not None:
        ert += text + ' /// '
  return {'ert': ert, 'ids': ids}


if __name__ == "__main__":
  get_referees()
  get_erts()