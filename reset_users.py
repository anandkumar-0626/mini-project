import hashlib
import mysql.connector

mysql_root_password = "anand" 

users_to_create = [
    ("anand@8056", "anand", "Client"),
    ("bala@5680", "bala", "Client"),
    ("kumar@159", "kumar", "Client"),
    ("monica@951","monica","Client"),
    ("swetha@519","swetha","Client"),
    ("sanjay@789","sanjay","Client"),
    ("deepa@897","deepa","Client"),
    ("vijay@007","vijay","Client"),
    ("mari@456","mari","Client"),
    ("swathi@0626","swathi","Client"),
    ("mani@111", "mani@123", "Support"),
    ("reyan@222", "reyan@123", "Support"),
]
# ----------------------------------------------------

def hash_password(password):
    """Converts a plain password into a secure hash."""
    return hashlib.sha256(str(password).encode()).hexdigest()

def clear_and_recreate_users():
    """Safely deletes all data and recreates users by handling foreign key constraints."""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=mysql_root_password,
            database="query_system"
        )
        cursor = conn.cursor()

        print("--- Starting: Deleting all old data (Safe Mode) ---")
        
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        print("  -> Foreign key checks disabled temporarily.")
        
        
        cursor.execute("TRUNCATE TABLE queries;")
        print("  -> 'queries' table cleared successfully.")
        
        cursor.execute("TRUNCATE TABLE users;")
        print("  -> 'users' table cleared successfully.")
        
        
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        print("  -> Foreign key checks re-enabled.")
        
        print("SUCCESS: All old users and their queries have been deleted.")
        print("-" * 30)

        
        print("--- Starting: Creating new users ---")
        for username, plain_password, role in users_to_create:
            hashed_pw = hash_password(plain_password)
            cursor.execute(
                "INSERT INTO users (username, hashed_password, role) VALUES (%s, %s, %s)",
                (username, hashed_pw, role)
            )
            print(f"  -> SUCCESS: User '{username}' ({role}) created.")

        conn.commit()

    except mysql.connector.Error as err:
        print(f"FATAL DATABASE ERROR: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("-" * 30)
            print("Process finished. Database connection closed.")


if __name__=='__main__':
    clear_and_recreate_users()