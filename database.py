import sqlite3
import datetime

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('plant_disease.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            predicted_class TEXT NOT NULL,
            confidence REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_prediction(filename, predicted_class, confidence):
    """Save prediction to database"""
    conn = sqlite3.connect('plant_disease.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO predictions (filename, predicted_class, confidence)
        VALUES (?, ?, ?)
    ''', (filename, predicted_class, confidence))
    
    conn.commit()
    conn.close()

def get_recent_predictions(limit=10):
    """Get recent predictions"""
    conn = sqlite3.connect('plant_disease.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT filename, predicted_class, confidence, timestamp
        FROM predictions
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]