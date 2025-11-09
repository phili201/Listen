import pymysql
from pymysql.err import MySQLError as Error

def get_db():
    try:
        conn = pymysql.connect(
            host='nfb0-d.h.filess.io',
            database='Test_childrenbe',
            user='Test_childrenbe',
            password='cb0dbf8556485ceed6cca6d83bca699333685788',
            port=3306
        )
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None