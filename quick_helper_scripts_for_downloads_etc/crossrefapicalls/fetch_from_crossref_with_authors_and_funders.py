
import csv, json, time, sys, re, urllib.parse, urllib.request

IN_CSV = 'dois_to_query.csv'
OUT_CSV = 'titles_abstracts_from_crossref_with_authors_funders.csv'

UA = 'Unjournal-tools/1.1 (mailto:info@unjournal.org)'

def fetch_crossref(doi):
    url = 'https://api.crossref.org/works/' + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return data.get('message', {})

def clean_text(raw):
    if not raw:
        return ''
    txt = re.sub('<[^<]+?>', ' ', raw)  # strip JATS/XML tags
    txt = re.sub('\s+', ' ', txt).strip()
    return txt

def authors_to_str(authors):
    if not isinstance(authors, list):
        return '', ''
    names = []
    affil_blocks = []
    for a in authors:
        given = (a.get('given') or '').strip()
        family = (a.get('family') or '').strip()
        # Format: Family, Given (when both available)
        if family and given:
            name = f"{family}, {given}"
        else:
            name = (a.get('name') or given or family or '').strip()
        names.append(name)
        affs = a.get('affiliation') or []
        aff_names = [clean_text(x.get('name') or '') for x in affs if (x.get('name') or '').strip()]
        # Combine multiple affiliations per author with '; '
        aff_block = '; '.join([x for x in aff_names if x])
        affil_blocks.append(aff_block)
    # Authors separated by ' | ' to keep CSV safe
    authors_str = ' | '.join(names).strip()
    # Affiliation blocks aligned to authors order
    affiliations_str = ' | '.join(affil_blocks).strip()
    return authors_str, affiliations_str

def funders_to_str(funders):
    if not isinstance(funders, list):
        return ''
    parts = []
    for f in funders:
        name = clean_text(f.get('name') or '')
        awards = f.get('award') or []
        if isinstance(awards, (list, tuple)):
            awards_txt = '; '.join([str(a) for a in awards if str(a).strip()])
        else:
            awards_txt = str(awards) if str(awards).strip() else ''
        if name and awards_txt:
            parts.append(f"{name} [awards: {awards_txt}]")
        elif name:
            parts.append(name)
        elif awards_txt:
            parts.append(f"awards: {awards_txt}")
    return ' | '.join(parts).strip()

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
                abstract = clean_text(msg.get('abstract', ''))
                authors_str, affils_str = authors_to_str(msg.get('author'))
                funders_str = funders_to_str(msg.get('funder'))
                rows.append({
                    'doi': doi,
                    'title': title,
                    'abstract': abstract,
                    'authors': authors_str,
                    'author_affiliations': affils_str,
                    'funding': funders_str,
                })
            except Exception as e:
                rows.append({
                    'doi': doi,
                    'title': '',
                    'abstract': '',
                    'authors': '',
                    'author_affiliations': '',
                    'funding': '',
                })
            time.sleep(0.2)  # be polite to the API
    with open(OUT_CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['doi','title','abstract','authors','author_affiliations','funding'])
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {OUT_CSV} with {len(rows)} rows.")

if __name__ == '__main__':
    main()
