import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import pymysql

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For session management

# ------------------ Database Connection ------------------
def get_db():
    try:
        conn = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "support_db"),
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as e:
        app.logger.error(f"Database connection error: {e}")
        return None

# ------------------ Database Initialization ------------------
def initialize_db():
    """Initialize database tables if they don't exist."""
    if os.environ.get('SKIP_DB_INIT', '0').lower() in ('1', 'true', 'yes'):
        app.logger.info('SKIP_DB_INIT set — skipping database initialization.')
        return
    
    conn = get_db()
    if conn is None:
        app.logger.error("init_db: no database connection available, skipping schema creation.")
        return

    try:
        with conn.cursor() as c:
            # Users table
            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Issues table
            c.execute("""
                CREATE TABLE IF NOT EXISTS issues (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    module VARCHAR(100),
                    description TEXT,
                    status VARCHAR(20) DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Logins table
            c.execute("""
                CREATE TABLE IF NOT EXISTS logins (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50),
                    status VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Knowledge Articles table
            c.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_articles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    issue_id INT,
                    author VARCHAR(50),
                    title VARCHAR(255),
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (issue_id) REFERENCES issues(id)
                )
            """)
        conn.commit()
        app.logger.info("✅ Database initialized successfully")
    except Exception as e:
        app.logger.error(f"Database initialization failed: {e}")
    finally:
        conn.close()

# ------------------ Run DB Init Once ------------------
_db_initialized = False

@app.before_request
def setup():
    global _db_initialized
    if not _db_initialized:
        initialize_db()
        _db_initialized = True

# ------------------ Example Routes ------------------
@app.route('/')
def home():
    return "Welcome to Support App ✅ Database setup is complete!"

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']

        conn = get_db()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO users (username, password, name) VALUES (%s, %s, %s)",
                                   (username, password, name))
                conn.commit()
                flash("Signup successful!", "success")
                return redirect(url_for('home'))
            except Exception as e:
                flash(f"Error: {e}", "danger")
            finally:
                conn.close()
    return render_template('signup.html')

if __name__ == "__main__":
    app.run(debug=True, port=10000)
