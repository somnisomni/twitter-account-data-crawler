import pymysql
from util import log

class Database:
  __connection: pymysql.Connection = None

  def __init__(self, host: str, port: int, user: str, password: str, database: str):
    self.__host = host
    self.__port = port
    self.__user = user
    self.__password = password
    self.__database = database

  def create_connection(self) -> pymysql.Connection:
    try:
      self.__connection = pymysql.connect(
        host=self.__host,
        port=self.__port,
        user=self.__user,
        password=self.__password,
        database=self.__database
      )

      return self.__connection
    except Exception as e:
      log("Failed to create DB connection!")
      log("  └ " + str(e))
      return None

  def manual_close_connection(self) -> bool:
    try:
      if self.__connection:
        self.__connection.close()
        self.__connection = None

      return True
    except Exception as e:
      print("Failed to close DB connection!")
      log("  └ " + str(e))
      return False

  def test_connection(self) -> bool:
    try:
      with self.create_connection() as conn:
        conn.ping()

      return True
    except:
      return False
