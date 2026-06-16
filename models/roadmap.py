import json
from database.db import get_db


class Roadmap:
    """DB operations for startup roadmaps and task completion tracking."""

    # ── Roadmap CRUD ────────────────────────────────────────────────────────

    @staticmethod
    def create(report_id, roadmap_data):
        """
        Saves a new roadmap for a report. roadmap_data is a dict.
        Returns the new roadmap id.
        """
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO startup_roadmaps (report_id, roadmap_data) VALUES (?, ?)",
                (report_id, json.dumps(roadmap_data))
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_by_report(report_id):
        """
        Returns the roadmap row for a report, or None if not generated yet.
        Parses roadmap_data from JSON string to dict.
        """
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT * FROM startup_roadmaps WHERE report_id = ? ORDER BY created_at DESC LIMIT 1",
                (report_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            result = dict(row)
            if result.get('roadmap_data'):
                try:
                    result['roadmap_data'] = json.loads(result['roadmap_data'])
                except Exception:
                    result['roadmap_data'] = {}
            return result
        except Exception as e:
            print(f"Error fetching roadmap for report {report_id}: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def delete_by_report(report_id):
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM startup_roadmaps WHERE report_id = ?", (report_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ── Task Progress ────────────────────────────────────────────────────────

    @staticmethod
    def set_task_complete(roadmap_id, task_key, completed):
        """
        Upsert a task completion record.
        task_key: unique string like "month_1_task_0" or "phase_3_task_1"
        completed: bool
        """
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO roadmap_task_progress (roadmap_id, task_key, completed)
                   VALUES (?, ?, ?)
                   ON CONFLICT(roadmap_id, task_key)
                   DO UPDATE SET completed = excluded.completed, updated_at = CURRENT_TIMESTAMP""",
                (roadmap_id, task_key, 1 if completed else 0)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_all_progress(roadmap_id):
        """
        Returns a dict {task_key: bool} for all tracked tasks of a roadmap.
        """
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT task_key, completed FROM roadmap_task_progress WHERE roadmap_id = ?",
                (roadmap_id,)
            )
            rows = cursor.fetchall()
            return {row['task_key']: bool(row['completed']) for row in rows}
        except Exception as e:
            print(f"Error fetching progress for roadmap {roadmap_id}: {e}")
            return {}
        finally:
            conn.close()

    @staticmethod
    def get_completion_stats(roadmap_id, total_tasks):
        """
        Returns (completed_count, total_tasks, percentage).
        """
        progress = Roadmap.get_all_progress(roadmap_id)
        completed = sum(1 for v in progress.values() if v)
        pct = round((completed / total_tasks * 100) if total_tasks > 0 else 0, 1)
        return completed, total_tasks, pct
