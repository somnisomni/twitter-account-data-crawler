from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from util import log
from abc import ABC, abstractmethod

class CrawlerBase(ABC):
  def __init__(self, driver: Chrome):
    self.driver = driver

  def _wait_retry(self, wdw: WebDriverWait, target_method, retry_count: int = 5) -> bool:
    count = 0

    while count < retry_count:
      log("#{}".format(count + 1), end=" ")
      try:
        wdw.until(target_method)
      except TimeoutException:
        count += 1
        continue

      log("")
      return True
    
    return False

  @abstractmethod
  def navigate(self): pass

  @abstractmethod
  def wait(self): pass

  @abstractmethod
  def do_crawl(self) -> dict:
    self.navigate()
    self.wait()
    pass
