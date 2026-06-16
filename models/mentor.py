import json
from database.db import get_db


class MentorChat:
    """
    Handles all DB operations for the AI Startup Mentor chat history.
    """

    @staticmethod
    def create_message(report_id, role, content, structured_response=None):
        """
        Saves a single chat message (user or assistant) to the database.
        role: 'user' | 'assistant'
        structured_response: optional JSON string for assistant responses
        """
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO mentor_chats
                   (report_id, role, content, structured_response)
                   VALUES (?, ?, ?, ?)""",
                (report_id, role, content,
                 json.dumps(structured_response) if structured_response else None)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_history(report_id, limit=20):
        """
        Returns the last `limit` messages for a given report, oldest first.
        """
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """SELECT * FROM mentor_chats
                   WHERE report_id = ?
                   ORDER BY created_at ASC
                   LIMIT ?""",
                (report_id, limit)
            )
            rows = cursor.fetchall()
            msgs = []
            for row in rows:
                m = dict(row)
                if m.get('structured_response'):
                    try:
                        m['structured_response'] = json.loads(m['structured_response'])
                    except Exception:
                        pass
                msgs.append(m)
            return msgs
        except Exception as e:
            print(f"Error fetching mentor history for report {report_id}: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def clear_history(report_id):
        """Deletes all chat messages for a report (used on report delete cascade)."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM mentor_chats WHERE report_id = ?", (report_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
