from LEDScraper.Mappers import *

DRIVER_DIR = "./chromedriver.exe"
HEADLESS = False

DATA_DIR = './data'
LED_SEARCH_URL = 'http://asset.led.go.th/newbidreg/default.asp'

PROVINCE_LIST = ['กรุงเทพมหานคร']
PROVINCE_SCOPE = {
  x: list(LED_DISTRICT_ID[x].keys()) for x in PROVINCE_LIST
}

LOCATION_COOLDOWN = 14400