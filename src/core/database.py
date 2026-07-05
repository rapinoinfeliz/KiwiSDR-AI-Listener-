import sqlite3
import time
from typing import List, Dict, Any

DB_PATH = "kiwisdr_logs.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intercepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            frequency REAL,
            node_name TEXT,
            text TEXT,
            translation TEXT,
            score REAL,
            confidence REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_intercept(frequency: float, node_name: str, text: str, translation: str, score: float, confidence: float):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO intercepts (timestamp, frequency, node_name, text, translation, score, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (time.time(), frequency, node_name, text, translation, score, confidence))
    conn.commit()
    conn.close()

def get_recent_intercepts(limit: int = 50) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, frequency, node_name, text, translation, score, confidence
        FROM intercepts
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    columns = [col[0] for col in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
    return results

init_db()
