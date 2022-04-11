from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime

from config import *

from LEDScraper.Scraper import *
from LEDScraper.Postprocess import *
from LEDScraper.Mappers import *
from LEDScraper.DataInterface import *

if __name__ == "__main__":

	options = Options()
	# options.headless = HEADLESS
	options.add_argument("--window-size=1920,1080")
	options.add_argument("--start-maximized")
	if HEADLESS:
		options.add_argument("--headless")
		options.add_argument("--disable-gpu")
	driver = webdriver.Chrome(DRIVER_DIR, options=options)

	loc_last_time = datetime.now()
	loc_last_status = 'success'

	while True:

		print('-'*30)
		print(datetime.now())

		for province in PROVINCE_SCOPE.keys():

			eng_province = ENG_TRANSLATE_PROVINCE[province]
			district_dict = LED_DISTRICT_ID[province]

			for district_id in PROVINCE_SCOPE[province]:
				
				# loc_last_time, loc_last_status = test_find_location()
				
				do_find_location, loc_last_time, loc_last_status = if_find_location(
					driver,
					loc_last_time,
					loc_last_status,
					cooldown=LOCATION_COOLDOWN
				)

				driver.get(LED_SEARCH_URL)
				select_province(driver, province=province)
				fuck_captcha(driver)

				district = district_dict[district_id]
				
				# out_dict = {}
				out_dict = get_existing_db(
					data_dir = DATA_DIR,
					province = eng_province,
					district_id = str(district_id)
				)
				
				print('-'*30)
				print(f'Extracting {district_id}:{district.strip()}')
				
				# select district
				select_district(driver, district=district)
				fuck_captcha(driver)
				out_dict = scraper_extract(
					driver,
					out_dict,
					province,
					district
				)

				# postprocess
				out_db = run_postprocess(
					out_dict
				)
				
				# find location
				if do_find_location:
					print('-'*30)
					print('Performing location search')
					out_db, loc_last_time, loc_last_status = run_location_finder(
						driver,
						out_db
					)
				else:
					print('-'*30)
					print('Skipping location search')
				print(f'Last {loc_last_status} search at {loc_last_time}')
				
				# save
				save_db(
					out_db,
					data_dir = DATA_DIR,
					province = eng_province,
					district_id = str(district_id)
				)