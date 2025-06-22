from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from mysql.connector import Error
import hashlib
import datetime
import os
import secrets
from werkzeug.utils import secure_filename
from functools import wraps
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Mpscax@126',
    'database': 'lovenest',
    'autocommit': True
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            flash('Admin access required')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  # 'boyfriend' or 'girlfriend'
        couple_code = request.form['couple_code']
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection error')
            return render_template('register.html')
        
        cursor = connection.cursor()
        
        try:
            # Check if couple code exists or create new couple
            cursor.execute("SELECT id FROM couples WHERE code = %s", (couple_code,))
            couple = cursor.fetchone()
            
            if not couple:
                # Create new couple
                cursor.execute("INSERT INTO couples (code, created_at) VALUES (%s, %s)", 
                             (couple_code, datetime.datetime.now()))
                couple_id = cursor.lastrowid
            else:
                couple_id = couple[0]
                # Check if couple already has 2 members
                cursor.execute("SELECT COUNT(*) FROM users WHERE couple_id = %s", (couple_id,))
                count = cursor.fetchone()[0]
                if count >= 2:
                    flash('This couple is already complete')
                    return render_template('register.html')
            
            # Create user
            hashed_password = hash_password(password)
            is_admin = (role == 'boyfriend')
            
            cursor.execute("""INSERT INTO users (name, email, password, role, couple_id, is_admin, created_at) 
                             VALUES (%s, %s, %s, %s, %s, %s, %s)""", 
                          (name, email, hashed_password, role, couple_id, is_admin, datetime.datetime.now()))
            
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
            
        except Error as e:
            flash(f'Registration error: {e}')
            return render_template('register.html')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection error')
            return render_template('login.html')
        
        cursor = connection.cursor()
        
        try:
            hashed_password = hash_password(password)
            cursor.execute("SELECT id, name, role, couple_id, is_admin FROM users WHERE email = %s AND password = %s", 
                          (email, hashed_password))
            user = cursor.fetchone()
            
            if user:
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                session['user_role'] = user[2]
                session['couple_id'] = user[3]
                session['is_admin'] = user[4]
                
                # Update love day counter
                cursor.execute("SELECT created_at FROM couples WHERE id = %s", (user[3],))
                couple_created = cursor.fetchone()[0]
                love_days = (datetime.datetime.now() - couple_created).days
                cursor.execute("UPDATE couples SET love_days = %s WHERE id = %s", (love_days, user[3]))
                
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials')
                
        except Error as e:
            flash(f'Login error: {e}')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('index'))
    
    cursor = connection.cursor()
    
    try:
        # Get couple info
        cursor.execute("SELECT love_days, created_at FROM couples WHERE id = %s", (session['couple_id'],))
        couple_info = cursor.fetchone()
        
        # Get partner info
        cursor.execute("SELECT name, role FROM users WHERE couple_id = %s AND id != %s", 
                      (session['couple_id'], session['user_id']))
        partner = cursor.fetchone()
        
        # Get recent timeline entries
        cursor.execute("""SELECT title, description, created_at FROM timeline 
                         WHERE couple_id = %s ORDER BY created_at DESC LIMIT 5""", 
                      (session['couple_id'],))
        recent_timeline = cursor.fetchall()
        
        # Get mood stats
        cursor.execute("""SELECT mood, COUNT(*) as count FROM mood_tracker 
                         WHERE couple_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                         GROUP BY mood""", (session['couple_id'],))
        mood_stats = cursor.fetchall()
        
        return render_template('dashboard.html', 
                             couple_info=couple_info, 
                             partner=partner, 
                             recent_timeline=recent_timeline,
                             mood_stats=mood_stats)
                             
    except Error as e:
        flash(f'Dashboard error: {e}')
        return redirect(url_for('index'))
    finally:
        cursor.close()
        connection.close()

@app.route('/timeline')
@login_required
def timeline():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('dashboard'))
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""SELECT title, description, created_at, created_by FROM timeline 
                         WHERE couple_id = %s ORDER BY created_at DESC""", 
                      (session['couple_id'],))
        entries = cursor.fetchall()
        
        return render_template('timeline.html', entries=entries)
        
    except Error as e:
        flash(f'Timeline error: {e}')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        connection.close()

@app.route('/add_timeline', methods=['POST'])
@login_required
def add_timeline():
    title = request.form['title']
    description = request.form['description']
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('timeline'))
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""INSERT INTO timeline (couple_id, title, description, created_by, created_at)
                         VALUES (%s, %s, %s, %s, %s)""",
                      (session['couple_id'], title, description, session['user_id'], datetime.datetime.now()))
        
        flash('Timeline entry added successfully!')
        
    except Error as e:
        flash(f'Error adding timeline entry: {e}')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('timeline'))

@app.route('/love_letters')
@login_required
def love_letters():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('dashboard'))
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""SELECT id, title, content, created_by, created_at FROM love_letters 
                         WHERE couple_id = %s ORDER BY created_at DESC""", 
                      (session['couple_id'],))
        letters = cursor.fetchall()
        
        return render_template('love_letters.html', letters=letters)
        
    except Error as e:
        flash(f'Love letters error: {e}')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        connection.close()

@app.route('/write_letter', methods=['GET', 'POST'])
@login_required
def write_letter():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection error')
            return redirect(url_for('love_letters'))
        
        cursor = connection.cursor()
        
        try:
            cursor.execute("""INSERT INTO love_letters (couple_id, title, content, created_by, created_at)
                             VALUES (%s, %s, %s, %s, %s)""",
                          (session['couple_id'], title, content, session['user_id'], datetime.datetime.now()))
            
            flash('Love letter sent successfully!')
            return redirect(url_for('love_letters'))
            
        except Error as e:
            flash(f'Error sending love letter: {e}')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('write_letter.html')

@app.route('/intimacy_zone')
@login_required
def intimacy_zone():
    return render_template('intimacy_zone.html')

@app.route('/mood_tracker')
@login_required
def mood_tracker():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('dashboard'))
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""SELECT mood, note, created_at FROM mood_tracker 
                         WHERE couple_id = %s AND user_id = %s ORDER BY created_at DESC LIMIT 30""", 
                      (session['couple_id'], session['user_id']))
        my_moods = cursor.fetchall()
        
        cursor.execute("""SELECT mood, created_at FROM mood_tracker 
                         WHERE couple_id = %s AND user_id != %s ORDER BY created_at DESC LIMIT 30""", 
                      (session['couple_id'], session['user_id']))
        partner_moods = cursor.fetchall()
        
        return render_template('mood_tracker.html', my_moods=my_moods, partner_moods=partner_moods)
        
    except Error as e:
        flash(f'Mood tracker error: {e}')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        connection.close()

@app.route('/add_mood', methods=['POST'])
@login_required
def add_mood():
    mood = request.form['mood']
    note = request.form.get('note', '')
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Database connection error'})
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""INSERT INTO mood_tracker (couple_id, user_id, mood, note, created_at)
                         VALUES (%s, %s, %s, %s, %s)""",
                      (session['couple_id'], session['user_id'], mood, note, datetime.datetime.now()))
        
        return jsonify({'success': True})
        
    except Error as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()
        connection.close()

@app.route('/period_tracker')
@login_required
def period_tracker():
    if session['user_role'] != 'girlfriend':
        flash('This feature is only available for girlfriends')
        return redirect(url_for('dashboard'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('dashboard'))
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""SELECT start_date, end_date, flow_level, symptoms, notes, created_at 
                         FROM period_tracker WHERE couple_id = %s ORDER BY start_date DESC LIMIT 12""", 
                      (session['couple_id'],))
        periods = cursor.fetchall()
        
        return render_template('period_tracker.html', periods=periods)
        
    except Error as e:
        flash(f'Period tracker error: {e}')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        connection.close()

@app.route('/add_period', methods=['POST'])
@login_required
def add_period():
    if session['user_role'] != 'girlfriend':
        return jsonify({'error': 'Unauthorized'}), 403
    
    start_date = request.form['start_date']
    end_date = request.form.get('end_date')
    flow_level = request.form['flow_level']
    symptoms = request.form.get('symptoms', '')
    notes = request.form.get('notes', '')
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('period_tracker'))
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""INSERT INTO period_tracker (couple_id, start_date, end_date, flow_level, symptoms, notes, created_at)
                         VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                      (session['couple_id'], start_date, end_date, flow_level, symptoms, notes, datetime.datetime.now()))
        
        flash('Period data added successfully!')
        
    except Error as e:
        flash(f'Error adding period data: {e}')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('period_tracker'))

@app.route('/photo_gallery')
@login_required
def photo_gallery():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('dashboard'))
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""SELECT id, filename, caption, uploaded_by, created_at FROM photos 
                         WHERE couple_id = %s ORDER BY created_at DESC""", 
                      (session['couple_id'],))
        photos = cursor.fetchall()
        
        return render_template('photo_gallery.html', photos=photos)
        
    except Error as e:
        flash(f'Photo gallery error: {e}')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        connection.close()

@app.route('/upload_photo', methods=['POST'])
@login_required
def upload_photo():
    if 'photo' not in request.files:
        flash('No photo selected')
        return redirect(url_for('photo_gallery'))
    
    file = request.files['photo']
    caption = request.form.get('caption', '')
    
    if file.filename == '':
        flash('No photo selected')
        return redirect(url_for('photo_gallery'))
    
    if file:
        filename = secure_filename(f"{session['couple_id']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection error')
            return redirect(url_for('photo_gallery'))
        
        cursor = connection.cursor()
        
        try:
            cursor.execute("""INSERT INTO photos (couple_id, filename, caption, uploaded_by, created_at)
                             VALUES (%s, %s, %s, %s, %s)""",
                          (session['couple_id'], filename, caption, session['user_id'], datetime.datetime.now()))
            
            flash('Photo uploaded successfully!')
            
        except Error as e:
            flash(f'Error uploading photo: {e}')
        finally:
            cursor.close()
            connection.close()
    
    return redirect(url_for('photo_gallery'))

@app.route('/secret_chat')
@login_required
def secret_chat():
    return render_template('secret_chat.html')

@app.route('/get_messages')
@login_required
def get_messages():
    connection = get_db_connection()
    if not connection:
        return jsonify([])
    
    cursor = connection.cursor()
    
    try:
        # Delete expired messages
        cursor.execute("DELETE FROM secret_messages WHERE expires_at < NOW()")
        
        cursor.execute("""SELECT message, sender_id, created_at FROM secret_messages 
                         WHERE couple_id = %s ORDER BY created_at ASC""", 
                      (session['couple_id'],))
        messages = cursor.fetchall()
        
        return jsonify([{
            'message': msg[0],
            'sender_id': msg[1],
            'is_mine': msg[1] == session['user_id'],
            'created_at': msg[2].strftime('%H:%M')
        } for msg in messages])
        
    except Error as e:
        return jsonify([])
    finally:
        cursor.close()
        connection.close()

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    message = request.json['message']
    duration = request.json.get('duration', 300)  # 5 minutes default
    
    expires_at = datetime.datetime.now() + datetime.timedelta(seconds=duration)
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Database connection error'})
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""INSERT INTO secret_messages (couple_id, sender_id, message, expires_at, created_at)
                         VALUES (%s, %s, %s, %s, %s)""",
                      (session['couple_id'], session['user_id'], message, expires_at, datetime.datetime.now()))
        
        return jsonify({'success': True})
        
    except Error as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()
        connection.close()

@app.route('/couple_quiz')
@login_required
def couple_quiz():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('dashboard'))
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""SELECT id, question, answer, created_by, created_at FROM quiz_questions 
                         WHERE couple_id = %s ORDER BY created_at DESC""", 
                      (session['couple_id'],))
        questions = cursor.fetchall()
        
        return render_template('couple_quiz.html', questions=questions)
        
    except Error as e:
        flash(f'Quiz error: {e}')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        connection.close()

@app.route('/add_quiz_question', methods=['POST'])
@login_required
def add_quiz_question():
    question = request.form['question']
    answer = request.form['answer']
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('couple_quiz'))
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""INSERT INTO quiz_questions (couple_id, question, answer, created_by, created_at)
                         VALUES (%s, %s, %s, %s, %s)""",
                      (session['couple_id'], question, answer, session['user_id'], datetime.datetime.now()))
        
        flash('Quiz question added successfully!')
        
    except Error as e:
        flash(f'Error adding quiz question: {e}')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('couple_quiz'))

@app.route('/apology_box')
@login_required
def apology_box():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('dashboard'))
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""SELECT message, sender_id, is_read, created_at FROM apologies 
                         WHERE couple_id = %s ORDER BY created_at DESC""", 
                      (session['couple_id'],))
        apologies = cursor.fetchall()
        
        return render_template('apology_box.html', apologies=apologies)
        
    except Error as e:
        flash(f'Apology box error: {e}')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        connection.close()

@app.route('/send_apology', methods=['POST'])
@login_required
def send_apology():
    message = request.form['message']
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('apology_box'))
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""INSERT INTO apologies (couple_id, sender_id, message, created_at)
                         VALUES (%s, %s, %s, %s)""",
                      (session['couple_id'], session['user_id'], message, datetime.datetime.now()))
        
        flash('Apology sent!')
        
    except Error as e:
        flash(f'Error sending apology: {e}')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('apology_box'))

@app.route('/surprise_corner')
@login_required
def surprise_corner():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('dashboard'))
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""SELECT id, title, description, surprise_date, created_by, is_revealed, created_at 
                         FROM surprises WHERE couple_id = %s ORDER BY surprise_date DESC""", 
                      (session['couple_id'],))
        surprises = cursor.fetchall()
        
        # Add today's date for template comparison
        today = datetime.date.today()
        
        return render_template('surprise_corner.html', surprises=surprises, today=today)
        
    except Error as e:
        flash(f'Surprise corner error: {e}')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        connection.close()

@app.route('/add_surprise', methods=['POST'])
@login_required
def add_surprise():
    title = request.form['title']
    description = request.form['description']
    surprise_date = request.form['surprise_date']
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('surprise_corner'))
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""INSERT INTO surprises (couple_id, title, description, surprise_date, created_by, created_at)
                         VALUES (%s, %s, %s, %s, %s, %s)""",
                      (session['couple_id'], title, description, surprise_date, session['user_id'], datetime.datetime.now()))
        
        flash('Surprise planned successfully!')
        
    except Error as e:
        flash(f'Error planning surprise: {e}')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('surprise_corner'))

@app.route('/admin_panel')
@admin_required
def admin_panel():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('dashboard'))
    
    cursor = connection.cursor()
    
    try:
        # Get couple statistics
        cursor.execute("""SELECT 
                         (SELECT COUNT(*) FROM timeline WHERE couple_id = %s) as timeline_count,
                         (SELECT COUNT(*) FROM love_letters WHERE couple_id = %s) as letters_count,
                         (SELECT COUNT(*) FROM photos WHERE couple_id = %s) as photos_count,
                         (SELECT COUNT(*) FROM mood_tracker WHERE couple_id = %s) as moods_count""", 
                      (session['couple_id'], session['couple_id'], session['couple_id'], session['couple_id']))
        stats = cursor.fetchone()
        
        return render_template('admin_panel.html', stats=stats)
        
    except Error as e:
        flash(f'Admin panel error: {e}')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
