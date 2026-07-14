import psycopg2

class Database:
    def __init__(self):
        self.connect = psycopg2.connect(
            dbname='Homeworkk',
            user='postgres',
            host='localhost',
            password='1685'
        )

    def manager(self, sql, *args, commit=False, fetchall=False, fetchone=False):
        with self.connect as connect:
            result = None
            with connect.cursor() as cursor:
                cursor.execute(sql, args)
                if commit:
                    connect.commit()
                elif fetchall:
                    result = cursor.fetchall()
                elif fetchone:
                    result = cursor.fetchone()
            return result

db = Database()