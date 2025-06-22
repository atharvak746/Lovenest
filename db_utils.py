from database import db_manager
import datetime
from typing import Optional, List, Dict, Any

class CoupleService:
    @staticmethod
    def create_couple(code: str) -> int:
        """Create a new couple and return the couple ID"""
        query = "INSERT INTO couples (code, created_at) VALUES (%s, %s)"
        return db_manager.execute_query(query, (code, datetime.datetime.now()))
    
    @staticmethod
    def get_couple_by_code(code: str) -> Optional[Dict]:
        """Get couple information by code"""
        query = "SELECT id, code, love_days, created_at FROM couples WHERE code = %s"
        return db_manager.execute_query(query, (code,), fetch='one', dictionary=True)
    
    @staticmethod
    def update_love_days(couple_id: int, days: int) -> int:
        """Update the love days counter for a couple"""
        query = "UPDATE couples SET love_days = %s WHERE id = %s"
        return db_manager.execute_query(query, (days, couple_id))

class UserService:
    @staticmethod
    def create_user(name: str, email: str, password: str, role: str, couple_id: int, is_admin: bool = False) -> int:
        """Create a new user"""
        query = """INSERT INTO users (name, email, password, role, couple_id, is_admin, created_at) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        return db_manager.execute_query(
            query, 
            (name, email, password, role, couple_id, is_admin, datetime.datetime.now())
        )
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        """Get user by email"""
        query = "SELECT id, name, email, password, role, couple_id, is_admin FROM users WHERE email = %s"
        return db_manager.execute_query(query, (email,), fetch='one', dictionary=True)
    
    @staticmethod
    def get_partner(couple_id: int, user_id: int) -> Optional[Dict]:
        """Get partner information"""
        query = "SELECT id, name, role FROM users WHERE couple_id = %s AND id != %s"
        return db_manager.execute_query(query, (couple_id, user_id), fetch='one', dictionary=True)
    
    @staticmethod
    def count_users_in_couple(couple_id: int) -> int:
        """Count users in a couple"""
        query = "SELECT COUNT(*) as count FROM users WHERE couple_id = %s"
        result = db_manager.execute_query(query, (couple_id,), fetch='one', dictionary=True)
        return result['count'] if result else 0

class TimelineService:
    @staticmethod
    def add_entry(couple_id: int, title: str, description: str, created_by: int) -> int:
        """Add a timeline entry"""
        query = """INSERT INTO timeline (couple_id, title, description, created_by, created_at)
                   VALUES (%s, %s, %s, %s, %s)"""
        return db_manager.execute_query(
            query, 
            (couple_id, title, description, created_by, datetime.datetime.now())
        )
    
    @staticmethod
    def get_entries(couple_id: int, limit: Optional[int] = None) -> List[Dict]:
        """Get timeline entries for a couple"""
        query = """SELECT id, title, description, created_by, created_at 
                   FROM timeline WHERE couple_id = %s ORDER BY created_at DESC"""
        if limit:
            query += f" LIMIT {limit}"
        return db_manager.execute_query(query, (couple_id,), fetch='all', dictionary=True)

class LoveLetterService:
    @staticmethod
    def create_letter(couple_id: int, title: str, content: str, created_by: int) -> int:
        """Create a love letter"""
        query = """INSERT INTO love_letters (couple_id, title, content, created_by, created_at)
                   VALUES (%s, %s, %s, %s, %s)"""
        return db_manager.execute_query(
            query, 
            (couple_id, title, content, created_by, datetime.datetime.now())
        )
    
    @staticmethod
    def get_letters(couple_id: int) -> List[Dict]:
        """Get all love letters for a couple"""
        query = """SELECT id, title, content, created_by, created_at 
                   FROM love_letters WHERE couple_id = %s ORDER BY created_at DESC"""
        return db_manager.execute_query(query, (couple_id,), fetch='all', dictionary=True)

class MoodService:
    @staticmethod
    def add_mood(couple_id: int, user_id: int, mood: str, note: str = '') -> int:
        """Add a mood entry"""
        query = """INSERT INTO mood_tracker (couple_id, user_id, mood, note, created_at)
                   VALUES (%s, %s, %s, %s, %s)"""
        return db_manager.execute_query(
            query, 
            (couple_id, user_id, mood, note, datetime.datetime.now())
        )
    
    @staticmethod
    def get_user_moods(couple_id: int, user_id: int, limit: int = 30) -> List[Dict]:
        """Get mood entries for a specific user"""
        query = """SELECT mood, note, created_at FROM mood_tracker 
                   WHERE couple_id = %s AND user_id = %s 
                   ORDER BY created_at DESC LIMIT %s"""
        return db_manager.execute_query(query, (couple_id, user_id, limit), fetch='all', dictionary=True)
    
    @staticmethod
    def get_mood_stats(couple_id: int, days: int = 7) -> List[Dict]:
        """Get mood statistics for the past N days"""
        query = """SELECT mood, COUNT(*) as count FROM mood_tracker 
                   WHERE couple_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                   GROUP BY mood"""
        return db_manager.execute_query(query, (couple_id, days), fetch='all', dictionary=True)

class PhotoService:
    @staticmethod
    def add_photo(couple_id: int, filename: str, caption: str, uploaded_by: int) -> int:
        """Add a photo"""
        query = """INSERT INTO photos (couple_id, filename, caption, uploaded_by, created_at)
                   VALUES (%s, %s, %s, %s, %s)"""
        return db_manager.execute_query(
            query, 
            (couple_id, filename, caption, uploaded_by, datetime.datetime.now())
        )
    
    @staticmethod
    def get_photos(couple_id: int) -> List[Dict]:
        """Get all photos for a couple"""
        query = """SELECT id, filename, caption, uploaded_by, created_at 
                   FROM photos WHERE couple_id = %s ORDER BY created_at DESC"""
        return db_manager.execute_query(query, (couple_id,), fetch='all', dictionary=True)

class SecretMessageService:
    @staticmethod
    def send_message(couple_id: int, sender_id: int, message: str, expires_at: datetime.datetime) -> int:
        """Send a secret message"""
        query = """INSERT INTO secret_messages (couple_id, sender_id, message, expires_at, created_at)
                   VALUES (%s, %s, %s, %s, %s)"""
        return db_manager.execute_query(
            query, 
            (couple_id, sender_id, message, expires_at, datetime.datetime.now())
        )
    
    @staticmethod
    def get_messages(couple_id: int) -> List[Dict]:
        """Get active secret messages"""
        # First, clean up expired messages
        db_manager.execute_query("DELETE FROM secret_messages WHERE expires_at < NOW()")
        
        # Then get active messages
        query = """SELECT message, sender_id, created_at FROM secret_messages 
                   WHERE couple_id = %s ORDER BY created_at ASC"""
        return db_manager.execute_query(query, (couple_id,), fetch='all', dictionary=True)

# Utility functions
def get_couple_statistics(couple_id: int) -> Dict[str, int]:
    """Get comprehensive statistics for a couple"""
    stats = {}
    
    # Timeline entries
    result = db_manager.execute_query(
        "SELECT COUNT(*) as count FROM timeline WHERE couple_id = %s", 
        (couple_id,), fetch='one', dictionary=True
    )
    stats['timeline_count'] = result['count'] if result else 0
    
    # Love letters
    result = db_manager.execute_query(
        "SELECT COUNT(*) as count FROM love_letters WHERE couple_id = %s", 
        (couple_id,), fetch='one', dictionary=True
    )
    stats['letters_count'] = result['count'] if result else 0
    
    # Photos
    result = db_manager.execute_query(
        "SELECT COUNT(*) as count FROM photos WHERE couple_id = %s", 
        (couple_id,), fetch='one', dictionary=True
    )
    stats['photos_count'] = result['count'] if result else 0
    
    # Mood entries
    result = db_manager.execute_query(
        "SELECT COUNT(*) as count FROM mood_tracker WHERE couple_id = %s", 
        (couple_id,), fetch='one', dictionary=True
    )
    stats['moods_count'] = result['count'] if result else 0
    
    return stats
