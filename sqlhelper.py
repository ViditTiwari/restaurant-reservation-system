import os
import MySQLdb
import config


# These environment variables are configured in app.yaml.
CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME')
CLOUDSQL_USER = os.environ.get('CLOUDSQL_USER')
CLOUDSQL_PASSWORD = os.environ.get('CLOUDSQL_PASSWORD')

class DBHelper:
    def __init__(self, dbname="reservation"):
        self.dbname = dbname
        self.conn = self.connect_to_cloudsql()

    def connect_to_cloudsql(self):
        # When deployed to App Engine, the `SERVER_SOFTWARE` environment variable
        # will be set to 'Google App Engine/version'.
        if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
            # Connect using the unix socket located at
            # /cloudsql/cloudsql-connection-name.
            cloudsql_unix_socket = os.path.join(
                '/cloudsql', CLOUDSQL_CONNECTION_NAME)

            db = MySQLdb.connect(
                unix_socket=cloudsql_unix_socket,
                user=CLOUDSQL_USER,
                passwd=CLOUDSQL_PASSWORD)

        # If the unix socket is unavailable, then try to connect using TCP. This
        # will work if you're running a local MySQL server or using the Cloud SQL
        # proxy, for example:
        #
        #   $ cloud_sql_proxy -instances=your-connection-name=tcp:3306
        #
        else:
            db = MySQLdb.connect(
                host='127.0.0.1', user=config.LOCAL_SQL_USERNAME, passwd=config.LOCAL_SQL_PASSWORD)

        return db

    def setup(self):
        db_stmt = "CREATE DATABASE IF NOT EXISTS {0}"
        tbl_stmt = "CREATE TABLE IF NOT EXISTS bookings (booking_no INT NOT NULL AUTO_INCREMENT, name VARCHAR(100), email VARCHAR(50), table_no INT(1), confirm INT(1) DEFAULT 0, owner INT, PRIMARY KEY (booking_no))"
        log_stmt = "CREATE TABLE IF NOT EXISTS logs (log_text TEXT)"
        use_stmt = "USE {0}"
        args = (self.dbname,)

        cursor = self.conn.cursor()
        cursor.execute(db_stmt.format(args[0]))
        cursor.execute(use_stmt.format(args[0]))
        cursor.execute(tbl_stmt)
        cursor.execute(log_stmt)
        self.conn.commit()

    def add_name(self, name, owner):
        stmt = "INSERT INTO bookings (name, owner) VALUES (%s, %s)"
        args = (name, owner)
        cursor = self.conn.cursor()
        cursor.execute(stmt, args)
        self.conn.commit()

    def add_email(self, email, owner):
        stmt = "UPDATE bookings SET email = (%s) WHERE owner = (%s)"
        args = (email, owner)
        cursor = self.conn.cursor()
        cursor.execute(stmt, args)
        self.conn.commit()

    def add_table_booking(self, table_no, owner):
        stmt = "UPDATE bookings SET table_no = (%s) WHERE owner = (%s)"
        args = (table_no, owner)
        cursor = self.conn.cursor()
        cursor.execute(stmt, args)
        self.conn.commit()

    def delete_booking(self, owner):
        stmt = "DELETE FROM bookings WHERE owner = (%s)"
        args = (owner,)
        cursor = self.conn.cursor()
        cursor.execute(stmt, args)
        self.conn.commit()

    def confirm_booking(self, owner):
        stmt = "UPDATE bookings SET confirm = (%s) WHERE owner = (%s)"
        args = (1, owner)
        cursor = self.conn.cursor()
        cursor.execute(stmt, args)
        self.conn.commit()

    def get_booked_tables(self):
        stmt = "SELECT DISTINCT table_no FROM bookings WHERE confirm = (%s)"
        args = (1,)
        cursor = self.conn.cursor()
        cursor.execute(stmt, args)
        return [x for x in cursor.fetchall()]

    def get_bookings(self, owner):
        stmt = "SELECT * FROM bookings WHERE owner = (%s)"
        args = (owner,)
        cursor = self.conn.cursor()
        cursor.execute(stmt, args)
        return [x for x in cursor.fetchall()]

    def add_log(self, log_text):
        stmt = "INSERT INTO logs VALUES (%s)"
        args = (log_text,)
        cursor = self.conn.cursor()
        cursor.execute(stmt, args)
        self.conn.commit()

