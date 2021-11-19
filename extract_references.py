""" The PDFs can be found in the DIDL metadata format for depositonce and edoc
and XOAI for refubium. The URL of the PDF can then be passed to 'refextract',
which extracts the references.  """


import xml.etree.ElementTree as ET
import json
import os
import logging
from time import time
from pathlib import Path

import requests
from refextract import extract_references_from_string
from tika import parser


oai = '{http://www.openarchives.org/OAI/2.0/}'
didl = '{urn:mpeg:mpeg21:2002:02-DIDL-NS}'
xoai = '{http://www.lyncode.com/xoai}'
base_urls = {
  'depositonce': 'https://depositonce.tu-berlin.de/oai/request',
  'edoc': 'https://edoc.hu-berlin.de/oai/request',
  'refubium': 'https://refubium.fu-berlin.de/oai/request'
}


def extract_refs(funcs):
  """ Extract references of all relevant docs and store them in a dict. 'funcs'
  stores the functions that should be used to retrieve PDFs for each repo. """
  for repo in ['depositonce', 'edoc', 'refubium']:
    logging.info(f'Starting with repo {repo}')
    res = {}
    ids = json.load(open(f'data/json/dim/{repo}/relevant_ids.json'))
    for id in ids:
      filename = funcs[repo](base_urls[repo], id)
      if filename is not None:
        if parse_pdf(filename):
          res[id] = get_references(filename)
    json.dump(res, open(f'data/json/references/{repo}.json', 'w'))


def extract_missing_refs(missing, funcs):
  res = {}
  for repo in missing.keys():
    for id in missing[repo]:
      filename = funcs[repo](base_urls[repo], id)
      if filename is not None:
        if parse_pdf(filename):
          res[id] = get_references(filename)
  json.dump(res, open(f'data/json/references/missing_references.json', 'w'))


def get_didl_pdf(base_url, id):
  """ Download the PDF found in the metadata in DIDL format. """
  filename = id.split('/')[-1]
  req = f'{base_url}?verb=GetRecord&identifier={id}&metadataPrefix=didl'
  try:
    record = ET.fromstring(requests.get(req).text)
    pdf_url = record.find(f'.//{didl}Component/{didl}Resource').attrib['ref']
    pdf_res = requests.get(pdf_url)
    f = Path(f'data/pdf/{filename}.pdf')
    f.write_bytes(pdf_res.content)
    logging.info(f'PDF file of {filename} downloaded.')
    return filename
  except Exception as exc:
    logging.error(exc)
    return None


def get_xoai_pdf(base_url, id):
  """ Download the PDF found in the metadata in XOAI format. """
  filename = id.split('/')[-1]
  try:
    req = f'{base_url}?verb=GetRecord&identifier={id}&metadataPrefix=xoai'
    record = ET.fromstring(requests.get(req).text)
    for bundle in record.findall(f'.//{xoai}element[@name="bundle"]'):
      if bundle.find(f'.//{xoai}field[@name="name"]').text == 'ORIGINAL':
        pdf_url = bundle.find(f'.//{xoai}field[@name="url"]').text
        pdf_res = requests.get(pdf_url)
        f = Path(f'data/pdf/{filename}.pdf')
        f.write_bytes(pdf_res.content)
        logging.info(f'PDF file of {filename} downloaded.')
        return filename
  except Exception as exc:
    logging.error(exc)
    return None


def parse_pdf(filename):
  """ Extract the text of the PDF and store it in a TXT file. Delete the PDF
  file afterwards. Return True if the PDF was parsed. else False."""
  try:
    pdf_file = f'data/pdf/{filename}.pdf'
    pdf = parser.from_file(pdf_file)
    if pdf["content"] is not None:
      with open(f'data/txt/{filename}.txt', 'w', encoding='utf8') as f:
        f.write(pdf["content"])
      os.remove(pdf_file)
      logging.info(f'TXT file of {filename} created.')
      return True
  except requests.exceptions.ReadTimeout:
    logging.error(f"Parsing of {filename} failed.")
    return False


def get_references(filename):
  """ Return the references of the TXT document and remove the TXT file. """
  txt_file = f'data/txt/{filename}.txt'
  text = open(txt_file).read()
  os.remove(txt_file)
  return extract_references_from_string(text, is_only_references=False)


if __name__ == '__main__':
  logging.basicConfig(
    filename=f"logs/extractrefs_missing_{str(int(time()))}.log",
    format='%(asctime)s %(message)s',
    level=logging.INFO
  )
  pdf_retrieval_funcs = {
    'depositonce': get_didl_pdf,
    'edoc': get_didl_pdf,
    'refubium': get_xoai_pdf
  }
  missing = json.load(open('data/json/references/missing.json'))
  extract_missing_refs(missing, pdf_retrieval_funcs)