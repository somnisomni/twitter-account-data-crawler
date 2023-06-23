from selenium.webdriver import Chrome
from abc import ABC, abstractmethod

class CrawlerBase(ABC):
  def __init__(self, driver: Chrome):
    self.driver = driver

  @abstractmethod
  def navigate(self): pass

  @abstractmethod
  def wait(self): pass

  @abstractmethod
  def do_crawl(self) -> dict:
    self.navigate()
    self.wait()
    pass
