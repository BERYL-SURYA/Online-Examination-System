import secrets
import string
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
app = Flask(__name__)

load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")


# HOME PAGE
@app.route('/')
def home():
    return render_template('index.html')


# STUDENT REGISTRATION
@app.route('/student-register', methods=['GET', 'POST'])
def student_register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for('student_register'))

        hashed_password = generate_password_hash(password)

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            query = """
                INSERT INTO Students
                (name, email, password, department)
                VALUES (%s, %s, %s, %s)
            """

            cursor.execute(query, (
                name, email, hashed_password, department
            ))

            connection.commit()

            flash("Registration successful! Please login.", "success")

            return redirect(url_for('student_login'))

        except Exception:
            connection.rollback()
            flash("Email already registered or registration failed.", "error")

        finally:
            cursor.close()
            connection.close()

    return render_template('student_register.html')


# STUDENT LOGIN
@app.route('/student-login', methods=['GET', 'POST'])
def student_login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            query = "SELECT * FROM Students WHERE email = %s"

            cursor.execute(query, (email,))

            student = cursor.fetchone()

            if student and check_password_hash(student['password'], password):

                session['student_id'] = student['student_id']
                session['student_name'] = student['name']

                return redirect(url_for('student_dashboard'))

            else:
                flash("Invalid email or password!", "error")

        finally:
            cursor.close()
            connection.close()

    return render_template('student_login.html')


# STUDENT DASHBOARD
@app.route('/student-dashboard')
def student_dashboard():

    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    return render_template(
        'student_dashboard.html',
        name=session['student_name']
    )


# STUDENT LOGOUT
@app.route('/student-logout')
def student_logout():

    session.clear()

    return redirect(url_for('home'))


# ADMIN LOGIN

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            query = "SELECT * FROM Admin WHERE username = %s"

            cursor.execute(query, (username,))

            admin = cursor.fetchone()

            if admin and check_password_hash(admin['password'], password):

                session.clear()

                session['admin_id'] = admin['admin_id']
                session['admin_username'] = admin['username']

                return redirect(url_for('admin_dashboard'))

            else:
                flash("Invalid username or password!", "error")

        finally:
            cursor.close()
            connection.close()

    return render_template('admin_login.html')


# ADMIN DASHBOARD

@app.route('/admin-dashboard')
def admin_dashboard():

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    return render_template(
        'admin_dashboard.html',
        username=session['admin_username']
    )


# ADMIN LOGOUT

@app.route('/admin-logout')
def admin_logout():

    session.clear()

    return redirect(url_for('home'))

# CREATE EXAMINATION

@app.route('/create-exam', methods=['GET', 'POST'])
def create_exam():

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':

        exam_name = request.form['exam_name']
        subject = request.form['subject']

        duration = request.form['duration']
        total_marks = request.form['total_marks']

        # Generate unique exam code
        characters = string.ascii_uppercase + string.digits

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            while True:

                exam_code = ''.join(
                    secrets.choice(characters)
                    for _ in range(8)
                )

                cursor.execute(
                    "SELECT exam_id FROM Exams WHERE exam_code = %s",
                    (exam_code,)
                )

                if cursor.fetchone() is None:
                    break

            query = """
                INSERT INTO Exams
                (exam_name, exam_code, subject,
                 duration, total_marks, status)
                VALUES (%s, %s, %s, %s, %s, 'Draft')
            """

            cursor.execute(query, (
                exam_name,
                exam_code,
                subject,
                duration,
                total_marks
            ))

            connection.commit()

            exam = {
                'exam_name': exam_name,
                'exam_code': exam_code,
                'subject': subject,
                'duration': duration,
                'total_marks': total_marks
            }

            return render_template(
                'exam_created.html',
                exam=exam
            )

        except Exception:
            connection.rollback()
            flash("Unable to create examination.", "error")
            return redirect(url_for('create_exam'))

        finally:
            cursor.close()
            connection.close()

    return render_template('create_exam.html')


@app.route('/manage-questions')
def manage_questions():

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        query = """
            SELECT E.*,
            COUNT(Q.question_id) AS question_count
            FROM Exams E
            LEFT JOIN Questions Q
            ON E.exam_id = Q.exam_id
            GROUP BY E.exam_id
            ORDER BY E.created_at DESC
        """

        cursor.execute(query)

        exams = cursor.fetchall()

        return render_template(
            'manage_questions.html',
            exams=exams
        )

    finally:
        cursor.close()
        connection.close()


@app.route('/add-question/<int:exam_id>', methods=['GET', 'POST'])
def add_question(exam_id):

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            "SELECT * FROM Exams WHERE exam_id = %s",
            (exam_id,)
        )

        exam = cursor.fetchone()

        if not exam:
            return "Examination not found", 404

        if exam['status'] != 'Draft':
            return "Questions cannot be modified after publishing.", 403

        if request.method == 'POST':

            question_text = request.form['question_text']

            option_a = request.form['option_a']
            option_b = request.form['option_b']
            option_c = request.form['option_c']
            option_d = request.form['option_d']

            correct_answer = request.form['correct_answer']

            if correct_answer not in ['A', 'B', 'C', 'D']:
                flash("Invalid correct answer!", "error")
                return redirect(
                    url_for('add_question', exam_id=exam_id)
                )

            query = """
                INSERT INTO Questions
                (exam_id, question_text, option_a,
                 option_b, option_c, option_d, correct_answer)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(query, (
                exam_id,
                question_text,
                option_a,
                option_b,
                option_c,
                option_d,
                correct_answer
            ))

            connection.commit()

            flash("Question added successfully!", "success")

            return redirect(
                url_for('add_question', exam_id=exam_id)
            )

        return render_template(
            'add_question.html',
            exam=exam
        )

    finally:
        cursor.close()
        connection.close()

@app.route('/publish-exam/<int:exam_id>', methods=['POST'])
def publish_exam(exam_id):

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            "SELECT * FROM Exams WHERE exam_id = %s",
            (exam_id,)
        )

        exam = cursor.fetchone()

        if not exam:
            flash("Examination not found!", "error")
            return redirect(url_for('manage_questions'))

        cursor.execute(
            "SELECT COUNT(*) AS total FROM Questions WHERE exam_id = %s",
            (exam_id,)
        )

        result = cursor.fetchone()

        if result['total'] == 0:
            flash("Add questions before publishing!", "error")
            return redirect(url_for('manage_questions'))

        if exam['status'] != 'Draft':
            flash("Examination is already published!", "error")
            return redirect(url_for('manage_questions'))

        cursor.execute(
            "UPDATE Exams SET status = 'Published' WHERE exam_id = %s",
            (exam_id,)
        )

        connection.commit()

        flash("Examination published successfully!", "success")

    except Exception:
        connection.rollback()
        flash("Unable to publish examination!", "error")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('manage_questions'))

# STUDENT JOIN EXAMINATION

@app.route('/join-exam', methods=['GET', 'POST'])
def join_exam():

    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    if request.method == 'POST':

        exam_code = request.form['exam_code'].strip().upper()

        student_id = session['student_id']

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            # Check whether examination exists

            query = """
                SELECT *
                FROM Exams
                WHERE exam_code = %s
                AND status = 'Published'
            """

            cursor.execute(query, (exam_code,))

            exam = cursor.fetchone()

            if not exam:

                flash(
                    "Invalid exam code or examination is not published!",
                    "error"
                )

                return redirect(url_for('join_exam'))

            # Check whether student already joined

            query = """
                SELECT registration_id
                FROM Exam_Registrations
                WHERE student_id = %s
                AND exam_id = %s
            """

            cursor.execute(query, (
                student_id,
                exam['exam_id']
            ))

            registration = cursor.fetchone()

            if registration:

                return render_template(
                    'joined_exam.html',
                    exam=exam
                )

            # Register student for examination

            query = """
                INSERT INTO Exam_Registrations
                (student_id, exam_id)
                VALUES (%s, %s)
            """

            cursor.execute(query, (
                student_id,
                exam['exam_id']
            ))

            connection.commit()

            return render_template(
                'joined_exam.html',
                exam=exam
            )

        except Exception:

            connection.rollback()

            flash(
                "Something went wrong. Please try again.",
                "error"
            )

            return redirect(url_for('join_exam'))

        finally:

            cursor.close()
            connection.close()

    return render_template('join_exam.html')


@app.route('/start-exam/<int:exam_id>', methods=['POST'])
def start_exam(exam_id):

    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    student_id = session['student_id']

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # Check student registration and exam status

        query = """
            SELECT E.*
            FROM Exams E

            JOIN Exam_Registrations R
            ON E.exam_id = R.exam_id

            WHERE E.exam_id = %s
            AND R.student_id = %s
            AND E.status = 'Published'
        """

        cursor.execute(query, (exam_id, student_id))

        exam = cursor.fetchone()

        if not exam:
            return "You are not registered for this examination.", 403

        # Check whether an attempt already exists

        cursor.execute("""
            SELECT *
            FROM Exam_Attempts
            WHERE student_id = %s AND exam_id = %s
        """, (student_id, exam_id))

        attempt = cursor.fetchone()

        if attempt:

            if attempt['status'] == 'Submitted':
                return "You have already submitted this examination."

            if attempt['expires_at'] <= datetime.now():
                return redirect(
                    url_for('submit_exam',
                            attempt_id=attempt['attempt_id'])
                )

        else:

            # Create a new examination attempt

            cursor.execute("""
                INSERT INTO Exam_Attempts
                (student_id, exam_id, expires_at)
                VALUES (
                    %s,
                    %s,
                    DATE_ADD(NOW(), INTERVAL %s MINUTE)
                )
            """, (
                student_id,
                exam_id,
                exam['duration']
            ))

            connection.commit()

            attempt_id = cursor.lastrowid

            cursor.execute("""
                SELECT *
                FROM Exam_Attempts
                WHERE attempt_id = %s
            """, (attempt_id,))

            attempt = cursor.fetchone()

        return redirect(
            url_for(
                'take_exam',
                attempt_id=attempt['attempt_id']
            )
        )

    except Exception:

        connection.rollback()

        return "Unable to start examination.", 500

    finally:

        cursor.close()
        connection.close()

@app.route('/take-exam/<int:attempt_id>')
def take_exam(attempt_id):

    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # GET EXAMINATION AND ATTEMPT DETAILS

        cursor.execute("""
            SELECT
                A.*,
                A.status AS attempt_status,
                E.exam_name,
                E.subject,
                E.total_marks

            FROM Exam_Attempts A

            JOIN Exams E
            ON A.exam_id = E.exam_id

            WHERE A.attempt_id = %s
            AND A.student_id = %s
        """, (
            attempt_id,
            session['student_id']
        ))

        attempt = cursor.fetchone()


        # CHECK ATTEMPT

        if not attempt:

            return "Examination attempt not found.", 404


        # CHECK EXAMINATION STATUS

        if attempt['attempt_status'] != 'In Progress':

            return "This examination has already been submitted."


        # GET QUESTIONS

        cursor.execute("""
            SELECT
                question_id,
                question_text,
                option_a,
                option_b,
                option_c,
                option_d

            FROM Questions

            WHERE exam_id = %s

            ORDER BY question_id
        """, (attempt['exam_id'],))

        questions = cursor.fetchall()


        if not questions:

            return "No questions available.", 404


        # GET EXAM EXPIRY TIME

        cursor.execute("""
            SELECT
                UNIX_TIMESTAMP(expires_at) * 1000 AS expiry

            FROM Exam_Attempts

            WHERE attempt_id = %s
        """, (attempt_id,))

        expiry_data = cursor.fetchone()

        if not expiry_data or expiry_data['expiry'] is None:

            return "Examination expiry time not found.", 500

        expiry = int(expiry_data['expiry'])


        # DISPLAY EXAMINATION PAGE

        return render_template(
            'take_exam.html',

            exam=attempt,

            attempt=attempt,

            questions=questions,

            expires_at_ms=expiry
        )


    finally:

        cursor.close()
        connection.close()
@app.route('/submit-exam/<int:attempt_id>', methods=['POST'])
def submit_exam(attempt_id):

    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # Verify examination attempt

        cursor.execute("""
            SELECT *
            FROM Exam_Attempts
            WHERE attempt_id = %s
            AND student_id = %s
            FOR UPDATE
        """, (
            attempt_id,
            session['student_id']
        ))

        attempt = cursor.fetchone()

        if not attempt:
            return "Invalid examination attempt.", 404

        if attempt['status'] != 'In Progress':
            return "Examination already submitted."

        # Fetch correct answers on the backend

        cursor.execute("""
            SELECT question_id, correct_answer
            FROM Questions
            WHERE exam_id = %s
        """, (attempt['exam_id'],))

        questions = cursor.fetchall()

        score = 0

        for question in questions:

            question_id = question['question_id']

            selected_answer = request.form.get(
                f'answer_{question_id}'
            )

            if selected_answer not in ['A', 'B', 'C', 'D']:
                selected_answer = None

            if selected_answer:

                cursor.execute("""
                    INSERT INTO Student_Answers
                    (attempt_id, question_id, selected_answer)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    selected_answer = VALUES(selected_answer)
                """, (
                    attempt_id,
                    question_id,
                    selected_answer
                ))

            if selected_answer == question['correct_answer']:
                score += 1

        # Check server-side expiry

        cursor.execute("""
            SELECT expires_at <= NOW() AS time_expired
            FROM Exam_Attempts
            WHERE attempt_id = %s
        """, (attempt_id,))

        time_check = cursor.fetchone()

        if time_check['time_expired']:

            # Answers submitted after expiry are not accepted.
            score = 0

            cursor.execute("""
                DELETE FROM Student_Answers
                WHERE attempt_id = %s
            """, (attempt_id,))

        # Save final score

        cursor.execute("""
            UPDATE Exam_Attempts

            SET score = %s,
                status = 'Submitted',
                submitted_at = NOW()

            WHERE attempt_id = %s
        """, (
            score,
            attempt_id
        ))

        connection.commit()

        return redirect(
            url_for(
                'exam_result',
                attempt_id=attempt_id
            )
        )

    except Exception:

        connection.rollback()

        return "Unable to submit examination.", 500

    finally:

        cursor.close()
        connection.close()

@app.route('/exam-result/<int:attempt_id>')
def exam_result(attempt_id):

    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # Get examination details

        cursor.execute("""
            SELECT A.*, E.exam_name, E.subject
            FROM Exam_Attempts A

            JOIN Exams E
            ON A.exam_id = E.exam_id

            WHERE A.attempt_id = %s
            AND A.student_id = %s
            AND A.status = 'Submitted'
        """, (
            attempt_id,
            session['student_id']
        ))

        attempt = cursor.fetchone()

        if not attempt:
            return "Result not found.", 404


        # Count total questions

        cursor.execute("""
            SELECT COUNT(*) AS total_questions
            FROM Questions
            WHERE exam_id = %s
        """, (attempt['exam_id'],))

        total_questions = cursor.fetchone()['total_questions']


        # Count answered questions

        cursor.execute("""
            SELECT COUNT(*) AS answered
            FROM Student_Answers
            WHERE attempt_id = %s
            AND selected_answer IS NOT NULL
        """, (attempt_id,))

        answered = cursor.fetchone()['answered']


        # Get correct answers

        cursor.execute("""
            SELECT COUNT(*) AS correct
            FROM Student_Answers SA

            JOIN Questions Q
            ON SA.question_id = Q.question_id

            WHERE SA.attempt_id = %s
            AND SA.selected_answer = Q.correct_answer
        """, (attempt_id,))

        correct = cursor.fetchone()['correct']


        # Calculate results

        wrong = answered - correct

        unanswered = total_questions - answered

        score = attempt['score']

        percentage = (
            (score / total_questions) * 100
            if total_questions > 0 else 0
        )

        # Pass mark: 40%

        result_status = (
            "PASS" if percentage >= 40 else "FAIL"
        )


        return render_template(
            'exam_result.html',

            attempt=attempt,

            total_questions=total_questions,

            correct=correct,

            wrong=wrong,

            unanswered=unanswered,

            score=score,

            percentage=round(percentage, 2),

            result_status=result_status
        )


    finally:

        cursor.close()
        connection.close()

@app.route('/admin-results')
def admin_results():

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # TOTAL EXAMINATIONS

        cursor.execute("""
            SELECT COUNT(*) AS total_exams
            FROM Exams
        """)

        total_exams = cursor.fetchone()['total_exams']


        # TOTAL REGISTERED STUDENTS

        cursor.execute("""
            SELECT COUNT(*) AS total_students
            FROM Students
        """)

        total_students = cursor.fetchone()['total_students']


        # TOTAL COMPLETED EXAMINATIONS

        cursor.execute("""
            SELECT COUNT(*) AS total_attempts
            FROM Exam_Attempts
            WHERE status = 'Submitted'
        """)

        total_attempts = cursor.fetchone()['total_attempts']


        # FETCH INDIVIDUAL STUDENT RESULTS

        cursor.execute("""
            SELECT
                A.attempt_id,
                S.student_id,
                S.name,
                S.email,
                E.exam_name,
                E.subject,
                A.score,
                A.status,
                A.submitted_at,
                COUNT(Q.question_id) AS total_questions,

                ROUND(
                    A.score * 100.0 /
                    NULLIF(COUNT(Q.question_id), 0),
                    1
                ) AS percentage

            FROM Exam_Attempts A

            JOIN Students S
                ON A.student_id = S.student_id

            JOIN Exams E
                ON A.exam_id = E.exam_id

            LEFT JOIN Questions Q
                ON A.exam_id = Q.exam_id

            WHERE A.status = 'Submitted'

            GROUP BY
                A.attempt_id,
                S.student_id,
                S.name,
                S.email,
                E.exam_name,
                E.subject,
                A.score,
                A.status,
                A.submitted_at

            ORDER BY A.submitted_at DESC
        """)

        results = cursor.fetchall()


        return render_template(
            'admin_results.html',

            results=results,

            total_exams=total_exams,

            total_students=total_students,

            total_attempts=total_attempts
        )


    finally:

        cursor.close()
        connection.close()

@app.route('/student-result-details/<int:attempt_id>')
def student_result_details(attempt_id):

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # GET STUDENT AND EXAM DETAILS

        cursor.execute("""
            SELECT
                A.attempt_id,
                A.score,
                A.status,
                A.submitted_at,
                S.name,
                S.email,
                E.exam_name,
                E.subject,
                E.total_marks

            FROM Exam_Attempts A

            JOIN Students S
                ON A.student_id = S.student_id

            JOIN Exams E
                ON A.exam_id = E.exam_id

            WHERE A.attempt_id = %s
        """, (attempt_id,))

        result = cursor.fetchone()

        if not result:
            return "Result not found.", 404

        if result['status'] != 'Submitted':
            return "This examination has not been submitted.", 400


        # GET QUESTIONS AND STUDENT ANSWERS

        cursor.execute("""
            SELECT
                Q.question_id,
                Q.question_text,
                Q.option_a,
                Q.option_b,
                Q.option_c,
                Q.option_d,
                Q.correct_answer,
                SA.selected_answer

            FROM Questions Q

            JOIN Exam_Attempts A
                ON Q.exam_id = A.exam_id

            LEFT JOIN Student_Answers SA
                ON SA.question_id = Q.question_id
                AND SA.attempt_id = A.attempt_id

            WHERE A.attempt_id = %s

            ORDER BY Q.question_id
        """, (attempt_id,))

        questions = cursor.fetchall()


        # CALCULATE CORRECT, WRONG AND UNANSWERED

        correct = 0
        wrong = 0
        unanswered = 0

        for q in questions:

            if not q['selected_answer']:

                unanswered += 1

            elif q['selected_answer'] == q['correct_answer']:

                correct += 1

            else:

                wrong += 1


        total_questions = len(questions)

        percentage = (
            (correct / total_questions) * 100
            if total_questions > 0 else 0
        )

        return render_template(
            'student_result_details.html',
            result=result,
            questions=questions,
            correct=correct,
            wrong=wrong,
            unanswered=unanswered,
            total_questions=total_questions,
            percentage=round(percentage, 1)
        )


    finally:

        cursor.close()
        connection.close()

# MANAGE EXAMINATIONS

@app.route('/manage-exams')
def manage_exams():

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT *
            FROM Exams
            ORDER BY created_at DESC
        """)

        exams = cursor.fetchall()

        return render_template(
            'manage_exams.html',
            exams=exams
        )

    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    app.run(debug=True)