import sqlite3
from flask import Flask, g

app = Flask(__name__)
app.config['DATABASE'] = 'placement.db'
app.config['SECRET_KEY'] = 'change-this-to-a-random-secret'

# ---------- DB helper functions ----------

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.executescript(f.read())
    db.commit()

# ---------- Test route ----------

@app.route('/')
def index():
    return 'Placement Portal Home - DB should be initialized now!'

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)


