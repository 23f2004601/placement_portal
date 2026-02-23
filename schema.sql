-- USERS: common login table for admin, student, company
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,          -- 'admin', 'student', 'company'
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- STUDENTS: extra info for users with role = 'student'
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,      -- also FK to users.id
    full_name TEXT NOT NULL,
    roll_number TEXT UNIQUE NOT NULL,
    department TEXT,
    year INTEGER,
    cgpa REAL,
    phone TEXT,
    resume_path TEXT,
    FOREIGN KEY (id) REFERENCES users (id)
);

-- COMPANIES: extra info for users with role = 'company'
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY,      -- also FK to users.id
    company_name TEXT NOT NULL,
    hr_name TEXT,
    hr_email TEXT,
    phone TEXT,
    website TEXT,
    approval_status TEXT NOT NULL DEFAULT 'pending', -- pending/approved/rejected/blacklisted
    FOREIGN KEY (id) REFERENCES users (id)
);

-- PLACEMENT DRIVES: job positions / placement drives
CREATE TABLE IF NOT EXISTS placement_drives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    job_title TEXT NOT NULL,
    job_description TEXT,
    eligibility_criteria TEXT,
    application_deadline DATE,
    status TEXT NOT NULL DEFAULT 'pending', -- pending/approved/closed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies (id)
);

-- APPLICATIONS: student applies to a drive
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    drive_id INTEGER NOT NULL,
    application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'applied', -- applied/shortlisted/selected/rejected
    UNIQUE (student_id, drive_id),          -- prevent multiple applications
    FOREIGN KEY (student_id) REFERENCES students (id),
    FOREIGN KEY (drive_id) REFERENCES placement_drives (id)
);

-- PLACEMENTS: final placement offers based on applications
CREATE TABLE IF NOT EXISTS placements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,           -- FK to applications.id
    offer_date DATE,
    joining_date DATE,
    package_ctc REAL,
    remarks TEXT,
    FOREIGN KEY (application_id) REFERENCES applications (id)
);

-- Companies table (add approval_status if missing)
ALTER TABLE companies ADD COLUMN approval_status TEXT DEFAULT 'pending';

-- Placement Drives
CREATE TABLE IF NOT EXISTS placement_drives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    job_title TEXT NOT NULL,
    description TEXT,
    eligibility TEXT,
    deadline DATE,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Applications
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    drive_id INTEGER NOT NULL,
    applied_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'applied',
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (drive_id) REFERENCES placement_drives(id),
    UNIQUE(student_id, drive_id)
);

