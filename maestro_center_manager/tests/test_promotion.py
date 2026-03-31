import os
import sys
# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from database import DatabaseManager

def test_promotion():
    db = DatabaseManager('test_maestro.db')
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO grades (name) VALUES ('Grade 1'), ('Grade 2')")
        cursor.execute("INSERT INTO students (name, grade_id) VALUES ('Alice', 1)")
        student_id = cursor.lastrowid

        # Add history
        cursor.execute("INSERT INTO sessions (grade_id, session_date, session_price) VALUES (1, '2023-01-01', 100)")
        session_id = cursor.lastrowid
        cursor.execute("INSERT INTO attendance (student_id, session_id, status) VALUES (?, ?, 'Present')", (student_id, session_id))
        cursor.execute("INSERT INTO invoices (student_id, total_amount, paid_amount, date) VALUES (?, 100, 100, '2023-01-01')", (student_id,))

    db.promote_student(student_id, 2)

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT grade_id FROM students WHERE id = ?", (student_id,))
        new_grade = cursor.fetchone()[0]
        assert new_grade == 2, f"Expected grade 2, got {new_grade}"

    history = db.get_student_history(student_id)
    assert len(history['attendance']) == 1, "Attendance history should be preserved"
    assert len(history['payments']) == 1, "Payment history should be preserved"

    print("Promotion and History Preservation Test Passed!")
    os.remove('test_maestro.db')

if __name__ == "__main__":
    test_promotion()
