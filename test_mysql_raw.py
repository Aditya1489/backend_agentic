import pymysql
import os

HOST = "localhost"
USER = "root"
PASSWORD = "Ashish@2001"
DB = "agent"

# Dummy hash for testing
DUMMY_HASH = "hashed_agent_123"
EMAIL = "ashishkumar93040086@gmail.com"

def test_mysql():
    print(f"Connecting to MySQL at {HOST}...")
    try:
        conn = pymysql.connect(host=HOST, user=USER, password=PASSWORD)
        print("Connection successful! Database exists check...")
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB}")
        conn.close()

        conn = pymysql.connect(host=HOST, user=USER, password=PASSWORD, database=DB)
        with conn.cursor() as cursor:
            print("Creating users table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            print("Action complete.")
        conn.commit()
        conn.close()
        print("Success!")
    except Exception as e:
        print(f"MySQL Error: {e}")

if __name__ == "__main__":
    test_mysql()
