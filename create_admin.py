from database import get_db_connection
from werkzeug.security import generate_password_hash

username = "admin"
password = "admin12345"

hashed_password = generate_password_hash(password)

connection = get_db_connection()
cursor = connection.cursor()

query = """
INSERT INTO Admin (username, password)
VALUES (%s, %s)
"""

cursor.execute(query, (username, hashed_password))

connection.commit()

print("Admin account created successfully!")

cursor.close()
connection.close()