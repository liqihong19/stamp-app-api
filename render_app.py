"""
用章申请系统 - 共享后端 (Render 部署版)
Flask + SQLite, CORS 支持
"""
import sqlite3, json, os
from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stamp_app.db')

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None: db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT NOT NULL, phone TEXT NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL);
    """)
    count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        db.execute("INSERT INTO users(id,name,phone,password,role) VALUES(?,?,?,?,?)", ("13800000001_经办人","A","13800000001","123456","经办人"))
        db.execute("INSERT INTO users(id,name,phone,password,role) VALUES(?,?,?,?,?)", ("13800000002_审核人","B","13800000002","123456","审核人"))
        db.execute("INSERT INTO users(id,name,phone,password,role) VALUES(?,?,?,?,?)", ("13800000003_审批人","C","13800000003","123456","审批人"))
    db.commit(); db.close()

# ── API ──
@app.route('/api/data', methods=['GET'])
def get_data():
    db = get_db()
    users = {}
    for r in db.execute("SELECT * FROM users").fetchall():
        users[r['id']] = {"name":r['name'],"phone":r['phone'],"password":r['password'],"role":r['role']}
    tasks = [json.loads(r['data']) for r in db.execute("SELECT data FROM tasks ORDER BY id").fetchall()]
    stats = [json.loads(r['data']) for r in db.execute("SELECT data FROM stats ORDER BY id").fetchall()]
    return jsonify({"users":users,"tasks":tasks,"stats":stats})

@app.route('/api/data', methods=['POST'])
def save_data():
    data = request.get_json(force=True)
    db = get_db()
    if 'users' in data:
        db.execute("DELETE FROM users")
        for key, u in data['users'].items():
            db.execute("INSERT INTO users(id,name,phone,password,role) VALUES(?,?,?,?,?)", (key,u['name'],u['phone'],u['password'],u['role']))
    if 'tasks' in data:
        db.execute("DELETE FROM tasks")
        for t in data['tasks']:
            db.execute("INSERT INTO tasks(id,data) VALUES(?,?)", (t['id'],json.dumps(t,ensure_ascii=False)))
    if 'stats' in data:
        db.execute("DELETE FROM stats")
        for s in data['stats']:
            db.execute("INSERT INTO stats(data) VALUES(?)", (json.dumps(s,ensure_ascii=False),))
    db.commit()
    return jsonify({"ok":True})

@app.route('/api/health')
def health():
    return jsonify({"ok":True})

# ── 首页重定向到 surge.sh ──
@app.route('/')
def index():
    return jsonify({"app":"stamp-app-api","frontend":"https://yongzhang-shenqing.surge.sh"})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5099))
    app.run(host='0.0.0.0', port=port, debug=False)
