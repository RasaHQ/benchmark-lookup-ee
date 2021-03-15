import requests
import nltk
import re
import argparse
import sys
from lxml import html

parser = argparse.ArgumentParser(description='Grab text from a Wikipedia page.')
parser.add_argument('--title', default='History of tennis',
                    help='Wikipedia file to download. default: History of tennis. Warning: this is case-sensitive')
parser.add_argument('--out', default='data/tennis_test.txt',
                    help='Output file. default: \'data/tennis_test.txt\'')
args = parser.parse_args()

nltk.download('punkt', download_dir='data')
nltk.data.path.append('data')
response = requests.get(
    'https://en.wikipedia.org/w/api.php',
    params={
        'action': 'parse',
        'page': args.title,
        'format': 'json',
    }
).json()

if 'error' in response:
    sys.stderr.write('There was an error retrieving the page:\n')
    if 'info' in response['error']:
        sys.stderr.write(f"{response['error']['info']}\n")
    exit(1)

raw_html = response['parse']['text']['*']
document = html.document_fromstring(raw_html)
paragraphs = document.xpath('//p')
with open(args.out, "w") as out_file:
    for paragraph in paragraphs:
        sentences = nltk.sent_tokenize(paragraph.text_content())
        for sentence in sentences:
            sentence = re.sub(r'\[\d+\]', '', sentence) # strip references
            if sentence and len(sentence.split()) > 2: # ignore very short sentences
                out_file.write(f"{sentence.strip()}\n")