import pymysql
from passlib.context import CryptContext
import os
from urllib.parse import urlparse

# URL provided by user
# mysql+pymysql://root:Ashish%402001@localhost:3306/agent
url = "mysql+pymysql://root:Ashish%402001@localhost:3306/agent"

# Parse URL (minimal parser)
# dialect+driver://username:password@host:port/database
# We'll just hardcode for the seed script to be 100% sure
HOST = "localhost"
USER = "root"
PASSWORD = "Ashish@2001"
DB = "agent"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
EMAIL = "ashishkumar93040086@gmail.com"
USER_PASSWORD = "agent@123"

def seed():
    print(f"Connecting to MySQL at {HOST}...")
    try:
        # Connect without DB first to create it if needed
        conn = pymysql.connect(host=HOST, user=USER, password=PASSWORD)
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB}")
        conn.close()

        # Connect to the database
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
            
            print(f"Checking for user {EMAIL}...")
            cursor.execute("SELECT id FROM users WHERE email=%s", (EMAIL,))
            user = cursor.fetchone()
            
            hashed_pw = pwd_context.hash(USER_PASSWORD)
            
            if not user:
                print("Inserting new user...")
                cursor.execute(
                    "INSERT INTO users (email, hashed_password) VALUES (%s, %s)",
                    (EMAIL, hashed_pw)
                )
                print("User inserted.")
            else:
                print("Updating user password...")
                cursor.execute(
                    "UPDATE users SET hashed_password=%s WHERE email=%s",
                    (hashed_pw, EMAIL)
                )
                print("User password updated.")
        
        conn.commit()
        conn.close()
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    seed()
