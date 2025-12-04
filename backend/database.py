"""
Database layer for unit storage and retrieval.
Uses SQLite for persistent storage with automatic schema initialization.
"""

import os
import re
import sqlite3
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(__file__), "data", "degree_path.db")
)

def get_db_connection() -> sqlite3.Connection:
    """Create database connection with row factory."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initialize database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS units (
            unit_code TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            credit_points INTEGER,
            year_level INTEGER,
            raw_prerequisites TEXT,
            raw_corequisites TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_code TEXT,
            outcome_text TEXT,
            FOREIGN KEY (unit_code) REFERENCES units (unit_code)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prerequisites (
            unit_code TEXT,
            prerequisite_code TEXT,
            FOREIGN KEY (unit_code) REFERENCES units (unit_code),
            FOREIGN KEY (prerequisite_code) REFERENCES units (unit_code),
            PRIMARY KEY (unit_code, prerequisite_code)
        )
    """)

    conn.commit()
    conn.close()

def save_unit(unit_data: Dict[str, Any]) -> None:
    """Save or update a unit in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO units 
            (unit_code, title, description, credit_points, year_level, 
             raw_prerequisites, raw_corequisites)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            unit_data['unit_code'],
            unit_data['title'],
            unit_data['description'],
            unit_data.get('credit_points', 10),
            unit_data.get('year_level', 1),
            unit_data.get('raw_prerequisites', ''),
            unit_data.get('raw_corequisites', '')
        ))
        
        cursor.execute(
            'DELETE FROM learning_outcomes WHERE unit_code = ?',
            (unit_data['unit_code'],)
        )
        
        for outcome in unit_data.get('learning_outcomes', []):
            cursor.execute(
                'INSERT INTO learning_outcomes (unit_code, outcome_text) VALUES (?, ?)',
                (unit_data['unit_code'], outcome)
            )
        
        raw_prereqs = unit_data.get('raw_prerequisites', '')
        found_prereqs = set(re.findall(r"([A-Z]{4}\d{4})", raw_prereqs))
        
        if unit_data['unit_code'] in found_prereqs:
            found_prereqs.remove(unit_data['unit_code'])
        
        cursor.execute(
            'DELETE FROM prerequisites WHERE unit_code = ?',
            (unit_data['unit_code'],)
        )
        
        for p_code in found_prereqs:
            cursor.execute('SELECT 1 FROM units WHERE unit_code = ?', (p_code,))
            if not cursor.fetchone():
                cursor.execute(
                    'INSERT INTO units (unit_code, title) VALUES (?, ?)',
                    (p_code, "Placeholder Unit")
                )
            
            cursor.execute(
                'INSERT INTO prerequisites (unit_code, prerequisite_code) VALUES (?, ?)',
                (unit_data['unit_code'], p_code)
            )
        
        conn.commit()
    except Exception as e:
        print(f"Error saving unit {unit_data.get('unit_code')}: {e}")
    finally:
        conn.close()

def get_unit(unit_code: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM units WHERE unit_code = ?', (unit_code,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
    
    unit = dict(row)
    
    cursor.execute('SELECT outcome_text FROM learning_outcomes WHERE unit_code = ?', (unit_code,))
    outcomes = [r['outcome_text'] for r in cursor.fetchall()]
    unit['learning_outcomes'] = outcomes
    
    # Fetch structured prerequisites
    cursor.execute('SELECT prerequisite_code FROM prerequisites WHERE unit_code = ?', (unit_code,))
    prereqs = [r['prerequisite_code'] for r in cursor.fetchall()]
    unit['prerequisites'] = prereqs
    
    unit['corequisites'] = []  # Placeholder for parsed coreqs if we add a table for them
    unit['incompatible_units'] = [] # Placeholder
    
    conn.close()
    return unit

def get_all_units() -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT unit_code FROM units')
    rows = cursor.fetchall()
    conn.close()
    
    all_units = {}
    for row in rows:
        unit = get_unit(row['unit_code'])
        if unit:
            all_units[unit['unit_code']] = unit
    return all_units

# Initialize DB on module load (or call explicitly)
init_db()
