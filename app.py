from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from blockchain import Blockchain, Transaction
from database import Database
import secrets
import os
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize blockchain and database
blockchain = Blockchain()
db = Database()

# Admin credentials (in production, use proper authentication)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    stats = {
        'total_voters': db.get_total_voters(),
        'total_candidates': db.get_total_candidates(),
        'total_votes': blockchain.get_total_votes(),
        'blockchain_blocks': len(blockchain.chain)
    }
    
    return render_template('admin.html', stats=stats)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            # Create admin session in database
            session_id = secrets.token_hex(32)
            expires_at = (datetime.now() + timedelta(hours=8)).isoformat()
            db.create_admin_session(session_id, username, expires_at)
            session['admin_session_id'] = session_id
            
            return jsonify({'success': True, 'message': 'Login admin berhasil!'})
        else:
            return jsonify({'success': False, 'message': 'Username atau password salah!'})
    
    return render_template('admin_login.html')

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    if 'admin' in session:
        # Delete admin session from database
        if 'admin_session_id' in session:
            db.delete_admin_session(session['admin_session_id'])
        
        session.pop('admin', None)
        session.pop('admin_session_id', None)
        return jsonify({'success': True, 'message': 'Logout berhasil!'})
    
    return jsonify({'success': False, 'message': 'Tidak ada sesi admin aktif!'})

# Update route /admin/candidates:
@app.route('/admin/candidates', methods=['GET', 'POST'])
def admin_candidates():
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'No data provided'}), 400
                
            print("Received data:", data)  # Debug logging
            
            nama = data.get('nama')
            nim = data.get('nim')
            jurusan = data.get('jurusan')
            visi = data.get('visi')
            misi = data.get('misi')
            
            if not all([nama, nim, jurusan, visi, misi]):
                return jsonify({'success': False, 'message': 'All fields are required'}), 400
            
            if db.add_candidate(nama, nim, jurusan, visi, misi):
                socketio.emit('candidate_added', {
                    'nama': nama,
                    'nim': nim,
                    'jurusan': jurusan,
                    'visi': visi,
                    'misi': misi
                })
                return jsonify({'success': True, 'message': 'Candidate added successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to add candidate (possibly duplicate NIM)'}), 400
                
        except Exception as e:
            print("Error adding candidate:", str(e))
            return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500
    
    all_candidates = db.get_all_candidates()
    return jsonify({'candidates': all_candidates})

# Update route /admin/candidates/edit:
@app.route('/admin/candidates/edit', methods=['PUT'])
def edit_candidate():
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.get_json()
        original_nim = data.get('originalNim')
        nama = data.get('nama')
        nim = data.get('nim')
        jurusan = data.get('jurusan')
        visi = data.get('visi')
        misi = data.get('misi')
        
        if not all([original_nim, nama, nim, jurusan, visi, misi]):
            return jsonify({'success': False, 'message': 'Data tidak lengkap!'})
        
        if db.edit_candidate(original_nim, nama, nim, jurusan, visi, misi):
            socketio.emit('candidate_updated', {
                'original_nim': original_nim,
                'nama': nama,
                'nim': nim,
                'jurusan': jurusan,
                'visi': visi,
                'misi': misi
            })
            return jsonify({'success': True, 'message': 'Kandidat berhasil diperbarui!'})
        else:
            return jsonify({'success': False, 'message': 'Gagal memperbarui kandidat! NIM mungkin sudah digunakan.'})
    
    except Exception as e:
        print(f"Error editing candidate: {e}")
        return jsonify({'success': False, 'message': 'Terjadi kesalahan saat memperbarui kandidat!'})
    
@app.route('/admin/candidates/delete', methods=['DELETE'])
def delete_candidate():
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.get_json()
        nim = data.get('nim')
        jurusan = data.get('jurusan')
        
        if not nim or not jurusan:
            return jsonify({'success': False, 'message': 'Data tidak lengkap!'})
        
        if db.delete_candidate(nim, jurusan):
            # Emit real-time update
            socketio.emit('candidate_deleted', {
                'nim': nim,
                'jurusan': jurusan
            })
            return jsonify({'success': True, 'message': 'Kandidat berhasil dihapus!'})
        else:
            return jsonify({'success': False, 'message': 'Kandidat tidak ditemukan atau gagal dihapus!'})
    
    except Exception as e:
        print(f"Error deleting candidate: {e}")
        return jsonify({'success': False, 'message': 'Terjadi kesalahan saat menghapus kandidat!'})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        nama = data.get('nama')
        nim = data.get('nim')
        jurusan = data.get('jurusan')
        
        if db.add_mahasiswa(nama, nim, jurusan):
            # Emit real-time update
            socketio.emit('voter_registered', {
                'nama': nama,
                'nim': nim,
                'jurusan': jurusan
            })
            return jsonify({'success': True, 'message': 'Registrasi berhasil!'})
        else:
            return jsonify({'success': False, 'message': 'NIM sudah terdaftar!'})
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        nim = data.get('nim')
        jurusan = data.get('jurusan')
        
        mahasiswa = db.verify_mahasiswa(nim, jurusan)
        if mahasiswa:
            session['mahasiswa'] = mahasiswa
            
            # Check if user has already voted
            if blockchain.has_voted(nim):
                return jsonify({
                    'success': True, 
                    'message': 'Login berhasil!', 
                    'redirect': url_for('vote_confirmed')
                })
            else:
                return jsonify({
                    'success': True, 
                    'message': 'Login berhasil!', 
                    'redirect': url_for('vote')
                })
        else:
            return jsonify({'success': False, 'message': 'Data tidak ditemukan!'})
    
    return render_template('login.html')

@app.route('/vote')
def vote():
    if 'mahasiswa' not in session:
        return redirect(url_for('login'))
    
    mahasiswa = session['mahasiswa']
    
    # Check if user has already voted
    if blockchain.has_voted(mahasiswa['nim']):
        return redirect(url_for('vote_confirmed'))
    
    # Ambil semua kandidat (tanpa filter jurusan)
    candidates = db.get_all_candidates()
    return render_template('vote.html', candidates=candidates, mahasiswa=mahasiswa)

@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    if 'mahasiswa' not in session:
        return jsonify({
            'success': False, 
            'message': 'Anda belum login!'
        }), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data tidak valid!'
            }), 400

        candidate = data.get('candidate')
        if not candidate:
            return jsonify({
                'success': False,
                'message': 'Kandidat tidak dipilih!'
            }), 400

        mahasiswa = session['mahasiswa']
        print(f"Debug: Voting attempt by {mahasiswa['nim']} for {candidate}")  # Log debugging

        # Cek apakah sudah pernah voting
        if blockchain.has_voted(mahasiswa['nim']):
            return jsonify({
                'success': False,
                'message': 'Anda sudah melakukan voting sebelumnya!'
            }), 400

        # Buat transaksi
        transaction = Transaction(
            voter_id=mahasiswa['nim'],
            candidate=candidate,
            jurusan=mahasiswa['jurusan']
        )

        # Tambahkan ke blockchain
        if blockchain.add_transaction(transaction):
            blockchain.mine_pending_transactions()
            
            # Update frontend via Socket.IO
            socketio.emit('vote_cast', {
                'candidate': candidate,
                'jurusan': mahasiswa['jurusan'],
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({
                'success': True, 
                'message': 'Vote berhasil dicatat!',
                'redirect': url_for('vote_confirmed')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Gagal menambahkan transaksi ke blockchain!'
            }), 500

    except Exception as e:
        print(f"Error in submit_vote: {str(e)}")  # Log error
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan sistem: {str(e)}'
        }), 500
        
        
@app.route('/results/<jurusan>')
def results(jurusan):
    vote_count = blockchain.get_vote_count(jurusan)
    candidates = db.get_candidates(jurusan)
    return render_template('results.html', vote_count=vote_count, jurusan=jurusan, candidates=candidates)

@app.route('/api/results/<jurusan>')
def api_results(jurusan):
    vote_count = blockchain.get_vote_count(jurusan)
    return jsonify(vote_count)

@app.route('/api/verify_tx')
def verify_transaction():
    tx_hash = request.args.get('hash')
    if not tx_hash:
        return jsonify({'valid': False, 'message': 'Hash parameter missing'}), 400
    
    # Search in blockchain
    for block in blockchain.chain:
        for tx in block.transactions:
            if tx.hash == tx_hash:
                return jsonify({
                    'valid': True,
                    'message': 'Transaction found in blockchain',
                    'block_index': block.index,
                    'transaction': tx.to_dict()
                })
    
    # Search in pending transactions
    for tx in blockchain.pending_transactions:
        if tx.hash == tx_hash:
            return jsonify({
                'valid': True,
                'message': 'Transaction is pending',
                'transaction': tx.to_dict()
            })
    
    return jsonify({'valid': False, 'message': 'Transaction not found'}), 404

@app.route('/blockchain_info')
def blockchain_info():
    try:
        chain_data = []
        for block in blockchain.chain:
            transactions = []
            for tx in block.transactions:
                try:
                    voter_info = db.get_mahasiswa_by_nim(tx.voter_id) or {}
                    candidate_info = db.get_candidate_by_name(tx.candidate) or {}
                    
                    transactions.append({
                        'voter_id': tx.voter_id,
                        'candidate': tx.candidate,
                        'jurusan': tx.jurusan,
                        'timestamp': tx.timestamp,
                        'tx_hash': tx.hash,
                        'voter_department': voter_info.get('jurusan', 'Unknown'),
                        'candidate_department': candidate_info.get('jurusan', 'Unknown')
                    })
                except Exception as e:
                    print(f"Error processing transaction: {e}")
                    continue
            
            chain_data.append({
                'index': block.index,
                'timestamp': block.timestamp,
                'transactions': transactions,
                'hash': block.hash,
                'previous_hash': block.previous_hash,
                'nonce': block.nonce
            })
        
        return jsonify({
            'chain': chain_data,
            'length': len(blockchain.chain),
            'is_valid': blockchain.is_chain_valid()
        })
    except Exception as e:
        print(f"Error in blockchain_info: {e}")
        return jsonify({'error': 'Could not retrieve blockchain data'}), 500
    
    
@app.route('/blockchain')
def blockchain_explorer():
    return render_template('blockchain.html')

@app.route('/logout')
def logout():
    session.pop('mahasiswa', None)
    session.pop('admin', None)
    return redirect(url_for('index'))

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join_room')
def handle_join_room(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'Joined room {room}'})

@app.route('/vote-confirmed')
def vote_confirmed():
    if 'mahasiswa' not in session:
        return redirect(url_for('login'))
    return render_template('vote-confirmed.html')


if __name__ == '__main__':
     # Bersihkan session lama
    try:
        os.remove('flask_session')
    except:
        pass
    # # Add sample data
    # sample_candidates = [
    #     ("Alice Johnson", "12345001", "Teknik Informatika"),
    #     ("Bob Smith", "12345002", "Teknik Informatika"),
    #     ("Charlie Brown", "12345003", "Sistem Informasi"),
    #     ("Diana Prince", "12345004", "Sistem Informasi")
    # ]
    
    # for nama, nim, jurusan in sample_candidates:
    #     db.add_candidate(nama, nim, jurusan)
    
    print("🚀 Starting Modern E-Voting Blockchain Application...")
    print("📱 Access: http://localhost:5000")
    print("👨‍💼 Admin: http://localhost:5000/admin (admin/admin123)")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
