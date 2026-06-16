import json
from database.db import get_db

class Report:
    @staticmethod
    def create(user_id, idea_title, idea_description):
        """
        Creates a new validation report in pending state and returns its ID.
        """
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO validation_reports (user_id, idea_title, idea_description, status) VALUES (?, ?, ?, ?)",
                (user_id, idea_title, idea_description, 'pending')
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def update_status(report_id, status, error_message=None):
        """
        Updates the status and optional error message of a validation report.
        """
        conn = get_db()
        cursor = conn.cursor()
        try:
            if error_message:
                cursor.execute(
                    "UPDATE validation_reports SET status = ?, error_message = ? WHERE id = ?",
                    (status, error_message, report_id)
                )
            else:
                cursor.execute(
                    "UPDATE validation_reports SET status = ? WHERE id = ?",
                    (status, report_id)
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def update_agent_output(report_id, agent_name, output_content):
        """
        Updates specific agent text output columns securely.
        Allowed columns: market_research, competitor_analysis, customer_persona, revenue_model, swot_analysis
        """
        conn = get_db()
        cursor = conn.cursor()
        try:
            allowed_columns = {
                'market_research', 
                'competitor_analysis', 
                'customer_persona', 
                'revenue_model', 
                'swot_analysis'
            }
            if agent_name not in allowed_columns:
                raise ValueError(f"Invalid agent name column: {agent_name}")
            
            cursor.execute(
                f"UPDATE validation_reports SET {agent_name} = ? WHERE id = ?",
                (output_content, report_id)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def update_final(report_id, feasibility_scores, overall_score, final_report, pdf_path):
        """
        Finalizes the report state: saves scores, summary, PDF path, and marks status as completed.
        """
        conn = get_db()
        cursor = conn.cursor()
        try:
            scores_str = json.dumps(feasibility_scores) if isinstance(feasibility_scores, dict) else feasibility_scores
            cursor.execute(
                """UPDATE validation_reports 
                   SET feasibility_scores = ?, overall_score = ?, final_report = ?, pdf_path = ?, status = 'completed', completed_at = CURRENT_TIMESTAMP 
                   WHERE id = ?""",
                (scores_str, overall_score, final_report, pdf_path, report_id)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get(report_id):
        """
        Fetches a report dict by ID.
        """
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM validation_reports WHERE id = ?", (report_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            print(f"Error fetching report {report_id}: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_by_user(user_id):
        """
        Fetches all reports for a specific user, sorted from newest to oldest.
        """
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM validation_reports WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching reports for user {user_id}: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def delete(report_id):
        """
        Deletes a validation report.
        """
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM validation_reports WHERE id = ?", (report_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
