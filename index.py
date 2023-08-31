from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium_stealth import stealth
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date
import pymysql
from const import *
from config import Config
from util import log
from crawlers.Twitter import Twitter
from crawlers.TwitterWorkaround import TwitterWorkaround

### --- Global variables --- ###
config: Config = None

### --- Functions --- ###
def load_config() -> bool:
  global config
  config = Config()

  if config.is_config_loaded():
    log("Config loaded.")
    return True
  else:
    log("Config cannot be loaded!")
    return False

def connect_db() -> pymysql.Connection:
  global config
  return pymysql.connect(host=(config["mysql"]["host"] if config["mysql"]["host"] else None),
                         port=(config["mysql"]["port"] if config["mysql"]["port"] else None),
                         user=(config["mysql"]["username"] if config["mysql"]["username"] else None),
                         password=(config["mysql"]["password"] if config["mysql"]["password"] else None),
                         database=(config["mysql"]["database"] if config["mysql"]["database"] else None))

def create_chrome_webdriver() -> webdriver.Chrome | None:
  options = webdriver.ChromeOptions()
  for arg in DRIVER_ARGUMENTS:
    if arg:
      options.add_argument(arg)

  service = ChromeService(executable_path=CHROMEDRIVER_PATH)

  try:
    driver = webdriver.Chrome(options=options, service=service)
    driver.implicitly_wait(10)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined })")

    stealth(driver,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            languages=["ko-KR", "ko", "en-US", "en"],
            platform="Linux64",
            vendor="Google Inc.",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)

    log("Chrome WebDriver instance created, with arguments: {}".format(" ".join(DRIVER_ARGUMENTS)))
    return driver
  except Exception as e:
    log("Error while creating Chrome WebDriver: {}".format(e))
    return None

def daily_loop(db_dry: bool = False):
  global config

  log("\nDaily loop job started...")

  today_date = date.today()
  log("Today is {}".format(today_date.strftime("%Y-%m-%d")))

  driver = create_chrome_webdriver()
  if not driver:
    log("Error while creating Chrome WebDriver! Can't continue, exiting daily loop job.")
    return

  fetched_data: list[dict] = []
  for target in config["targets"]:
    log("")

    if "handle" in target:
      if "workaround_status_id" in target:
        data = TwitterWorkaround(driver, handle=target["handle"], status_id=target["workaround_status_id"]).do_crawl()
      else:
        data = Twitter(driver, handle=target["handle"]).do_crawl()
    else:
      data = Twitter(driver, account_id=target["id"]).do_crawl()

    fdata = {}
    if data:
      fdata["data"] = data
      fdata["table"] = target["table"]
      fdata["success"] = True

      fetched_data.append(fdata)
    else:
      fdata["data"] = None
      fdata["table"] = None
      fdata["success"] = False

      log("Can't continue for this account due to crawling error!")
      fetched_data.append(fdata)
  
  log("")

  if not db_dry:
    try:
      with connect_db() as db_connection:
        log("Connected with database server.")

        try:
          with db_connection.cursor() as cursor:
            for data in fetched_data:
              if (not ("success" in data)) or (not data["success"]):
                log("Skipping account ID {}, due to crawling error.".format(data["data"]["id"]))
                continue

              table = str(data["table"])
              followers = str(data["data"]["follower_count"])
              followings = str(data["data"]["following_count"])
              statuses = str(data["data"]["tweet_count"])

              try:
                cursor.execute("INSERT INTO {} (date, following_count, follower_count, tweet_count) VALUES (%s, %s, %s, %s)".format(table.split()[0]),
                              (today_date.strftime("%Y-%m-%d"),
                              followings,
                              followers,
                              statuses))
                log("Row inserted.")
              except Exception as e:
                log("Failed to execute DB query!")
                log(e)
                continue
            cursor.fetchall()
        except Exception as e:
          log("Failed to create DB cursor or manipulate DB!")
          log(e)

        try:
          db_connection.commit()
          log("Database changes are successfully committed.")
        except Exception as e:
          log("Failed to commit DB!")
          log(e)
    except Exception as e:
      log("Something wrong while manipulating the database! Is database server available, and database config is valid?")
      log(e)
  else:
    log("DB dry run mode enabled, skipping database manipulation.")

  log("Chrome WebDriver cleanup.")
  driver.quit()
  del driver

  log("Daily loop job finished!")


### --- Main procedure --- ###
if __name__ == "__main__":
  log("\n\nMain procedure started.\n")

  if not load_config():
    exit(1)

  # Log configuration
  log("Total {} target(s) will be crawled.".format(len(config["targets"])))

  # Schedule
  SCHED_HOUR = 23
  SCHED_MINUTE = 58
  sched = BlockingScheduler(timezone="Asia/Seoul")
  sched.add_job(daily_loop, CronTrigger.from_crontab("{} {} * * *".format(SCHED_MINUTE, SCHED_HOUR)))

  try:
    log("\nDaily loop job scheduled, at {}:{} everyday. timezone = {}".format(SCHED_HOUR, SCHED_MINUTE, sched.timezone.zone))
    sched.start()
  except (KeyboardInterrupt, SystemExit):
    log("Exiting...")
    sched.shutdown(False)
    exit(100)
