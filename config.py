from LEDScraper.Mappers import *
import platform

DRIVER_DIR = "./chromedriver.exe" if platform.system()=='Windows' else "./chromedriver"
HEADLESS = False

DATA_DIR = './data'
LED_SEARCH_URL = 'http://asset.led.go.th/newbidreg/default.asp'

PROVINCE_LIST = ['ภูเก็ต']
PROVINCE_SCOPE = {
  x: list(LED_DISTRICT_ID[x].keys()) for x in PROVINCE_LIST
}

SCRAPER_PAGE_LIMIT = 1
LOCATION_COOLDOWN = 14400
LOCATION_SEARCH_LIMIT = 30