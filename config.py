from const import CONFIG_FILE_PATH
import os
import yaml

class Config:
  __config: dict = None

  def __init__(self):
    if self.__config_file_exists():
      if not self.__load_config():
        raise Exception("Config can't be loaded! Is it readable and valid YAML file?")
    else:
      raise FileNotFoundError("Cannot find config file!")

  def __config_file_exists(self) -> bool:
    return os.path.exists(CONFIG_FILE_PATH) and os.path.isfile(CONFIG_FILE_PATH)

  def __load_config(self) -> bool:
    with open(CONFIG_FILE_PATH, "r") as file:
      self.__config = yaml.safe_load(file)

      if self.__config:
        return True
    return False

  def is_config_loaded(self) -> bool:
    return True if self.__config else False

  def __contains__(self, key: str) -> bool:
    return key in self.__config

  def __getitem__(self, key: str) -> any:
    return self.__config[key]

  def __len__(self) -> int:
    return len(self.__config)

  def __repr__(self) -> str:
    return repr(self.__config)
