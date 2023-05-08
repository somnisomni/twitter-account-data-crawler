from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from time import sleep
from datetime import date
import pymysql
import json
from const import *
from config import Config

### --- Global variables --- ###
config: Config = None

### --- Helper functions --- ##
def log(value: object, sep = " ", end="\n"):
  print(value, sep=sep, end=end, flush=True)


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
    options.add_argument(arg)

  try:
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)

    log("Chrome WebDriver instance created, with arguments: {}".format(" ".join(DRIVER_ARGUMENTS)))
    return driver
  except:
    return None

def navigate_to_handle(driver: webdriver.Chrome, handle: str):
  log("Start navigating to Twitter profile page of @{}.".format(handle))
  driver.get("https://twitter.com/{}".format(handle.replace("@", "")))

def navigate_to_account_id(driver: webdriver.Chrome, id: str | int):
  log("Start navigating to Twitter profile page of account ID {}.".format(id))
  driver.get("https://twitter.com/intent/user?user_id={}".format(id))

def wait_for_dynamic_load(driver: webdriver.Chrome):
  log("Waiting for dynamic load to be completed...")
  wait = WebDriverWait(driver, 5)
  wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='primaryColumn']")))
  wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='UserName']")))

def try_find_user_profile_schema(driver: webdriver.Chrome) -> dict:
  find_count = 1
  find_count_max = 10
  find_interval_sec = 1
  found_element: WebElement = None
  schema_str = None

  while (not found_element) and (find_count <= find_count_max):
    log("Trying to find user profile schema... {}/{}".format(find_count, find_count_max))

    try:
      script_elements: list[WebElement] = driver.find_elements(By.TAG_NAME, "script")
    except StaleElementReferenceException:
      log("Any script element is not present, sleep 2 seconds and retry...")
      sleep(2)
      find_count += 1
      continue

    for elem in script_elements:
      if elem.get_dom_attribute("type") == "application/ld+json" \
         and elem.get_dom_attribute("data-testid") == "UserProfileSchema-test":
        found_element = elem
        break

    if not found_element:
      find_count += 1
      sleep(find_interval_sec)

  if not found_element:
    log("Can't find user profile schema; was the website updated?")
    return None

  schema_str = found_element.get_attribute("innerHTML")
  if schema_str:
    log("Found.")
    return json.loads(schema_str)
  else:
    log("No content in user profile schema element.")
    return None

def get_profile_data_from_schema(data: dict) -> dict:
  result = {
    "id": data["author"]["identifier"],
    "screen_name": data["author"]["additionalName"],
    "nickname": data["author"]["givenName"],
  }

  for stat in data["author"]["interactionStatistic"]:
    if stat["name"] == "Follows": # Followers
      result["follower_count"] = int(stat["userInteractionCount"])
    elif stat["name"] == "Friends": # Followings
      result["following_count"] = int(stat["userInteractionCount"])
    elif stat["name"] == "Tweets": # Tweets
      result["tweet_count"] = int(stat["userInteractionCount"])

  return result

def daily_loop():
  global config

  log("\nDaily loop job started...")

  driver = create_chrome_webdriver()
  if not driver:
    log("Error while creating Chrome WebDriver.")
    exit(1)

  fetched_data = dict()
  for target in config["targets"]:
    navigate_to_account_id(driver, target["id"])
    wait_for_dynamic_load(driver)

    schema = try_find_user_profile_schema(driver)
    if schema:
        data = get_profile_data_from_schema(schema)
        fetched_data[target["id"]] = data
    else:
        log("Can't continue due to error!")

  try:
    with connect_db() as db_connection:
      log("Connected with database server.")

      with db_connection.cursor() as cursor:
        for target in config["targets"]:
          followers = fetched_data[target["id"]]["follower_count"]
          followings = fetched_data[target["id"]]["following_count"]
          statuses = fetched_data[target["id"]]["tweet_count"]

          try:
            cursor.execute("INSERT INTO {} (date, following_count, follower_count, tweet_count) VALUES (%s, %s, %s, %s)".format(str(target["table"]).split()[0]),
                          (date.today().strftime("%Y-%m-%d"),
                          followings,
                          followers,
                          statuses))
            log("Row inserted.")
          finally:
            pass
        cursor.fetchall()
      db_connection.commit()
      log("Database changes are successfully committed.")
  except:
    log("Something wrong while manipulating the database! Is database server available, and database config is valid?")

  log("Chrome WebDriver cleanup.")
  driver.quit()
  del driver

  log("Daily loop job finished!")


### --- Main procedure --- ###
if __name__ == "__main__":
  log("\n\nMain procedure started.\n")

  if not load_config():
    exit(1)

  # Schedule
  sched = BlockingScheduler(timezone="Asia/Seoul")
  sched.add_job(daily_loop, CronTrigger.from_crontab("59 23 * * *"))

  try:
    log("\nDaily loop job scheduled, at 23:59 everyday. timezone = {}".format(sched.timezone.zone))
    sched.start()
  except (KeyboardInterrupt, SystemExit):
    log("Exiting...")
    sched.shutdown(False)
    exit(100)
