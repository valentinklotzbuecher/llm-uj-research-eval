
import csv, json, time, sys, re, urllib.parse, urllib.request

IN_CSV = 'dois_to_query.csv'
OUT_CSV = 'titles_abstracts_from_crossref.csv'

def fetch_crossref(doi):
    # Crossref works endpoint. Note: only Crossref-registered DOIs will return data here.
    url = 'https://api.crossref.org/works/' + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={'User-Agent': 'Unjournal-tools/1.0 (mailto:info@unjournal.org)'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return data.get('message', {})

def clean_abstract(raw):
    if not raw:
        return ''
    # Crossref abstracts may come in JATS XML; strip tags crudely
    txt = re.sub('<[^<]+?>', ' ', raw)
    txt = re.sub('\s+', ' ', txt).strip()
    return txt

def main():
    rows = []
    with open(IN_CSV, newline='') as f:
        for r in csv.DictReader(f):
            doi = r['doi'].strip()
            if not doi:
                continue
            try:
                msg = fetch_crossref(doi)
                title = ' '.join(msg.get('title', [])).strip()
                abstract = clean_abstract(msg.get('abstract', ''))
                rows.append({'doi': doi, 'title': title, 'abstract': abstract})
            except Exception as e:
                rows.append({'doi': doi, 'title': '', 'abstract': ''})
            time.sleep(0.2)  # be polite
    with open(OUT_CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['doi','title','abstract'])
        w.writeheader()
        w.writerows(rows)
    print(f'Wrote {OUT_CSV} with {len(rows)} rows.')

if __name__ == '__main__':
    main()
