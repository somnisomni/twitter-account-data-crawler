import subprocess

### --- Constants --- ###
CONFIG_FILE_PATH = "config/config.yaml"
USE_DRIVER_MANAGER = True
CHROMEDRIVER_PATH = subprocess.run(["which", "chromedriver"], capture_output=True).stdout.decode("utf-8").strip()
# DEFAULT_USERAGENT = None
DRIVER_ARGUMENTS = ["--headless",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"]
