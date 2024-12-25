import json
from time import sleep
from selenium.webdriver import Chrome
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from crawlers.CrawlerBase import CrawlerBase
from util import log

class Twitter(CrawlerBase):
  def __init__(self, driver: Chrome, handle: str = None, account_id: str = None):
    super()
    self.driver = driver
    self.handle = handle
    self.account_id = account_id

  def navigate(self):
    if self.handle:
      log("Start navigating to Twitter profile page of @{}.".format(self.handle))
      self.driver.get("https://twitter.com/{}".format(self.handle.replace("@", "")))
    elif self.account_id:
      log("Start navigating to Twitter profile page of account ID {}.".format(self.account_id))
      self.driver.get("https://twitter.com/intent/user?user_id={}".format(self.account_id))

  def wait(self):
    try:
      log("Waiting for dynamic load to be completed...")
      wait = WebDriverWait(self.driver, 5)
      self._wait_retry(wait, EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='UserDescription']")))
      self._wait_retry(wait, EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='UserName']")))
    except TimeoutException:
      log("Seems like the page is not loaded correctly! Is the website updated, or Twitter blocked access?")
      return

  def __find_user_profile_schema(self) -> dict:
    find_count = 1
    find_count_max = 5
    find_interval_sec = 1
    found_element: WebElement = None
    schema_str = None

    while (not found_element) and (find_count <= find_count_max):
      log("Trying to locate user profile schema... #{} try out of {}".format(find_count, find_count_max))

      try:
        script_elements: list[WebElement] = self.driver.find_elements(By.TAG_NAME, "script")
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
      log("Can't locate user profile schema; Is the website updated, or user is not exist?")
      return None

    schema_str = found_element.get_attribute("innerHTML")
    if schema_str:
      log("Found.")
      return json.loads(schema_str)
    else:
      log("No content in user profile schema element.")
      return None

  def __get_target_data_from_schema(self, schema: dict) -> dict:
    result = {
      "id": schema["mainEntity"]["identifier"],
      "screen_name": schema["mainEntity"]["additionalName"],
      "nickname": schema["mainEntity"]["givenName"],
    }

    for stat in schema["mainEntity"]["interactionStatistic"]:
      if stat["name"] == "Follows": # Followers
        result["follower_count"] = int(stat["userInteractionCount"])
      elif stat["name"] == "Friends": # Followings
        result["following_count"] = int(stat["userInteractionCount"])
      elif stat["name"] == "Tweets": # Tweets
        result["tweet_count"] = int(stat["userInteractionCount"])

    return result

  def do_crawl(self) -> dict:
    super().do_crawl()

    schema = self.__find_user_profile_schema()
    if schema:
      return self.__get_target_data_from_schema(schema)
    else:
      log("Can't continue for this account due to error!")
      return None
