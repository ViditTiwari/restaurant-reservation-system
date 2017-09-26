import sqlite3


class DBHelper:

    def __init__(self, dbname="reservation.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)

    def setup(self):
        tblstmt = "CREATE TABLE IF NOT EXISTS bookings (name text, email text, table_no INT, confirm INT, owner text)"
        itemidx = "CREATE INDEX IF NOT EXISTS bookingIndex ON bookings (name ASC)" 
        ownidx = "CREATE INDEX IF NOT EXISTS ownIndex ON bookings (owner ASC)"
        # aquery = "INSERT INTO bookings VALUES(?,?,?,?,?)"
        # args = ('ABC','abc@gmail.com',1,1,'123')
        # args1 = ('ABC','abc@gmail.com',2,1,'123')
        self.conn.execute(tblstmt)
        self.conn.execute(itemidx)
        self.conn.execute(ownidx)
        # self.conn.execute(aquery, args)
        # self.conn.execute(aquery, args1)
        self.conn.commit()

    def add_name(self, name, owner):
        stmt = "INSERT INTO bookings (name, owner) VALUES (?, ?)"
        args = (name, owner)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def add_email(self, email, owner):
        stmt = "UPDATE bookings SET email = (?) WHERE owner = (?)"
        args = (email, owner)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def add_table_booking(self, table_no, owner):
        stmt = "UPDATE bookings SET table_no = (?) WHERE owner = (?)"
        args = (table_no, owner)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_booking(self, owner):
        stmt = "DELETE FROM bookings WHERE owner = (?)"
        args = (owner,)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def confirm_booking(self, owner):
        stmt = "UPDATE bookings SET confirm = (?) WHERE owner = (?)"
        args = (1, owner)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_booked_tables(self):
        stmt = "SELECT DISTINCT table_no FROM bookings WHERE confirm = (?)"
        args = (1,)
        return [x for x in self.conn.execute(stmt, args)]

    def get_bookings(self, owner):
        stmt = "SELECT * FROM bookings WHERE owner = (?)"
        args = (owner,)
        return [x for x in self.conn.execute(stmt, args)]

    
            




