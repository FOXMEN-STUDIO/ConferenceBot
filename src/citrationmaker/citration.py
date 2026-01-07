import bibtexparser
# 1. Load a single BibTeX entry
def load_bibtex_entry(bibtex_str):
    return bibtexparser.loads(bibtex_str).entries[0]
# 2. Helper to format authors
def format_authors(authors_raw):
    if not authors_raw:
        return ["Unknown"]
    authors = [a.strip() for a in authors_raw.replace("\n", " ").split(" and ")]
    final = []
    for a in authors:
        if "," in a:  # Already "Last, First"
            last, first = a.split(",", 1)
            final.append(f"{first.strip()} {last.strip()}")
        else:
            parts = a.split()
            final.append(f"{parts[-1]}, {' '.join(parts[:-1])}")
    return final
# 3. STYLE FUNCTIONS
def apa(e):
    authors = format_authors(e.get("author", ""))
    if len(authors) > 1:
        a = ", ".join(authors[:-1]) + ", & " + authors[-1]
    else:
        a = authors[0]
    return f"{a} ({e.get('year')}). {e.get('title')}. {e.get('journal')}, {e.get('volume')}({e.get('number')}), {e.get('pages')}."

def mla(e):
    authors = format_authors(e.get("author", ""))
    a = authors[0] + (" et al." if len(authors) > 1 else "")
    return f"{a}. \"{e.get('title')}\". {e.get('journal')}, vol. {e.get('volume')}, no. {e.get('number')}, {e.get('year')}, pp. {e.get('pages')}."
def mla(e):
    authors = format_authors(e.get("author", ""))
    a = authors[0] + (" et al." if len(authors) > 1 else "")
    return f"{a}. \"{e.get('title')}\". {e.get('journal')}, vol. {e.get('volume')}, no. {e.get('number')}, {e.get('year')}, pp. {e.get('pages')}."

def ieee(e):
    authors = ", ".join(format_authors(e.get("author", "")))
    return f"{authors}, \"{e.get('title')},\" {e.get('journal')}, vol. {e.get('volume')}, no. {e.get('number')}, pp. {e.get('pages')}, {e.get('year')}."

def chicago(e):
    authors = ", ".join(format_authors(e.get("author", "")))
    return f"{authors}. \"{e.get('title')}\". {e.get('journal')} {e.get('volume')}, no. {e.get('number')} ({e.get('year')}): {e.get('pages')}."

def harvard(e):
    authors = "; ".join(format_authors(e.get("author", "")))
    return f"{authors} ({e.get('year')}) {e.get('title')}. {e.get('journal')}, {e.get('volume')}({e.get('number')}), pp. {e.get('pages')}."

def vancouver(e):
    authors = ", ".join(format_authors(e.get("author", "")))
    return f"{authors}. {e.get('title')}. {e.get('journal')}. {e.get('year')};{e.get('volume')}({e.get('number')}):{e.get('pages')}."

# 4. MAIN FUNCTION (Your Bot Uses This)
def convert_bibtex_to_style(bibtex_input, style_name):
    entry = load_bibtex_entry(bibtex_input)
    
    style_map = {
        "APA": apa,
        "MLA": mla,
        "IEEE": ieee,
        "Chicago": chicago,
        "Harvard": harvard,
        "Vancouver": vancouver
    }
    
    style_fn = style_map.get(style_name)
    if not style_fn:
        return f"❌ Error: '{style_name}' is not supported."
    
    return style_fn(entry)

