""" Retrieve the publishing venue of each publication. """


from xml.etree import ElementTree as ET
import json
import os


oai = '{http://www.openarchives.org/OAI/2.0/}'
oai_dc = '{http://www.openarchives.org/OAI/2.0/oai_dc/}'
dc = '{http://purl.org/dc/elements/1.1/}'
didl = '{urn:mpeg:mpeg21:2002:02-DIDL-NS}'
dim = '{http://www.dspace.org/xmlns/dspace/dim}'


def get_record(id, repo):
  """ Retrieve a record given its ID and the folder with the XML files it is
  included in. """
  folder = f'data/xml/dim/{repo}'
  for filename in os.listdir(folder):
    root = ET.parse(f'{folder}/{filename}').getroot()
    for record in root.find(f'{oai}ListRecords'):
      header = record.find(f'{oai}header')
      try:
        this_id = header.find(f'{oai}identifier').text
        if this_id == id:
          return record
      except AttributeError:
        continue


def get_venue(id, publication_type, repo):
  """ Return the venue included in the given record. The venue type differs
  depending on the publication type. """
  if repo == 'edoc':
    qualifier = 'container-title'
  else:
    if publication_type == 'bookpart':
      qualifier = 'booktitle'
    elif publication_type in ('conferenceobject', 'conferenceproceedings'):
      qualifier = 'proceedingstitle'
    else:
      qualifier = 'journaltitle'
  record = get_record(id, repo)
  metadata = record.find(f'{oai}metadata')
  if metadata is None:
    return None
  for f in metadata.find(f'{dim}dim').findall(f'{dim}field'):
    if 'qualifier' in f.attrib and f.attrib['qualifier'] == qualifier:
      return f.text
  for f in metadata.find(f'{dim}dim').findall(f'{dim}field'):
    if 'element' in f.attrib and f.attrib['element'] == 'series':
      if 'qualifier' in f.attrib and f.attrib['qualifier'] == 'name':
        return f.text
    elif 'qualifier' in f.attrib and f.attrib['qualifier'] == 'container-erstkat-id':
      return f.text
    elif 'qualifier' in f.attrib and f.attrib['qualifier'] == 'container-erstkatid':
      return f.text
  if repo == 'depositonce':
    for f in metadata.find(f'{dim}dim').findall(f'{dim}field'):
      if 'element' in f.attrib and f.attrib['element'] == 'bibliograhicCitation':
        if 'qualifier' in f.attrib and f.attrib['qualifier'] == 'journaltitle':
          return f.text
  elif repo == 'refubium':
    for f in metadata.find(f'{dim}dim').findall(f'{dim}field'):
      if 'element' in f.attrib and f.attrib['element'] == 'bibliographicCitation':
        return f.text.split('.')[0]
  return None


def get_venues():
  """ Return a mapping of IDs to venues. 'relevant_types' is a mapping of IDs
  to publication types. Theses don't have venues and are thus not included. """
  mapping = dict()
  for repo in ['depositonce', 'edoc', 'refubium']:
    relevant_types = json.load(open(f'data/json/dim/{repo}/relevant_types.json'))
    for id, doc_type in relevant_types.items():
      if 'thesis' not in doc_type:
        mapping[id] = get_venue(id, doc_type, repo)
  json.dump(mapping, open(f'data/json/dim/all/relevant_venues.json', 'w'))


def discover_fields():
  """ For every type of document, retrieve the qualifiers that have
  'bibliographicCitation' as element. This is important to know which
  qualifiers to look at when searching for the venue of a publication. """
  fields = {'depositonce': {}, 'edoc': {}, 'refubium': {}}
  for repo in fields:
    folder = f'data/xml/dim/{repo}'
    for filename in os.listdir(folder):
      root = ET.parse(f'{folder}/{filename}').getroot()
      for record in root.find(f'{oai}ListRecords'):
        qualifiers = []
        metadata = record.find(f'{oai}metadata')
        if metadata is None:
          continue
        for f in metadata.find(f'{dim}dim').findall(f'{dim}field'):
          if 'element' in f.attrib and \
              f.attrib['element'] == 'bibliographicCitation':
            if 'qualifier' in f.attrib:
              qualifiers.append(f.attrib['qualifier'])
          elif 'element' in f.attrib and 'qualifier' not in f.attrib \
              and f.attrib['element'] == 'type':
            doc_type = f.text
        if doc_type in fields[repo]:
          fields[repo][doc_type] = list(set(fields[repo][doc_type] + qualifiers))
        else:
          fields[repo][doc_type] = qualifiers
  json.dump(fields, open('data/json/dim/all/citation_qualifiers.json', 'w'))


def test_venues():
  ids = ['oai:refubium.fu-berlin.de:fub188/18598', 'oai:refubium.fu-berlin.de:fub188/19810']
  mapping = dict()
  repo = 'test'
  for id in ids:
    mapping[id] = get_venue(id, 'article', repo)
  print(mapping)


if __name__ == "__main__":
  get_venues()
