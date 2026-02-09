import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    # Connect to default 'postgres' database to create new db
    try:
        con = psycopg2.connect(
            dbname='postgres',
            user='postgre',
            host='localhost',
            password='postgre'
        )
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'lara_db'")
        exists = cur.fetchone()
        
        if not exists:
            print("Creating database lara_db...")
            cur.execute('CREATE DATABASE lara_db')
            print("Database created successfully!")
        else:
            print("Database lara_db already exists.")
            
        cur.close()
        con.close()
    except Exception as e:
        print(f"Error creating database: {e}")

if __name__ == "__main__":
    create_database()
