import mysql.connector
from mysql.connector import Error

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Mpscax@126'
}

def create_database():
    connection = None
    cursor = None
    
    try:
        # Connect without specifying database
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS lovenest")
        cursor.execute("USE lovenest")
        
        # Create tables
        
        # Couples table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS couples (
                id INT AUTO_INCREMENT PRIMARY KEY,
                code VARCHAR(50) UNIQUE NOT NULL,
                love_days INT DEFAULT 0,
                created_at DATETIME NOT NULL
            )
        """)
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                couple_id INT NOT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('boyfriend', 'girlfriend') NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (couple_id) REFERENCES couples(id) ON DELETE CASCADE
            )
        """)
        
        # Timeline table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timeline (
                id INT AUTO_INCREMENT PRIMARY KEY,
                couple_id INT NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                created_by INT NOT NULL,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (couple_id) REFERENCES couples(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Love letters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS love_letters (
                id INT AUTO_INCREMENT PRIMARY KEY,
                couple_id INT NOT NULL,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                created_by INT NOT NULL,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (couple_id) REFERENCES couples(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Mood tracker table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mood_tracker (
                id INT AUTO_INCREMENT PRIMARY KEY,
                couple_id INT NOT NULL,
                user_id INT NOT NULL,
                mood ENUM('happy', 'sad', 'excited', 'angry', 'love', 'stressed', 'calm', 'romantic') NOT NULL,
                note TEXT,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (couple_id) REFERENCES couples(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Period tracker table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS period_tracker (
                id INT AUTO_INCREMENT PRIMARY KEY,
                couple_id INT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                flow_level ENUM('light', 'medium', 'heavy') NOT NULL,
                symptoms TEXT,
                notes TEXT,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (couple_id) REFERENCES couples(id) ON DELETE CASCADE
            )
        """)
        
        # Photos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS photos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                couple_id INT NOT NULL,
                filename VARCHAR(255) NOT NULL,
                caption TEXT,
                uploaded_by INT NOT NULL,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (couple_id) REFERENCES couples(id) ON DELETE CASCADE,
                FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Secret messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS secret_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                couple_id INT NOT NULL,
                sender_id INT NOT NULL,
                message TEXT NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (couple_id) REFERENCES couples(id) ON DELETE CASCADE,
                FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Quiz questions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                couple_id INT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_by INT NOT NULL,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (couple_id) REFERENCES couples(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Apologies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS apologies (
                id INT AUTO_INCREMENT PRIMARY KEY,
                couple_id INT NOT NULL,
                sender_id INT NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (couple_id) REFERENCES couples(id) ON DELETE CASCADE,
                FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Surprises table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS surprises (
                id INT AUTO_INCREMENT PRIMARY KEY,
                couple_id INT NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                surprise_date DATE NOT NULL,
                created_by INT NOT NULL,
                is_revealed BOOLEAN DEFAULT FALSE,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (couple_id) REFERENCES couples(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX idx_couples_code ON couples(code)")
        cursor.execute("CREATE INDEX idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX idx_users_couple ON users(couple_id)")
        cursor.execute("CREATE INDEX idx_timeline_couple ON timeline(couple_id)")
        cursor.execute("CREATE INDEX idx_love_letters_couple ON love_letters(couple_id)")
        cursor.execute("CREATE INDEX idx_mood_tracker_couple ON mood_tracker(couple_id)")
        cursor.execute("CREATE INDEX idx_photos_couple ON photos(couple_id)")
        cursor.execute("CREATE INDEX idx_secret_messages_couple ON secret_messages(couple_id)")
        cursor.execute("CREATE INDEX idx_secret_messages_expires ON secret_messages(expires_at)")
        cursor.execute("CREATE INDEX idx_quiz_questions_couple ON quiz_questions(couple_id)")
        cursor.execute("CREATE INDEX idx_apologies_couple ON apologies(couple_id)")
        cursor.execute("CREATE INDEX idx_surprises_couple ON surprises(couple_id)")
        
        connection.commit()
        print("Database and tables created successfully!")
        print("Indexes created for better performance!")
        
    except Error as e:
        print(f"Error creating database: {e}")
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def create_sample_data():
    """Create some sample data for testing"""
    connection = None
    cursor = None
    
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='your_db_user',
            password='your_db_password',
            database='lovenest'
        )
        cursor = connection.cursor()
        
        # Check if sample data already exists
        cursor.execute("SELECT COUNT(*) FROM couples")
        if cursor.fetchone()[0] > 0:
            print("Sample data already exists!")
            return
        
        # Create sample couple
        import datetime
        couple_created = datetime.datetime.now() - datetime.timedelta(days=365)  # 1 year ago
        
        cursor.execute("INSERT INTO couples (code, love_days, created_at) VALUES (%s, %s, %s)", 
                      ('LOVE2024', 365, couple_created))
        couple_id = cursor.lastrowid
        
        # Create sample users
        from hashlib import sha256
        
        # Boyfriend (admin)
        bf_password = sha256('password123'.encode()).hexdigest()
        cursor.execute("""INSERT INTO users (couple_id, name, email, password, role, is_admin, created_at)
                         VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                      (couple_id, 'John Doe', 'john@example.com', bf_password, 'boyfriend', True, couple_created))
        bf_id = cursor.lastrowid
        
        # Girlfriend
        gf_password = sha256('password123'.encode()).hexdigest()
        cursor.execute("""INSERT INTO users (couple_id, name, email, password, role, is_admin, created_at)
                         VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                      (couple_id, 'Jane Smith', 'jane@example.com', gf_password, 'girlfriend', False, couple_created))
        gf_id = cursor.lastrowid
        
        # Sample timeline entries
        timeline_entries = [
            ('First Date', 'Our magical first date at the coffee shop', bf_id),
            ('First Kiss', 'Under the stars in the park', gf_id),
            ('Anniversary', 'Celebrating our 6 months together', bf_id),
            ('Moving In', 'We decided to move in together!', gf_id)
        ]
        
        for i, (title, desc, creator) in enumerate(timeline_entries):
            entry_date = couple_created + datetime.timedelta(days=i*30)
            cursor.execute("""INSERT INTO timeline (couple_id, title, description, created_by, created_at)
                             VALUES (%s, %s, %s, %s, %s)""",
                          (couple_id, title, desc, creator, entry_date))
        
        # Sample love letters
        cursor.execute("""INSERT INTO love_letters (couple_id, title, content, created_by, created_at)
                         VALUES (%s, %s, %s, %s, %s)""",
                      (couple_id, 'My Dearest Love', 
                       'Every day with you feels like a beautiful dream. Thank you for being my everything.', 
                       bf_id, datetime.datetime.now() - datetime.timedelta(days=7)))
        
        cursor.execute("""INSERT INTO love_letters (couple_id, title, content, created_by, created_at)
                         VALUES (%s, %s, %s, %s, %s)""",
                      (couple_id, 'To My Heart', 
                       'You make every moment special. I love how you make me laugh and feel so loved.', 
                       gf_id, datetime.datetime.now() - datetime.timedelta(days=3)))
        
        # Sample mood entries
        moods = ['happy', 'love', 'excited', 'romantic', 'calm']
        for i in range(10):
            mood_date = datetime.datetime.now() - datetime.timedelta(days=i)
            user_id = bf_id if i % 2 == 0 else gf_id
            mood = moods[i % len(moods)]
            cursor.execute("""INSERT INTO mood_tracker (couple_id, user_id, mood, created_at)
                             VALUES (%s, %s, %s, %s)""",
                          (couple_id, user_id, mood, mood_date))
        
        # Sample quiz questions
        quiz_questions = [
            ('What is my favorite color?', 'Blue', bf_id),
            ('What is my dream vacation destination?', 'Paris', gf_id),
            ('What is my favorite food?', 'Pizza', bf_id),
            ('What movie makes me cry every time?', 'The Notebook', gf_id)
        ]
        
        for question, answer, creator in quiz_questions:
            cursor.execute("""INSERT INTO quiz_questions (couple_id, question, answer, created_by, created_at)
                             VALUES (%s, %s, %s, %s, %s)""",
                          (couple_id, question, answer, creator, datetime.datetime.now()))
        
        connection.commit()
        print("Sample data created successfully!")
        print("Login credentials:")
        print("Boyfriend: john@example.com / password123")
        print("Girlfriend: jane@example.com / password123")
        
    except Error as e:
        print(f"Error creating sample data: {e}")
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

if __name__ == '__main__':
    print("Creating LoveNest database...")
    create_database()
    
    create_sample = input("Would you like to create sample data for testing? (y/n): ")
    if create_sample.lower() == 'y':
        create_sample_data()
    
    print("Setup complete!")
