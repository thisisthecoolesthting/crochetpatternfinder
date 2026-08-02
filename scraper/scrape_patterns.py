#!/opt/crochet-venv/bin/python
"""
CrochetPatternFinder scraper v4 -- verified URLs, clean titles
"""
import requests, sqlite3, re, time, logging, json
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('scraper')

DB = '/var/www/crochetpatternfinder/patterns.db'
AFC_BASE = 'https://www.allfreecrochet.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute(
        'CREATE TABLE IF NOT EXISTS patterns ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT,'
        'title TEXT NOT NULL,'
        'source TEXT NOT NULL,'
        'source_url TEXT UNIQUE NOT NULL,'
        'image_url TEXT,'
        'category TEXT DEFAULT "General",'
        'difficulty TEXT,'
        'yarn_weight TEXT,'
        'description TEXT,'
        'scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP'
        ')'
    )
    conn.execute('CREATE INDEX IF NOT EXISTS idx_category ON patterns(category)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_source ON patterns(source)')
    conn.commit()
    return conn

def upsert(conn, title, source, src_url, img_url, category):
    clean_title = re.sub(r'\s+', ' ', title).strip()[:200]
    if not clean_title or len(clean_title) < 4:
        return False
    try:
        conn.execute(
            'INSERT OR IGNORE INTO patterns (title,source,source_url,image_url,category) VALUES (?,?,?,?,?)',
            (clean_title, source, src_url, img_url or '', category)
        )
        conn.commit()
        return conn.execute('SELECT changes()').fetchone()[0] > 0
    except Exception as ex:
        log.warning('upsert error: %s', ex)
        return False

def get_soup(url, retries=2):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return BeautifulSoup(r.text, 'html.parser')
            log.warning('HTTP %s for %s', r.status_code, url)
        except Exception as ex:
            log.warning('Attempt %d failed for %s: %s', i+1, url, ex)
        time.sleep(2)
    return None

# ----------------------------------------------------------------
# AllFreeCrochet -- verified working category slugs
# ----------------------------------------------------------------
AFC_CATS = [
    ('/Scarves',                  'Scarves'),
    ('/Crocheted-Cowls',          'Scarves'),
    ('/Shawls',                   'Scarves'),
    ('/Hats',                     'Hats'),
    ('/Baby-Hats',                'Baby'),
    ('/Crochet-Afghan-Patterns',  'Blankets'),
    ('/Baby-Afghan-Crochet-Patterns', 'Baby'),
    ('/Lapghan-Crochet-Patterns', 'Blankets'),
    ('/Free-Baby-Crochet-Patterns','Baby'),
    ('/Baby-Sweaters',            'Baby'),
    ('/Crochet-Amigurumi-Patterns','Amigurumi'),
    ('/Toys',                     'Amigurumi'),
    ('/Crochet-Bag-Patterns',     'Bags'),
    ('/Totes',                    'Bags'),
    ('/Sweaters-and-Ponchos',     'Sweaters'),
    ('/Dishcloths',               'Home Decor'),
    ('/Mittens-and-Gloves',       'Accessories'),
    ('/Bookmarks',                'General'),
    ('/Doilies',                  'Home Decor'),
    ('/Miscellaneous-Crochet/Free-Crochet-Patterns', 'General'),
]

# Path segments to skip (nav/utility links)
SKIP_SEGS = {
    'tutorials', 'basics', 'index.php', 'section', 'subctr', 'contest',
    'tag', 'author', 'frequently', 'newsletter', 'ebook', 'crochet-for-charity',
    'crochet-companies', 'crochet-designers', 'back-to-school',
}

def parse_afc_page(soup, category, conn):
    inserted = 0
    seen = set()

    # Strategy A: JSON-LD itemListElement (most reliable - always present)
    for script_el in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script_el.string or '')
            items = data.get('itemListElement', [])
            for item in items:
                url = item.get('url', '')
                if url and 'allfreecrochet.com' in url and url not in seen:
                    seen.add(url)
                    slug = url.rstrip('/').split('/')[-1]
                    title = slug.replace('-', ' ').title()
                    # Get from page content if possible
                    if upsert(conn, title, 'AllFreeCrochet', url, '', category):
                        inserted += 1
        except Exception:
            pass

    # Strategy B: articleCell / articleGrid divs (for titles + images)
    # We've already inserted from JSON-LD; now try to enrich with titles/images
    # by matching on the same URL paths
    for cell in soup.select('.articleCell, .articleGrid'):
        a_el = cell.find('a', href=True)
        if not a_el:
            continue
        href = a_el['href']
        if href.startswith('/'):
            full_url = AFC_BASE + href
        elif 'allfreecrochet.com' in href:
            full_url = href
        else:
            continue

        path = full_url.split('allfreecrochet.com')[-1]
        segs = [s.lower() for s in path.split('/') if s]
        if len(segs) < 2:
            continue
        if any(s in SKIP_SEGS for s in segs):
            continue
        if any(kw in path.lower() for kw in ['page/', 'sort_value=', '?s=']):
            continue

        # Get title from heading inside cell
        h_el = cell.find(class_=re.compile(r'articleHeadline|title|heading', re.I))
        title = h_el.get_text(strip=True) if h_el else a_el.get_text(strip=True)
        if not title or len(title) < 5:
            title = segs[-1].replace('-', ' ').title()

        # Get image
        img_el = cell.find('img')
        img = ''
        if img_el:
            img = img_el.get('data-lazy-src') or img_el.get('data-src') or img_el.get('src', '')
            if img and img.startswith('data:'):
                img = ''

        if full_url not in seen:
            seen.add(full_url)
            if upsert(conn, title, 'AllFreeCrochet', full_url, img, category):
                inserted += 1
        elif img:
            # Update image if we have one now
            try:
                conn.execute(
                    'UPDATE patterns SET image_url=?, title=? WHERE source_url=? AND image_url=""',
                    (img, title, full_url)
                )
                conn.commit()
            except Exception:
                pass

    return inserted

def scrape_allfree(conn, pages_per_cat=6):
    inserted = 0
    for cat_path, category in AFC_CATS:
        base_url = AFC_BASE + cat_path
        soup = get_soup(base_url)
        if not soup:
            log.warning('AFC %s: no response, skipping', cat_path)
            continue
        n = parse_afc_page(soup, category, conn)
        inserted += n
        log.info('AFC %s pg1: +%d (run total %d)', cat_path, n, inserted)
        time.sleep(1.2)

        for page in range(2, pages_per_cat + 1):
            page_url = base_url.rstrip('/') + '/page/' + str(page)
            soup = get_soup(page_url)
            if not soup:
                break
            n = parse_afc_page(soup, category, conn)
            inserted += n
            log.info('AFC %s pg%d: +%d (run total %d)', cat_path, page, n, inserted)
            time.sleep(1.2)
    return inserted

# ----------------------------------------------------------------
# Yarnspirations search -- clean up garbage titles
# ----------------------------------------------------------------
# Badge text that clutters Yarnspirations titles
YS_BADGE_RE = re.compile(
    r'\b(New|Free Gift|Limited Edition|Coming Soon|Price Drop|Clearance|'
    r'Sale|Best Seller|Top Rated|Exclusive)\b',
    re.IGNORECASE
)

CAT_KEYWORDS = {
    'Amigurumi': ['amigurumi', 'toy', 'stuffed', 'plush'],
    'Blankets':  ['blanket', 'afghan', 'throw', 'lapghan'],
    'Hats':      ['hat', 'beanie', 'cap', 'toque'],
    'Baby':      ['baby', 'infant', 'newborn', 'toddler'],
    'Scarves':   ['scarf', 'cowl', 'wrap', 'shawl'],
    'Bags':      ['bag', 'tote', 'purse', 'pouch'],
    'Sweaters':  ['sweater', 'cardigan', 'pullover', 'vest', 'poncho'],
}

def guess_cat(title):
    tl = title.lower()
    for cat, kws in CAT_KEYWORDS.items():
        if any(kw in tl for kw in kws):
            return cat
    return 'General'

def clean_ys_title(raw):
    # Remove badge words and clean whitespace
    cleaned = YS_BADGE_RE.sub('', raw)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def scrape_yarnspirations(conn, pages=20):
    inserted = 0
    base = 'https://www.yarnspirations.com'
    for page in range(1, pages + 1):
        url = base + '/search?type=product&q=crochet+free+pattern&page=' + str(page)
        soup = get_soup(url)
        if not soup:
            break
        count_this_page = 0
        seen_urls = set()

        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/products/' not in href:
                continue
            clean_path = href.split('?')[0]
            if not clean_path.startswith('http'):
                clean_path = base + clean_path
            if clean_path in seen_urls:
                continue
            seen_urls.add(clean_path)

            # Title: try the link text first, then nearby heading
            raw_txt = a.get_text(strip=True)
            if not raw_txt or len(raw_txt) < 4:
                p = a.parent
                for _ in range(3):
                    if p is None:
                        break
                    h = p.find(['h2', 'h3', 'h4', 'span'],
                               class_=re.compile(r'title|name|heading', re.I))
                    if h:
                        raw_txt = h.get_text(strip=True)
                        break
                    p = p.parent
            if not raw_txt or len(raw_txt) < 4:
                raw_txt = clean_path.split('/products/')[-1].replace('-', ' ').title()

            title = clean_ys_title(raw_txt)
            if not title or len(title) < 4:
                title = clean_path.split('/products/')[-1].replace('-', ' ').title()

            # Image
            img = ''
            p = a.parent
            for _ in range(4):
                if p is None:
                    break
                img_el = p.find('img')
                if img_el:
                    img = (img_el.get('data-src') or
                           img_el.get('srcset', '').split(' ')[0] or
                           img_el.get('src', ''))
                    if img and not img.startswith('data:'):
                        if img.startswith('//'):
                            img = 'https:' + img
                        break
                    img = ''
                p = p.parent

            cat = guess_cat(title)
            if upsert(conn, title, 'Yarnspirations', clean_path, img, cat):
                inserted += 1
                count_this_page += 1

        log.info('Yarnspirations page %d: +%d (total %d)', page, count_this_page, inserted)
        if count_this_page == 0:
            log.info('No new results at page %d, stopping YS', page)
            break
        time.sleep(2)
    return inserted

# ----------------------------------------------------------------
# Moogly
# ----------------------------------------------------------------
def scrape_moogly(conn, pages=6):
    inserted = 0
    for page in range(1, pages + 1):
        url = ('https://www.mooglyblog.com/category/free-crochet-patterns/' if page == 1
               else 'https://www.mooglyblog.com/category/free-crochet-patterns/page/' + str(page) + '/')
        soup = get_soup(url)
        if not soup:
            break
        count = 0
        for a in soup.select('h2.entry-title a, h3.entry-title a, .post-title a'):
            title = a.get_text(strip=True)
            href  = a.get('href', '')
            if not title or not href:
                continue
            img = ''
            art = a.find_parent('article') or a.find_parent('div', class_=re.compile(r'post|entry'))
            if art:
                img_el = art.find('img')
                if img_el:
                    img = img_el.get('data-lazy-src') or img_el.get('data-src') or img_el.get('src', '')
                    if img and img.startswith('data:'):
                        img = ''
            cat = guess_cat(title)
            if upsert(conn, title, 'Moogly', href, img, cat):
                inserted += 1
                count += 1
        log.info('Moogly page %d: +%d (total %d)', page, count, inserted)
        time.sleep(1.5)
    return inserted

# ----------------------------------------------------------------
# Daisy Farm Crafts
# ----------------------------------------------------------------
def scrape_daisy_farm(conn, pages=4):
    inserted = 0
    for page in range(1, pages + 1):
        url = ('https://daisyfarmcrafts.com/category/free-crochet-patterns/' if page == 1
               else 'https://daisyfarmcrafts.com/category/free-crochet-patterns/page/' + str(page) + '/')
        soup = get_soup(url)
        if not soup:
            break
        count = 0
        for a in soup.select('h2.entry-title a, h3.entry-title a, article h2 a, .post-title a'):
            title = a.get_text(strip=True)
            href  = a.get('href', '')
            if not title or not href:
                continue
            img = ''
            art = a.find_parent('article') or a.find_parent('div', class_=re.compile(r'post|entry'))
            if art:
                img_el = art.find('img')
                if img_el:
                    img = img_el.get('data-lazy-src') or img_el.get('data-src') or img_el.get('src', '')
                    if img and img.startswith('data:'):
                        img = ''
            cat = guess_cat(title)
            if upsert(conn, title, 'DaisyFarmCrafts', href, img, cat):
                inserted += 1
                count += 1
        log.info('DaisyFarm page %d: +%d (total %d)', page, count, inserted)
        time.sleep(1.5)
    return inserted

if __name__ == '__main__':
    conn = init_db()
    log.info('=== Scrape run v4 starting ===')
    n1 = scrape_allfree(conn, pages_per_cat=6)
    n2 = scrape_yarnspirations(conn, pages=20)
    n3 = scrape_moogly(conn, pages=6)
    n4 = scrape_daisy_farm(conn, pages=4)
    total = conn.execute('SELECT COUNT(*) FROM patterns').fetchone()[0]
    by_source = conn.execute('SELECT source, COUNT(*) FROM patterns GROUP BY source').fetchall()
    log.info('=== DONE: afc=%d ys=%d moogly=%d daisy=%d Total=%d ===', n1, n2, n3, n4, total)
    for src, cnt in by_source:
        log.info('  %s: %d', src, cnt)
    conn.close()
