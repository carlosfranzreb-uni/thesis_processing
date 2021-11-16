""" Store references between documents of our corpus as lists of IDs. """


import json


def relate_docs():
  relations = {}
  data = json.load(open('data/json/dim/all/improved_data.json'))
  for repo in ('depositonce', 'edoc', 'refubium'):
    refs = json.load(open(f'data/json/references/{repo}.json'))
    for id in refs.keys():
      relations[id] = []
      for ref in refs[id]:
        for doc_id in data.keys():
          if doc_id == id:
            continue
          if data[doc_id]['title'] in ref['raw_ref']:
            relations[id].append(doc_id)
            json.dump(relations, open('data/json/references/relations.json', 'w'))


if __name__ == '__main__':
  relate_docs()