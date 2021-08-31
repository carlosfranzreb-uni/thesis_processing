import json
from xml.etree import ElementTree as ET
import os


oai = '{http://www.openarchives.org/OAI/2.0/}'
oai_dc = '{http://www.openarchives.org/OAI/2.0/oai_dc/}'
dc = '{http://purl.org/dc/elements/1.1/}'
didl = '{urn:mpeg:mpeg21:2002:02-DIDL-NS}'
dim = '{http://www.dspace.org/xmlns/dspace/dim}'


def compute_frequency(relevant, field_name, field_type):
  """ Given a mapping of IDs to document types, compute how often the
  given field is occupied. """
  doc_types = {'depositonce': {}, 'edoc': {}, 'refubium': {}}
  seen_values = {'depositonce': [], 'edoc': [], 'refubium': []}
  for repo in doc_types:
    folder = f'data/xml/dim/{repo}'
    for filename in os.listdir(folder):
      root = ET.parse(f'{folder}/{filename}').getroot()
      for record in root.find(f'{oai}ListRecords'):
        header = record.find(f'{oai}header')
        try:
          id = header.find(f'{oai}identifier').text
        except AttributeError:
          continue
        if id in relevant:
          if relevant[id] in doc_types[repo]:
            doc_types[repo][relevant[id]]['total'] += 1
          else:
            doc_types[repo][relevant[id]] = {
              'total': 1, 'occurrences': 0, 'distinct-values': 0
            }
          metadata = record.find(f'{oai}metadata')
          if metadata is None:
            continue
          for f in metadata.find(f'{dim}dim').findall(f'{dim}field'):
            if field_type in f.attrib and \
                f.attrib[field_type] == field_name:
              doc_types[repo][relevant[id]]['occurrences'] += 1
              if f.text in seen_values[repo]:
                doc_types[repo][relevant[id]]['distinct-values'] += 1
              else:
                seen_values[repo].append(f.text)
  json.dump(doc_types, open(f'data/json/dim/all/{field_name}.json', 'w'))


if __name__ == '__main__':
  relevant_types = json.load(open(f'data/json/dim/all/relevant_types.json'))
  field_name = 'container-erstkatid'
  field_type = 'qualifier'
  compute_frequency(relevant_types, field_name, field_type)