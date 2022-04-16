from LEDScraper.Mappers import *
import platform

DRIVER_DIR = "./chromedriver.exe" if platform.system()=='Windows' else "./chromedriver"
HEADLESS = True

DATA_DIR = './data'
LED_SEARCH_URL = 'http://asset.led.go.th/newbidreg/default.asp'

PROVINCE_LIST = ['กรุงเทพมหานคร']
PROVINCE_SCOPE = {
  x: list(LED_DISTRICT_ID[x].keys()) for x in PROVINCE_LIST
}

LOCATION_COOLDOWN = 14400
LOCATION_SEARCH_LIMIT = 30