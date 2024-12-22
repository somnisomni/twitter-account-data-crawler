import json
from time import sleep
from selenium.webdriver import Chrome
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from crawlers.CrawlerBase import CrawlerBase
from util import log
from crawlers.Twitter import Twitter

class TwitterWorkaround(Twitter):
  def __init__(self, driver: Chrome, handle: str = None, status_id: str = None):
    super()
    self.driver = driver
    self.handle = handle.replace("@", "")
    self.status_id = status_id

  def navigate(self, current_retry: int = 0, retry_count: int = 5):
    wait = WebDriverWait(self.driver, 5)

    try:
      ''' Stage 1. Navigate to status page '''
      log("Start navigating to Twitter status page (handle: @{}, status id: {}).".format(self.handle, self.status_id))
      self.driver.get("https://twitter.com/{}/status/{}".format(self.handle, self.status_id))

      ''' Stage 1-1. Wait for dynamic load '''
      log("Waiting for dynamic load to be completed...")
      self._wait_retry(wait, EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='tweetText']")))
      self._wait_retry(wait, EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='User-Name']")))

      ''' Stage 2. Navigate to profile page by clicking username anchor '''
      log("Status page loaded, try finding and clicking profile link anchor...")
      username_element = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='User-Name']")
      username_anchor_element = username_element.find_element(By.TAG_NAME, "a")
      username_anchor_element.click()

      ''' Stage 2-1. Wait for dynamic load '''
      log("Waiting for dynamic load to be completed...")
      self._wait_retry(wait, EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='UserDescription']")))
      self._wait_retry(wait, EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='UserName']")))
    except:
      log("Seems like the page is not loaded correctly! Is the website updated, or Twitter blocked access?")
      return

  def wait(self):
    # navigate() does wait, no need to declare something in here.
    pass
