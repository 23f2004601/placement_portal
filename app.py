from flask import Flask, render_template, request, redirect, url_for, flash, g
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-super-secret-key-change-this-123'
app.config['DATABASE'] = 'placement.db'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, email, role, active=True):
        self.id = id
        self.email = email
        self.role = role
        self._is_active = active  # ✅ FIXED - use private attribute

    @property
    def is_active(self):
        return self._is_active

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user:
        return User(user['id'], user['email'], user['role'], user['is_active'])
    return None

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            if user['is_active']:
                login_user(User(user['id'], user['email'], user['role'], 1))
                flash('Login successful!', 'success')
                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('student_dashboard'))
            else:
                flash('Account deactivated!', 'danger')
        else:
            flash('Invalid credentials!', 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        full_name = request.form['full_name']
        roll_number = request.form['roll_number']
        
        db = get_db()
        try:
            cursor = db.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
                              (email, password, 'student'))
            user_id = cursor.lastrowid
            db.execute("INSERT INTO students (id, full_name, roll_number) VALUES (?, ?, ?)",
                     (user_id, full_name, roll_number))
            db.commit()
            flash('Student registered! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email or roll number exists!', 'danger')
    
    return render_template('auth/register_student.html')

@app.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        company_name = request.form['company_name']
        
        db = get_db()
        try:
            cursor = db.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
                              (email, password, 'company'))
            user_id = cursor.lastrowid
            db.execute("INSERT INTO companies (id, company_name) VALUES (?, ?)",
                     (user_id, company_name))
            db.commit()
            flash('Company registered! Awaiting approval.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Registration failed!', 'danger')
    
    return render_template('auth/register_company.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Admin access only!', 'danger')
        return redirect(url_for('login'))
    
    db = get_db()
    stats = {
        'students': db.execute('SELECT COUNT(*) FROM students').fetchone()[0],
        'companies': db.execute('SELECT COUNT(*) FROM companies').fetchone()[0],
        'drives': db.execute('SELECT COUNT(*) FROM placement_drives').fetchone()[0] or 0,
        'applications': db.execute('SELECT COUNT(*) FROM applications').fetchone()[0] or 0
    }
    return render_template('admin/dashboard.html', stats=stats)

# Admin: Manage Companies
@app.route('/admin/companies')
@login_required
def admin_companies():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    db = get_db()
    query = "SELECT c.*, u.email FROM companies c JOIN users u ON c.id = u.id WHERE 1=1"
    params = []
    
    if search:
        query += " AND (c.company_name LIKE ? OR u.email LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%'])
    
    query += " ORDER BY c.id DESC"
    companies = db.execute(query, params).fetchall()
    
    return render_template('admin/companies.html', companies=companies, search=search)

@app.route('/admin/companies/<int:company_id>/approve', methods=['POST'])
@login_required
def approve_company(company_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    db = get_db()
    db.execute("UPDATE companies SET approval_status = 'approved' WHERE id = ?", (company_id,))
    db.commit()
    flash('Company approved successfully!', 'success')
    return redirect(url_for('admin_companies'))

@app.route('/admin/companies/<int:company_id>/reject', methods=['POST'])
@login_required
def reject_company(company_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    db = get_db()
    db.execute("UPDATE companies SET approval_status = 'rejected' WHERE id = ?", (company_id,))
    db.commit()
    flash('Company rejected!', 'warning')
    return redirect(url_for('admin_companies'))

@app.route('/admin/companies/<int:company_id>/blacklist', methods=['POST'])
@login_required
def blacklist_company(company_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    db = get_db()
    db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (company_id,))
    db.commit()
    flash('Company blacklisted!', 'danger')
    return redirect(url_for('admin_companies'))

# Admin: Manage Students (similar pattern)
@app.route('/admin/students')
@login_required
def admin_students():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    search = request.args.get('search', '')
    
    db = get_db()
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


if __name__ == '__main__':
    app.run(debug=True)
