from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from crawlers.CrawlerBase import CrawlerBase
from util import log

class Pixiv(CrawlerBase):
  __USERNAME_XPATH = '//*[@id="root"]/div[2]/div/div[2]/div/div[1]/div[2]/div/a[3]'
  __STAT_COUNT_XPATH = '//*[@id="root"]/div[2]/div/div[2]/div/div[2]/div[2]/div[2]/div/section/div[1]/div/div/div/span'

  def __init__(self, driver: Chrome, user_id: str | None = None):
    super()
    self.driver = driver
    self.user_id = user_id

  # Don't use abstract method
  def navigate(self): pass

  def navigate(self, following_page = False):
    if following_page:
      log("Start navigating to Pixiv followings page of user id {}.".format(self.user_id))
      self.driver.get("https://www.pixiv.net/users/21160166/following".format(self.user_id.replace("@", "")))
    else:
      log("Start navigating to Pixiv followers page of user id {}.".format(self.user_id))
      self.driver.get("https://www.pixiv.net/users/21160166/followers".format(self.user_id.replace("@", "")))

  def wait(self):
    log("Waiting for dynamic load to be completed...")
    wait = WebDriverWait(self.driver, 5)

    # TODO: This won't work; need investigate
    wait.until(EC.presence_of_element_located((By.XPATH, self.__STAT_COUNT_XPATH)))

  def do_crawl(self) -> dict:
    result = {
      "username": None,
      "follower_count": None,
      "following_count": None
    }

    # Follower
    self.navigate()
    self.wait()
    result["username"] = self.driver.find_element(By.XPATH, self.__USERNAME_XPATH).text
    result["follower_count"] = int(self.driver.find_element(By.XPATH, self.__STAT_COUNT_XPATH).text)

    # Following
    self.navigate(True)
    self.wait()
    result["following_count"] = int(self.driver.find_element(By.XPATH, self.__STAT_COUNT_XPATH).text)

    return result
