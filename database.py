import sqlite3
import os
import bcrypt
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'nursingcne.db')
data_dir = os.path.dirname(DB_PATH)
if not os.path.exists(data_dir):
    os.makedirs(data_dir, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA foreign_keys=ON;')
    return conn

# Global conn for init
db = get_db_connection()

def init_db():
    cursor = db.cursor()
    cursor.executescript("""
      CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL,
        original_amount REAL,
        badge TEXT,
        image_url TEXT,
        valid_till DATE,
        is_active INTEGER DEFAULT 1,
        seats_total INTEGER DEFAULT 0,
        seats_filled INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        offer_id INTEGER REFERENCES offers(id),
        name TEXT NOT NULL,
        institute TEXT NOT NULL,
        mobile TEXT NOT NULL,
        email TEXT NOT NULL,
        reg_number TEXT,
        amount REAL,
        payment_status TEXT DEFAULT 'pending',
        payment_id TEXT,
        transaction_id TEXT,
        payment_method TEXT,
        payment_data TEXT,
        email_sent INTEGER DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS gallery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        image_url TEXT NOT NULL,
        category TEXT DEFAULT 'general',
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS site_settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
    """)

    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'Admin@123')
    
    admin = cursor.execute('SELECT id FROM admins WHERE username = ?', (admin_username,)).fetchone()
    if not admin:
        hashed = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt()).decode()
        cursor.execute('INSERT INTO admins (username, password) VALUES (?, ?)', (admin_username, hashed))
        print(f"✅ Default admin created: {admin_username}")
        db.commit()

    offer_count = cursor.execute('SELECT COUNT(*) as cnt FROM offers').fetchone()['cnt']
    if offer_count == 0:
        cursor.execute('''
            INSERT INTO offers (title, description, amount, original_amount, badge, valid_till, seats_total, seats_filled, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Basic CNE Package', 'Comprehensive 20-credit nursing continuing education package covering essential clinical topics.', 1999.0, 2999.0, 'Popular', '2024-12-31', 50, 12, 1))
        cursor.execute('''
            INSERT INTO offers (title, description, amount, original_amount, badge, valid_till, seats_total, seats_filled, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Advanced CNE Bundle', 'Full 40-credit advanced nursing education bundle with specialization tracks and certification.', 3499.0, 4999.0, 'Best Value', '2024-12-31', 30, 5, 1))
        cursor.execute('''
            INSERT INTO offers (title, description, amount, original_amount, badge, valid_till, seats_total, seats_filled, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Emergency Nursing Workshop', 'Intensive hands-on emergency nursing workshop with simulation and case studies.', 4999.0, 6999.0, 'New', '2024-06-30', 20, 8, 1))
        print('✅ Sample offers seeded')
        db.commit()

    settings_data = {
        'site_name': 'NursingCNE',
        'site_tagline': 'Empowering Nurses Through Continuous Education',
        'site_phone': '+91-9876543210',
        'site_email': 'info@nursingcne.com',
        'site_whatsapp': '919876543210',
        'about_text': 'NursingCNE is India\'s premier platform for nursing continuing education. We provide high-quality, accredited CNE programs that help nurses stay updated with the latest clinical practices and advance their careers.',
        'hero_title': 'Advance Your Nursing Career',
        'hero_subtitle': 'Access world-class continuing nursing education programs designed by experts',
    }
    
    for k, v in settings_data.items():
        cursor.execute('INSERT OR IGNORE INTO site_settings (key, value) VALUES (?, ?)', (k, v))
    db.commit()
    print('✅ Database initialized successfully')

init_db()

def get_db():
    conn = get_db_connection()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
