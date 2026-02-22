import sqlite3
from werkzeug.security import generate_password_hash

def create_admin():
    conn = sqlite3.connect('placement.db')
    cursor = conn.cursor()

    email = 'prachitaralkar15@gmail.com'
    password = 'prachi1512'
    password_hash=generate_password_hash(password)

    cursor.execute("SELECT id FROM users WHERE email = ?",(email,))
    if cursor.fetchone():
        print("Admin exits")
    else:
        cursor.execute(
            "INSERT INTO users(email , password_hash,role) VALUES (?,?,?)"
            ,(email,password_hash,'admin')
        )
        conn.commit()
        print("Admin Created ")
    conn.close()
if __name__ == '__main__':
    create_admin()