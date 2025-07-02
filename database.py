import sqlite3
from typing import List, Dict, Optional
import os

class Database:
    def __init__(self, db_name: str = "evoting.db"):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_name, timeout=20.0)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
    
    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create mahasiswa table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mahasiswa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama TEXT NOT NULL,
                    nim TEXT UNIQUE NOT NULL,
                    jurusan TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create candidates table with visi and misi columns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama TEXT NOT NULL,
                    nim TEXT UNIQUE NOT NULL,
                    jurusan TEXT NOT NULL,
                    visi TEXT NOT NULL DEFAULT '',
                    misi TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create admin_sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            ''')
            
            # Create votes table for tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS votes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    voter_nim TEXT NOT NULL,
                    candidate_nim TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (voter_nim) REFERENCES mahasiswa(nim),
                    FOREIGN KEY (candidate_nim) REFERENCES candidates(nim)
                )
            ''')
            
            # Check and add missing columns if needed
            try:
                cursor.execute("SELECT visi, misi FROM candidates LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE candidates ADD COLUMN visi TEXT NOT NULL DEFAULT ''")
                cursor.execute("ALTER TABLE candidates ADD COLUMN misi TEXT NOT NULL DEFAULT ''")
            
            conn.commit()
    
    def add_mahasiswa(self, nama: str, nim: str, jurusan: str) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO mahasiswa (nama, nim, jurusan) VALUES (?, ?, ?)",
                    (nama, nim, jurusan)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Error adding mahasiswa: {e}")
            return False
    
    def verify_mahasiswa(self, nim: str, jurusan: str) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT nama, nim, jurusan FROM mahasiswa WHERE nim = ? AND jurusan = ?",
                    (nim, jurusan)
                )
                result = cursor.fetchone()
                return {
                    'nama': result[0],
                    'nim': result[1],
                    'jurusan': result[2]
                } if result else None
        except Exception as e:
            print(f"Error verifying mahasiswa: {e}")
            return None
    
    def get_mahasiswa_by_nim(self, nim: str) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT nama, nim, jurusan FROM mahasiswa WHERE nim = ?",
                    (nim,)
                )
                result = cursor.fetchone()
                return {
                    'nama': result[0],
                    'nim': result[1],
                    'jurusan': result[2]
                } if result else None
        except Exception as e:
            print(f"Error getting mahasiswa by NIM: {e}")
            return None
    
    def add_candidate(self, nama: str, nim: str, jurusan: str, visi: str, misi: str) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO candidates (nama, nim, jurusan, visi, misi) VALUES (?, ?, ?, ?, ?)",
                    (nama, nim, jurusan, visi, misi)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Error adding candidate: {e}")
            return False
    
    def get_candidate_by_name(self, name: str) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT nama, nim, jurusan FROM candidates WHERE nama = ?",
                    (name,)
                )
                result = cursor.fetchone()
                return {
                    'nama': result[0],
                    'nim': result[1],
                    'jurusan': result[2]
                } if result else None
        except Exception as e:
            print(f"Error getting candidate by name: {e}")
            return None
    
    def get_candidates(self, jurusan: str = None) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if jurusan:
                    cursor.execute(
                        "SELECT id, nama, nim, jurusan, visi, misi FROM candidates WHERE jurusan = ?",
                        (jurusan,)
                    )
                else:
                    cursor.execute("SELECT id, nama, nim, jurusan, visi, misi FROM candidates")
                
                return [{
                    'id': row[0],
                    'nama': row[1],
                    'nim': row[2],
                    'jurusan': row[3],
                    'visi': row[4],
                    'misi': row[5]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting candidates: {e}")
            return []
    
    def get_all_candidates(self) -> List[Dict]:
        return self.get_candidates()
    
    def get_total_voters(self) -> int:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM mahasiswa")
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error getting total voters: {e}")
            return 0
    
    def get_total_candidates(self) -> int:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM candidates")
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error getting total candidates: {e}")
            return 0
    
    def edit_candidate(self, original_nim: str, nama: str, nim: str, jurusan: str, visi: str, misi: str) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if nim != original_nim:
                    cursor.execute("SELECT COUNT(*) FROM candidates WHERE nim = ?", (nim,))
                    if cursor.fetchone()[0] > 0:
                        return False
                
                cursor.execute(
                    "UPDATE candidates SET nama = ?, nim = ?, jurusan = ?, visi = ?, misi = ? WHERE nim = ?",
                    (nama, nim, jurusan, visi, misi, original_nim)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error editing candidate: {e}")
            return False
    
    def delete_candidate(self, nim: str) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM candidates WHERE nim = ?", (nim,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting candidate: {e}")
            return False
    
    def create_admin_session(self, session_id: str, username: str, expires_at: str) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO admin_sessions (session_id, username, expires_at) VALUES (?, ?, ?)",
                    (session_id, username, expires_at)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating admin session: {e}")
            return False
    
    def delete_admin_session(self, session_id: str) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM admin_sessions WHERE session_id = ?", (session_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting admin session: {e}")
            return False
    
    def verify_admin_session(self, session_id: str) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM admin_sessions WHERE session_id = ? AND expires_at > datetime('now')",
                    (session_id,)
                )
                return cursor.fetchone()[0] > 0
        except Exception as e:
            print(f"Error verifying admin session: {e}")
            return False
    
    def record_vote(self, voter_nim: str, candidate_nim: str) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO votes (voter_nim, candidate_nim) VALUES (?, ?)",
                    (voter_nim, candidate_nim)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error recording vote: {e}")
            return False
    
    def has_voted(self, nim: str) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM votes WHERE voter_nim = ?",
                    (nim,)
                )
                return cursor.fetchone()[0] > 0
        except Exception as e:
            print(f"Error checking vote status: {e}")
            return False
