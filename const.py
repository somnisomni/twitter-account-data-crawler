### --- Constants --- ###
CONFIG_FILE_PATH = "config/config.yaml"
DEFAULT_USERAGENT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" # Googlebot
# DEFAULT_USERAGENT = None
DRIVER_ARGUMENTS = ["--headless",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "user-agent={}".format(DEFAULT_USERAGENT) if DEFAULT_USERAGENT else ""]
