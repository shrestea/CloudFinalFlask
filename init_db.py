import os
import psycopg2

def get_db_connection(query, values = ()):
    conn = psycopg2.connect(
        host="cc-psql-databse-server.postgres.database.azure.com",
        database="consumer",
        user="CCGroup47",
        password="CCFinalPass!")
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute(query, values)
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result

def post_db_connection(query, values = ()):
    conn = psycopg2.connect(
        host="cc-psql-databse-server.postgres.database.azure.com",
        database="consumer",
        user="CCGroup47",
        password="CCFinalPass!")
    cur = conn.cursor()
    cur.execute(query, values)
    conn.commit()
    cur.close()
    conn.close()


