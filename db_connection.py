import mysql.connector
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="mysql",
        database="genai",
        port=3306
    )
print("database connected")