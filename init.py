import psycopg2
import os

DATABASE_URL = os.environ['DATABASE_URL']
if __name__ == "__main__":
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()

    # Creamos la tabla si no existe
    cur.execute("DROP TABLE IF EXISTS usuario;")
    cur.execute("CREATE TABLE usuario ( \
        carnet CHAR(8) PRIMARY KEY, \
        password VARCHAR(255), \
        chat_id VARCHAR(255),\
        CHECK (carnet ~ '[0-9][0-9]-[0-9][0-9][0-9][0-9][0-9]'));")

    conn.commit()
    cur.close()
    conn.close()