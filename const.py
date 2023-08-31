import subprocess

### --- Constants --- ###
CONFIG_FILE_PATH = "config/config.yaml"
CHROMEDRIVER_PATH = subprocess.run(["which", "chromedriver"], capture_output=True).stdout.decode("utf-8").strip()
# DEFAULT_USERAGENT = None
DRIVER_ARGUMENTS = ["--headless",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"]
