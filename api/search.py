#!/opt/crochet-venv/bin/python
"""
CrochetPatternFinder search API -- port 3088
"""
from flask import Flask, request, jsonify
import sqlite3, os

app = Flask(__name__)
DB = '/var/www/crochetpatternfinder/patterns.db'

def ensure_db():
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
    conn.commit()
    return conn

def get_conn():
    conn = ensure_db()
    conn.row_factory = sqlite3.Row
    return conn

@app.after_request
def cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/api/search')
def search():
    q      = request.args.get('q', '').strip()
    cat    = request.args.get('category', '').strip()
    src    = request.args.get('source', '').strip()
    limit  = min(int(request.args.get('limit', 24)), 100)
    offset = int(request.args.get('offset', 0))

    where, params = ['1=1'], []
    if q:
        where.append('(title LIKE ? OR description LIKE ?)')
        params += ['%' + q + '%', '%' + q + '%']
    if cat:
        where.append('category = ?')
        params.append(cat)
    if src:
        where.append('source = ?')
        params.append(src)

    w_clause  = ' AND '.join(where)
    sql       = 'SELECT * FROM patterns WHERE ' + w_clause + ' ORDER BY scraped_at DESC LIMIT ? OFFSET ?'
    count_sql = 'SELECT COUNT(*) FROM patterns WHERE ' + w_clause

    conn  = get_conn()
    total = conn.execute(count_sql, params).fetchone()[0]
    rows  = conn.execute(sql, params + [limit, offset]).fetchall()
    conn.close()

    return jsonify({
        'results': [dict(r) for r in rows],
        'total':   total,
        'limit':   limit,
        'offset':  offset,
    })

@app.route('/api/stats')
def stats():
    conn  = get_conn()
    total = conn.execute('SELECT COUNT(*) FROM patterns').fetchone()[0]
    cats  = conn.execute('SELECT category, COUNT(*) n FROM patterns GROUP BY category ORDER BY n DESC').fetchall()
    srcs  = conn.execute('SELECT source,   COUNT(*) n FROM patterns GROUP BY source   ORDER BY n DESC').fetchall()
    conn.close()
    return jsonify({
        'total':       total,
        'by_category': {r['category']: r['n'] for r in cats},
        'by_source':   {r['source']:   r['n'] for r in srcs},
    })

@app.route('/api/categories')
def categories():
    conn = get_conn()
    cats = conn.execute('SELECT DISTINCT category FROM patterns WHERE category != "" ORDER BY category').fetchall()
    conn.close()
    return jsonify([r['category'] for r in cats])

if __name__ == '__main__':
    ensure_db()
    app.run(host='127.0.0.1', port=3088, debug=False)
