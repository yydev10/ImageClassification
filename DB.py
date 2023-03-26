import pymysql
import os
from dotenv import load_dotenv

load_dotenv()
 
class Database():
    def __init__(self):
        self.db = pymysql.connect(host=os.getenv("DB_HOST"),
                                  user=os.getenv("DB_USER"),
                                  password=os.getenv("DB_PASS"),
                                  db=os.getenv("DB_NAME"),
                                  charset='utf8')
        self.cursor = self.db.cursor(pymysql.cursors.DictCursor)
 
    def execute(self, query, args={}):
        self.cursor.execute(query, args)  
 
    def executeOne(self, query, args={}):
        self.cursor.execute(query, args)
        row = self.cursor.fetchone()
        return row
 
    def executeAll(self, query, args={}):
        self.cursor.execute(query, args)
        row = self.cursor.fetchall()
        return row
 
    def commit(self):
        self.db.commit()