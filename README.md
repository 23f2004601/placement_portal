Placement Portal Application

A web-based Placement Portal Application built using Flask and SQLite that allows Admin, Companies, and Students to manage campus recruitment activities efficiently.

📌 Problem Statement

Institutes often manage placement activities using spreadsheets and emails, which leads to:

Difficulty in tracking student applications

Duplicate registrations

Lack of centralized approval system

Poor historical record maintenance

This application provides a structured system for managing companies, placement drives, student applications, and final placements.

🚀 Features
👨‍💼 Admin (Institute Placement Cell)

View dashboard statistics

Approve or reject company registrations

Approve or reject placement drives

Search students and companies

Blacklist/deactivate accounts

View all applications and placement history

🏢 Company

Register and create profile

Login after admin approval

Create placement drives

View applicants per drive

Shortlist / Select / Reject students

Close placement drives

🎓 Student

Self-registration and login

Update profile and upload resume

View approved placement drives

Apply for drives

Track application status

View placement history

🔒 Core Functionalities Implemented

Role-Based Access Control (Admin / Student / Company)

Prevent duplicate applications (UNIQUE constraint)

Only approved companies can create drives

Students can view only approved drives

Complete placement history tracking

Secure password hashing

Foreign key constraints for data integrity

🛠 Technologies Used
Technology	Purpose
Flask	Backend framework
SQLite	Database
Jinja2	Template rendering
HTML5	Structure
CSS3	Styling
Bootstrap 5	Responsive UI
Werkzeug	Password hashing
