""" Yield the metadata information of the relevant documents. Their IDs are
in data/json/dim/all/relevant_ids.json and the metadata is in data/xml/dim. """


import os
import json
from xml.etree import ElementTree as ET
from string import Template
import logging


oai = '{http://www.openarchives.org/OAI/2.0/}'
oai_dc = '{http://www.openarchives.org/OAI/2.0/oai_dc/}'
dc = '{http://purl.org/dc/elements/1.1/}'
dim = '{http://www.dspace.org/xmlns/dspace/dim}'


class DataLoader:
  def __init__(self):
    self.ids_template = Template('data/json/dim/$repo/relevant_ids.json')
    self.folder = 'data/xml/dim'
    self.repos = ['depositonce', 'edoc', 'refubium']
  
  def load_data(self):
    """ Iterate over the files. Yield the records whose IDs are in the list
    of relevant IDs. """
    for repo in self.repos:
      ids = json.load(open(self.ids_template.substitute(repo=repo)))
      for filename in os.listdir(f'{self.folder}/{repo}'):
        root = ET.parse(f'{self.folder}/{repo}/{filename}').getroot()
        for record in root.find(f'{oai}ListRecords'):
          header = record.find(f'{oai}header')
          if record.tag == f'{oai}resumptionToken' or 'status' in \
              header.attrib and header.attrib['status'] == 'deleted':
            continue
          id = header.find(f'{oai}identifier').text
          if id in ids:
            yield self.process(id, record.find(f'{oai}metadata').find(f'{dim}dim'))
  
  def process(self, id, metadata):
    """ Return the id, title and abstract of the record as a tuple. """
    title, abstract = None, None
    for f in metadata.findall(f'{dim}field'):
      if 'qualifier' in f.attrib and f.attrib['qualifier'] == 'abstract':
        if 'lang' in f.attrib and f.attrib['lang'] in ('en', 'eng'):
          abstract = f.text
      if 'element' in f.attrib and f.attrib['element'] == 'title':
        if 'lang' in f.attrib:
          if f.attrib['lang'] in ('en', 'eng'):
            title = f.text
        else:
          title = f.text
      if abstract is not None and title is not None:
        break
    return (id, title, abstract)

def check_data():
  """ Log the elements that are missing the title, abstract or both. """
  logging.basicConfig(
    filename=f"logs/check_data.log",
    level=logging.INFO
  )
  no_title, no_abstract, no_both = 0, 0, 0
  loader = DataLoader()
  for id, title, abstract in loader.load_data():
    if title is None and abstract is None:
      no_both += 1
      logging.info(f'{id} has no title and no abstract.')
    else:
      if title is None:
        no_title += 1
        logging.info(f'{id} has no title.')
      if abstract is None:
        no_abstract += 1
        logging.info(f'{id} has no abstract.')
  logging.info('--- DONE ---')
  logging.info(f'{no_both} records do not have title and abstract.')
  logging.info(f'{no_title} records do not have title.')
  logging.info(f'{no_abstract} records do not have abstract.')


def save_data(dump_file):
  """ Save the data into a file as a dictionary: id -> title, abstract. """
  data = []
  loader = DataLoader()
  for id, title, abstract in loader.load_data():
    if not (title is None and abstract is None):
      data.append({'id': id, 'title': title, 'abstract': abstract})
  json.dump(data, open(dump_file, 'w'))

if __name__ == "__main__":
  save_data('data/json/dim/all/data.json')
