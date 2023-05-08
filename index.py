from typing import Tuple
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import twitter
import yaml
import pymysql
from datetime import date
import os

CONFIG_FILE_PATH = "config/config.yaml"
config: dict = None
tw_client: twitter.Api = None
db_connection: pymysql.Connection = None

def check_config_file_exists() -> bool:
  return os.path.exists(CONFIG_FILE_PATH)

def connect_db() -> pymysql.Connection:
  global config
  return pymysql.connect(host=(config["mysql"]["host"] if config["mysql"]["host"] else None),
                         port=(config["mysql"]["port"] if config["mysql"]["port"] else None),
                         user=(config["mysql"]["username"] if config["mysql"]["username"] else None),
                         password=(config["mysql"]["password"] if config["mysql"]["password"] else None),
                         database=(config["mysql"]["database"] if config["mysql"]["database"] else None))

def create_twitter_api_instance() -> twitter.Api:
  global config
  return twitter.Api(consumer_key=config["twitter"]["consumerKey"],
                     consumer_secret=config["twitter"]["consumerSecret"],
                     application_only_auth=True)

def get_twitter_user_info(user_id: str) -> Tuple[int, int, int]:
  global tw_client
  user: twitter.User = tw_client.GetUser(user_id)

  return (int(user.followers_count), int(user.friends_count), int(user.statuses_count))

def daily_loop():
  global config, db_connection

  print("Daily loop job started...", flush=True)

  db_connection = connect_db()
  if not db_connection:
    print("Error while connecting to database!", flush=True)
    exit(4)

  with connect_db() as db_connection:
    with db_connection.cursor() as cursor:
      for target in config["targets"]:
        followers, following, statuses = get_twitter_user_info(target["id"])

        try:
          cursor.execute("INSERT INTO {} (date, following_count, follower_count, tweet_count) VALUES (%s, %s, %s, %s)".format(str(target["table"]).split()[0]),
                        (date.today().strftime("%Y-%m-%d"),
                        following,
                        followers,
                        statuses))
        finally:
          pass
      cursor.fetchall()
    db_connection.commit()

  db_connection = None

  print("Daily loop job done.", flush=True)

if __name__ == "__main__":
  if not check_config_file_exists():
    print("Config file does not exist!", flush=True)
    exit(1)

  with open(CONFIG_FILE_PATH) as conffile:
    config = yaml.load(conffile, Loader=yaml.FullLoader)

    if not config:
      print("Error while loading config file!", flush=True)
      exit(2)

  tw_client = create_twitter_api_instance()
  if not tw_client:
    print("Error while creating Twitter API instance!", flush=True)
    exit(3)

  # Schedule
  sched = BlockingScheduler(timezone="Asia/Seoul")
  sched.add_job(daily_loop, CronTrigger.from_crontab("59 23 * * *"))

  try:
    print("\nDaily loop scheduled, timezone = {}".format(sched.timezone.zone), flush=True)
    sched.start()
  except (KeyboardInterrupt, SystemExit):
    print("Exiting...", flush=True)
    sched.shutdown(False)
    exit(100)
