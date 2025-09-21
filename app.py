import os 
import io
import sqlite3
import numpy as np
from flask import Flask, request, render_template, jsonify, g
from PIL import Image
import insightface
from sklearn.metrics.pairwise import cosine_similarity

DB_PATH = os.path.join(os.path.dirname(__file__), "voters.db")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# initialize model (ArcFace via insightface)
model = insightface.app.FaceAnalysis(name='buffalo_l')
model.prepare(ctx_id=-1)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS voters (
        id INTEGER PRIMARY KEY, 
        name TEXT UNIQUE, 
        embedding BLOB
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY, 
        voter_id INTEGER, 
        candidate TEXT, 
        ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    db.commit()

@app.before_first_request
def setup():
    init_db()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def embedding_to_blob(emb):
    return emb.astype('float32').tobytes()

def blob_to_embedding(blob):
    return np.frombuffer(blob, dtype='float32')

def find_best_match(emb, threshold=0.35):
    db = get_db()
    rows = db.execute('SELECT id, name, embedding FROM voters').fetchall()
    if not rows:
        return None, None
    embeddings = [blob_to_embedding(r['embedding']) for r in rows]
    ids = [r['id'] for r in rows]
    names = [r['name'] for r in rows]
    embeddings = np.vstack(embeddings)
    emb = emb.reshape(1, -1)
    sims = cosine_similarity(emb, embeddings)[0]
    best_idx = int(sims.argmax())
    best_score = float(sims[best_idx])
    if best_score > 0.65:  # threshold for same person
        return ids[best_idx], names[best_idx]
    return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    name = request.form.get('name','').strip()
    img_file = request.files.get('image')
    if not name or not img_file:
        return jsonify({'success': False, 'error': 'name and image required'}), 400
    
    img = Image.open(io.BytesIO(img_file.read())).convert('RGB')
    img = np.array(img)[:, :, ::-1]
    faces = model.get(img)
    if not faces:
        return jsonify({'success': False, 'error': 'no face detected'}), 400
    
    emb = faces[0].embedding.astype('float32')

    # --- New duplicate face check ---
    db = get_db()
    rows = db.execute('SELECT id, name, embedding FROM voters').fetchall()
    for r in rows:
        existing_emb = blob_to_embedding(r['embedding']).reshape(1, -1)
        sim = cosine_similarity(emb.reshape(1, -1), existing_emb)[0][0]
        if sim > 0.65:  # similarity threshold
            return jsonify({'success': False, 'error': f'Face already registered as {r["name"]}'}), 400
    # --------------------------------

    try:
        db.execute('INSERT INTO voters (name, embedding) VALUES (?, ?)', (name, embedding_to_blob(emb)))
        db.commit()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    return jsonify({'success': True, 'message': f'Voter {name} registered.'})

@app.route('/vote', methods=['POST'])
def vote():
    img_file = request.files.get('image')
    candidate = request.form.get('candidate','').strip()
    if not img_file or not candidate:
        return jsonify({'success': False, 'error': 'image and candidate required'}), 400
    
    img = Image.open(io.BytesIO(img_file.read())).convert('RGB')
    img = np.array(img)[:, :, ::-1]
    faces = model.get(img)
    if not faces:
        return jsonify({'success': False, 'error': 'no face detected'}), 400
    
    emb = faces[0].embedding.astype('float32')
    voter_id, name = find_best_match(emb)
    if not voter_id:
        return jsonify({'success': False, 'error': 'no matching voter found'}), 404
    
    db = get_db()
    existing = db.execute('SELECT * FROM votes WHERE voter_id = ?', (voter_id,)).fetchone()
    if existing:
        return jsonify({'success': False, 'error': 'voter has already voted'}), 403
    
    db.execute('INSERT INTO votes (voter_id, candidate) VALUES (?, ?)', (voter_id, candidate))
    db.commit()
    return jsonify({'success': True, 'voter': name, 'candidate': candidate})

@app.route('/results')
def results():
    db = get_db()
    rows = db.execute('SELECT candidate, COUNT(*) as cnt FROM votes GROUP BY candidate').fetchall()
    data = [{ 'candidate': r['candidate'], 'votes': r['cnt']} for r in rows]
    return render_template('results.html', data=data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
