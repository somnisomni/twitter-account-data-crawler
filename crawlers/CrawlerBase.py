from selenium.webdriver import Chrome
from abc import ABC, abstractmethod

class CrawlerBase(ABC):
  def __init__(self, driver: Chrome):
    self.driver = driver

  @abstractmethod
  def __navigate(self): pass

  @abstractmethod
  def __wait(self): pass

  @abstractmethod
  def do_crawl(self) -> dict:
    self.__navigate()
    self.__wait()
    pass
