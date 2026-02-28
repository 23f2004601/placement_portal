# These are all the basic imports 
from flask import Flask, render_template, request, redirect, url_for, flash, g
from flask_login import (
    LoginManager,# he login system la contro lryla use kela ahe 
    UserMixin,# he login system la user class banvayla use kela ahe 
    login_user as flask_login_user,
    logout_user as flask_logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
# Database connections 
import sqlite3
import os # used for saving resume file 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-super-secret-key-change-this-123'
app.config['DATABASE'] = 'placement.db'

login_user_manager = LoginManager()
login_user_manager.init_app(app)
login_user_manager.login_view = 'login_user'
# ha class login user la represent krto 
class User(UserMixin):
    def __init__(self, id, email, role, active=True):
        self.id = id
        self.email = email
        self.role = role
        self._is_active = active

    @property
    def is_active(self):
        return self._is_active

@login_user_manager.user_loader
def get_user_by_id(user_id):
    db = get_database()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user:
        return User(user['id'], user['email'], user['role'], user['is_active'] == 1)
    return None

def get_database():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_database(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
# login page la return krta 
@app.route('/')
def home():
    return redirect(url_for('login_user'))

# hys purn function made user details submit krto database check hota 
@app.route('/login_user', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        db = get_database()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            if not user['is_active']:
                flash('Account deactivated!', 'danger')
            else:
                # company approve ahe ka nahi admin kdun he check krto 
                if user['role'] == 'company':
                    company = db.execute('SELECT approval_status FROM companies WHERE id = ?', (user['id'],)).fetchone()
                    if not company or company['approval_status'] != 'approved':
                        flash('Company not approved by admin yet.', 'warning')
                        return redirect(url_for('login_user'))

                flask_login_user(User(user['id'], user['email'], user['role'], user['is_active'] == 1))
                flash('login_user successful!', 'success')
                if user['role'] == 'admin':
                    return redirect(url_for('admin_home'))
                elif user['role'] == 'company':
                    return redirect(url_for('company_main_page'))
                elif user['role'] == 'student':
                    return redirect(url_for('student_main_page'))
        else:
            flash('Invalid credentials!', 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout_user')
@login_required
def logout_user():
    flask_logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login_user'))
# student registration 
@app.route('/register/student', methods=['GET', 'POST'])
def reg_stud():
    if request.method == 'POST':
        email = request.form['email']
        raw_password = request.form['password']
        confirm_password = request.form.get('confirm_password', '')
        if raw_password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('auth/register_student.html')

        password = generate_password_hash(raw_password)
        full_name = request.form['full_name']
        roll_number = request.form['roll_number']
        
        db = get_database()
        try:
            cursor = db.execute("INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, ?, 1)",
                              (email, password, 'student'))
            user_id = cursor.lastrowid
            db.execute("INSERT INTO students (id, full_name, roll_number) VALUES (?, ?, ?)",
                     (user_id, full_name, roll_number))
            db.commit()
            flash('Student registered! Please login_user.', 'success')
            return redirect(url_for('login_user'))
        except sqlite3.IntegrityError:
            flash('Email or roll number exists!', 'danger')
    
    return render_template('auth/register_student.html')
 # new company registration 
@app.route('/register/company', methods=['GET', 'POST'])
def reg_company():
    if request.method == 'POST':
        email = request.form['email']
        raw_password = request.form['password']
        confirm_password = request.form.get('confirm_password', '')
        if raw_password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('auth/register_company.html')

        password = generate_password_hash(raw_password)
        company_name = request.form['company_name']
        
        db = get_database()
        try:
            cursor = db.execute("INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, ?, 1)",
                              (email, password, 'company'))
            user_id = cursor.lastrowid
            db.execute("INSERT INTO companies (id, company_name, approval_status) VALUES (?, ?, 'pending')",
                     (user_id, company_name))
            db.commit()
            flash('Company registered! Awaiting approval.', 'success')
            return redirect(url_for('login_user'))
        except:
            flash('Registration failed!', 'danger')
    
    return render_template('auth/register_company.html')

# Admin routes 
@app.route('/admin/dashboard')
@login_required
def admin_home():
    if current_user.role != 'admin':
        flash('Admin access only!', 'danger')
        return redirect(url_for('login_user'))
    
    db = get_database()
    stats = {
        'students': db.execute('SELECT COUNT(*) FROM students').fetchone()[0],
        'companies': db.execute('SELECT COUNT(*) FROM companies').fetchone()[0],
        'drives': db.execute('SELECT COUNT(*) FROM placement_drives').fetchone()[0] or 0,
        'applications': db.execute('SELECT COUNT(*) FROM applications').fetchone()[0] or 0
    }
    return render_template('admin/dashboard.html', stats=stats)
# ethe admin la saglya company dista 
@app.route('/admin/companies')
@login_required
def view_company():
    if current_user.role != 'admin':
        return redirect(url_for('login_user'))
    
    search = request.args.get('search', '').strip()
    db = get_database()
    query = "SELECT c.*, u.email FROM companies c JOIN users u ON c.id = u.id WHERE 1=1"
    params = []
    
    if search:
        # Allow searching by ID, name, or email
        query += " AND (CAST(c.id AS TEXT) LIKE ? OR c.company_name LIKE ? OR u.email LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like])
    
    query += " ORDER BY c.id DESC"
    companies = db.execute(query, params).fetchall()
    
    return render_template('admin/companies.html', companies=companies, search=search)
# company approve krto 
@app.route('/admin/companies/<int:company_id>/approve', methods=['POST'])
@login_required
def company_swikaar_karo(company_id):
    if current_user.role != 'admin':
        return redirect(url_for('login_user'))
    
    db = get_database()
    db.execute("UPDATE companies SET approval_status = 'approved' WHERE id = ?", (company_id,))
    db.commit()
    flash('Company approved successfully!', 'success')
    return redirect(url_for('view_company'))
# company reject krto 
@app.route('/admin/companies/<int:company_id>/reject', methods=['POST'])
@login_required
def company_aswikaar_karo(company_id):
    if current_user.role != 'admin':
        return redirect(url_for('login_user'))
    
    db = get_database()
    db.execute("UPDATE companies SET approval_status = 'rejected' WHERE id = ?", (company_id,))
    db.commit()
    flash('Company rejected!', 'warning')
    return redirect(url_for('view_company'))
# company la blacklist krto 
@app.route('/admin/companies/<int:company_id>/blacklist', methods=['POST'])
@login_required
def company_blacklist(company_id):
    if current_user.role != 'admin':
        return redirect(url_for('login_user'))
    
    db = get_database()
    db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (company_id,))
    db.commit()
    flash('Company blacklisted!', 'danger')
    return redirect(url_for('view_company'))


@app.route('/admin/companies/<int:company_id>/delete', methods=['POST'])
@login_required
def delete_company(company_id):
    if current_user.role != 'admin':
        return redirect(url_for('login_user'))
    
    db = get_database()
    # Delete applications for this company's drives
    db.execute(
        """
        DELETE FROM applications 
        WHERE drive_id IN (SELECT id FROM placement_drives WHERE company_id = ?)
        """,
        (company_id,),
    )
    # Delete drives, company record, then user record
    db.execute("DELETE FROM placement_drives WHERE company_id = ?", (company_id,))
    db.execute("DELETE FROM companies WHERE id = ?", (company_id,))
    db.execute("DELETE FROM users WHERE id = ?", (company_id,))
    db.commit()
    flash('Company deleted permanently!', 'danger')
    return redirect(url_for('view_company'))

# company details edit kru shkto 
@app.route('/admin/companies/<int:company_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_company(company_id):
    if current_user.role != 'admin':
        return redirect(url_for('login_user'))
    
    db = get_database()
    company = db.execute(
        """
        SELECT c.*, u.email 
        FROM companies c 
        JOIN users u ON c.id = u.id 
        WHERE c.id = ?
        """,
        (company_id,),
    ).fetchone()
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('view_company'))

    if request.method == 'POST':
        company_name = request.form['company_name']
        email = request.form['email']

        db.execute(
            "UPDATE companies SET company_name = ? WHERE id = ?",
            (company_name, company_id),
        )
        db.execute(
            "UPDATE users SET email = ? WHERE id = ?",
            (email, company_id),
        )
        db.commit()
        flash('Company updated successfully!', 'success')
        return redirect(url_for('view_company'))

    return render_template('admin/company_edit.html', company=company)
# all aboyt drives 
@app.route('/admin/drives')
@login_required
def drive_suchi():
    if current_user.role != 'admin': return redirect(url_for('login_user'))
    
    db = get_database()
    search = request.args.get('search', '')
    query = """
        SELECT d.*, c.company_name FROM placement_drives d 
        JOIN companies c ON d.company_id = c.id WHERE 1=1
    """
    params = []
    if search:
        query += " AND (d.job_title LIKE ? OR c.company_name LIKE ?)"
        params.extend([f'%{search}%']*2)
    query += " ORDER BY d.created_at DESC"
    drives = db.execute(query, params).fetchall()
    return render_template('admin/drives.html', drives=drives, search=search)
# accept drive 
@app.route('/admin/drives/<int:drive_id>/approve', methods=['POST'])
@login_required
def drive_swikaar_karo(drive_id):
    if current_user.role != 'admin': return redirect(url_for('login_user'))
    db = get_database()
    db.execute("UPDATE placement_drives SET status = 'approved' WHERE id = ?", (drive_id,))
    db.commit()
    flash('Drive approved!', 'success')
    return redirect(url_for('drive_suchi'))
# reject drive 
@app.route('/admin/drives/<int:drive_id>/reject', methods=['POST'])
@login_required
def drive_aswikaar_karo(drive_id):
    if current_user.role != 'admin': return redirect(url_for('login_user'))
    db = get_database()
    db.execute("UPDATE placement_drives SET status = 'rejected' WHERE id = ?", (drive_id,))
    db.commit()
    flash('Drive rejected!', 'warning')
    return redirect(url_for('drive_suchi'))

 # shows students list 
@app.route('/admin/students')
@login_required
def vidyarthi_list():
    if current_user.role != 'admin':
        return redirect(url_for('login_user'))
    
    search = request.args.get('search', '')
    db = get_database()
    query = """
        SELECT s.*, u.email, u.is_active 
        FROM students s 
        JOIN users u ON s.id = u.id 
        WHERE 1=1
    """
    params = []
    
    if search:
        query += " AND (s.full_name LIKE ? OR s.roll_number LIKE ? OR u.email LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    
    query += " ORDER BY s.id DESC"
    students = db.execute(query, params).fetchall()
    
    return render_template('admin/students.html', students=students, search=search)

@app.route('/admin/students/<int:student_id>/deactivate', methods=['POST'])
@login_required
def vidhyarthi_nikalo(student_id):
    if current_user.role != 'admin':
        return redirect(url_for('login_user'))
    
    db = get_database()
    db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (student_id,))
    db.commit()
    flash('Student blacklisted!', 'warning')
    return redirect(url_for('vidyarthi_list'))


@app.route('/admin/students/<int:student_id>/delete', methods=['POST'])
@login_required
def delete_student(student_id):
    if current_user.role != 'admin':
        return redirect(url_for('login_user'))
    
    db = get_database()
    # Remove all related data, then the user record
    db.execute("DELETE FROM applications WHERE student_id = ?", (student_id,))
    db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.execute("DELETE FROM users WHERE id = ?", (student_id,))
    db.commit()
    flash('Student deleted permanently!', 'danger')
    return redirect(url_for('vidyarthi_list'))


@app.route('/admin/students/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    if current_user.role != 'admin':
        return redirect(url_for('login_user'))
    
    db = get_database()
    student = db.execute(
        """
        SELECT s.*, u.email 
        FROM students s 
        JOIN users u ON s.id = u.id 
        WHERE s.id = ?
        """,
        (student_id,),
    ).fetchone()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('vidyarthi_list'))

    if request.method == 'POST':
        full_name = request.form['full_name']
        roll_number = request.form['roll_number']
        email = request.form['email']

        db.execute(
            "UPDATE students SET full_name = ?, roll_number = ? WHERE id = ?",
            (full_name, roll_number, student_id),
        )
        db.execute(
            "UPDATE users SET email = ? WHERE id = ?",
            (email, student_id),
        )
        db.commit()
        flash('Student updated successfully!', 'success')
        return redirect(url_for('vidyarthi_list'))

    return render_template('admin/student_edit.html', student=student)

@app.route('/admin/applications')
@login_required
def admin_applis():
    if current_user.role != 'admin':
        return redirect(url_for('login_user'))
    
    search = request.args.get('search', '')
    db = get_database()
    query = """
        SELECT a.*, d.job_title, c.company_name, s.full_name, s.roll_number
        FROM applications a
        JOIN placement_drives d ON a.drive_id = d.id
        JOIN companies c ON d.company_id = c.id
        JOIN students s ON a.student_id = s.id
        WHERE 1=1
    """
    params = []
    
    if search:
        query += " AND (s.full_name LIKE ? OR s.roll_number LIKE ? OR c.company_name LIKE ? OR d.job_title LIKE ?)"
        params.extend([f'%{search}%']*4)
    
    query += " ORDER BY a.application_date DESC"
    applications = db.execute(query, params).fetchall()
    
    return render_template('admin/applications.html', applications=applications, search=search)

# Company routes 
@app.route('/company/dashboard')
@login_required
def company_main_page():
    if current_user.role != 'company':
        flash('Company access only!', 'danger')
        return redirect(url_for('login_user'))
    
    db = get_database()
    company = db.execute('SELECT approval_status FROM companies WHERE id = ?', 
                        (current_user.id,)).fetchone()
    
    if company and company['approval_status'] != 'approved':
        flash('Company approval pending! Contact admin.', 'warning')
        return render_template('company/pending.html')
    
    stats = {
        'drives': db.execute('SELECT COUNT(*) FROM placement_drives WHERE company_id = ?', 
                           (current_user.id,)).fetchone()[0],
        'applications': db.execute("""
            SELECT COUNT(*) FROM applications a 
            JOIN placement_drives d ON a.drive_id = d.id 
            WHERE d.company_id = ?
        """, (current_user.id,)).fetchone()[0]
    }
    
    company_info = db.execute('SELECT * FROM companies WHERE id = ?', 
                             (current_user.id,)).fetchone()
    
    return render_template('company/dashboard.html', stats=stats, company=company_info)

@app.route('/company/post-job', methods=['GET', 'POST'])
@login_required
def job_dalo():
    if current_user.role != 'company':
        return redirect(url_for('login_user'))
    
    db = get_database()
    status = db.execute('SELECT approval_status FROM companies WHERE id = ?', 
                       (current_user.id,)).fetchone()
    if status['approval_status'] != 'approved':
        flash('Company not approved!', 'danger')
        return redirect(url_for('company_main_page'))
    
    if request.method == 'POST':
        job_title = request.form['job_title']
        description = request.form['description']
        eligibility = request.form['eligibility']
        deadline = request.form['deadline']
        
        db.execute("""
            INSERT INTO placement_drives (company_id, job_title, job_description, eligibility_criteria, application_deadline, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (current_user.id, job_title, description, eligibility, deadline))
        db.commit()
        flash('Job posted! Awaiting admin approval.', 'success')
        return redirect(url_for('drive_list'))
    
    return render_template('company/post_job.html')

@app.route('/company/drives')
@login_required
def drive_list():
    if current_user.role != 'company':
        return redirect(url_for('login_user'))
    
    db = get_database()
    drives = db.execute("""
        SELECT * FROM placement_drives 
        WHERE company_id = ? ORDER BY created_at DESC
    """, (current_user.id,)).fetchall()
    
    return render_template('company/manage_drives.html', drives=drives)

@app.route('/company/drives/<int:drive_id>/update', methods=['POST'])
@login_required
def drive_status(drive_id):
    if current_user.role != 'company':
        return redirect(url_for('login_user'))
    
    new_status = request.form['status']
    db = get_database()
    db.execute("UPDATE placement_drives SET status = ? WHERE id = ? AND company_id = ?",
              (new_status, drive_id, current_user.id))
    db.commit()
    flash(f'Drive status updated to {new_status}!', 'success')
    return redirect(url_for('drive_list'))

@app.route('/company/applications/<int:drive_id>')
@login_required
def company_applis(drive_id):
    if current_user.role != 'company':
        return redirect(url_for('login_user'))
    
    db = get_database()
    drive = db.execute('SELECT * FROM placement_drives WHERE id = ?', (drive_id,)).fetchone()
    if not drive or drive['company_id'] != current_user.id:
        flash('Access denied!', 'danger')
        return redirect(url_for('drive_list'))
    
    applications = db.execute("""
        SELECT a.*, s.full_name, s.roll_number, s.cgpa, s.skills, s.resume_path
        FROM applications a
        JOIN students s ON a.student_id = s.id
        WHERE a.drive_id = ?
        ORDER BY a.application_date DESC
    """, (drive_id,)).fetchall()
    
    return render_template('company/applications.html', 
                         applications=applications, drive=drive)

@app.route('/company/applications/<int:app_id>/update', methods=['POST'])
@login_required
def application_status(app_id):
    if current_user.role != 'company':
        return redirect(url_for('login_user'))
    
    new_status = request.form['status']
    db = get_database()
    
    app = db.execute("""
        SELECT a.drive_id FROM applications a
        JOIN placement_drives d ON a.drive_id = d.id
        WHERE a.id = ? AND d.company_id = ?
    """, (app_id, current_user.id)).fetchone()
    
    if app:
        db.execute("UPDATE applications SET status = ? WHERE id = ?", (new_status, app_id))
        db.commit()
        flash(f'Status updated to: {new_status.title()}!', 'success')
        return redirect(url_for('company_applis', drive_id=app['drive_id']))
    
    flash('Access denied!', 'danger')
    return redirect(url_for('drive_list'))

# Student routes 
def approved_drives(search_term=''):
    """Internal helper to fetch approved drives for student views."""
    db = get_database()
    query = """
        SELECT 
            d.id, 
            d.job_title, 
            d.job_description AS description, 
            d.eligibility_criteria AS eligibility, 
            d.application_deadline AS deadline, 
            c.company_name
        FROM placement_drives d
        JOIN companies c ON d.company_id = c.id
        WHERE d.status = 'approved'
    """
    params = []
    if search_term:
        query += " AND (d.job_title LIKE ? OR c.company_name LIKE ? OR d.eligibility_criteria LIKE ?)"
        like = f'%{search_term}%'
        params.extend([like, like, like])
    query += " ORDER BY d.created_at DESC"
    return get_database().execute(query, params).fetchall()

@app.route('/student/dashboard')
@login_required
def student_main_page():
    if current_user.role != 'student':
        return redirect(url_for('login_user'))

    search = request.args.get('search', '')
    jobs = approved_drives(search)

    db = get_database()
    applications = db.execute("""
        SELECT 
            a.*, 
            d.job_title, 
            d.status AS drive_status,
            d.application_deadline AS deadline, 
            c.company_name
        FROM applications a
        JOIN placement_drives d ON a.drive_id = d.id
        JOIN companies c ON d.company_id = c.id
        WHERE a.student_id = ?
        ORDER BY a.application_date DESC
    """, (current_user.id,)).fetchall()

    return render_template('student/dashboard.html', jobs=jobs, applications=applications, search=search)

@app.route('/student/jobs')
@login_required
def jobs_list():
    if current_user.role != 'student':
        return redirect(url_for('login_user'))

    search = request.args.get('search', '')
    jobs = approved_drives(search)
    return render_template('student/jobs.html', jobs=jobs, search=search)

@app.route('/student/profile', methods=['GET', 'POST'])
@login_required
def stud_prof():
    if current_user.role != 'student':
        return redirect(url_for('login_user'))
    
    db = get_database()
    student_id = current_user.id

    student = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    
    if request.method == 'POST':
        full_name = request.form['full_name']
        roll_number = request.form['roll_number']
        phone = request.form.get('phone', '')
        department = request.form.get('department', '')
        year = request.form.get('year') or None
        cgpa = request.form.get('cgpa') or None
        skills = request.form.get('skills', '')
        
        resume_file = request.files.get('resume')
        resume_path = student['resume_path'] if student and 'resume_path' in student.keys() else None
        if resume_file and resume_file.filename:
            os.makedirs('static/uploads', exist_ok=True)
            resume_filename = f"resume_{student_id}_{resume_file.filename}"
            resume_path = os.path.join('static', 'uploads', resume_filename)
            resume_file.save(resume_path)

        if cgpa is not None and cgpa != '':
            try:
                cgpa = float(cgpa)
            except ValueError:
                cgpa = None

        if year is not None and year != '':
            try:
                year = int(year)
            except ValueError:
                year = None

        if student:
            db.execute("""
                UPDATE students
                SET full_name = ?, roll_number = ?, phone = ?, department = ?, year = ?, cgpa = ?, skills = ?, resume_path = ?
                WHERE id = ?
            """, (full_name, roll_number, phone, department, year, cgpa, skills, resume_path, student_id))
        else:
            db.execute("""
                INSERT INTO students (id, full_name, roll_number, phone, department, year, cgpa, skills, resume_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (student_id, full_name, roll_number, phone, department, year, cgpa, skills, resume_path))
        db.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('stud_prof'))

    student = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    return render_template('student/profile.html', student=student)

@app.route('/student/apply/<int:drive_id>', methods=['GET', 'POST'])
@login_required
def stud_apply(drive_id):
    if current_user.role != 'student':
        return redirect(url_for('login_user'))

    db = get_database()
    drive = db.execute("""
        SELECT d.*, c.company_name
        FROM placement_drives d
        JOIN companies c ON d.company_id = c.id
        WHERE d.id = ? AND d.status = 'approved'
    """, (drive_id,)).fetchone()

    if not drive:
        flash('Drive not found or not available.', 'danger')
        return redirect(url_for('jobs_list'))

    if request.method == 'POST':
        try:
            db.execute(
                "INSERT INTO applications (student_id, drive_id) VALUES (?, ?)",
                (current_user.id, drive_id)
            )
            db.commit()
            flash('Application submitted successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('You have already applied for this drive.', 'warning')
        return redirect(url_for('stud_applications'))

    return render_template('student/apply.html', drive=drive)

@app.route('/student/applications')
@login_required
def stud_applications():
    if current_user.role != 'student':
        return redirect(url_for('login_user'))

    db = get_database()
    applications = db.execute("""
        SELECT 
            a.*, 
            d.job_title, 
            d.status AS drive_status,
            d.application_deadline AS deadline, 
            c.company_name
        FROM applications a
        JOIN placement_drives d ON a.drive_id = d.id
        JOIN companies c ON d.company_id = c.id
        WHERE a.student_id = ?
        ORDER BY a.application_date DESC
    """, (current_user.id,)).fetchall()

    return render_template('student/my_applications.html', applications=applications)

if __name__ == '__main__':
    print("🚀 Starting Placement Portal...")
    app.run(debug=True, host='127.0.0.1', port=5000)
