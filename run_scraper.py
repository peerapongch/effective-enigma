from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import pickle

from config import *

from LEDScraper.Scraper import *
from LEDScraper.Postprocess import *
from LEDScraper.Mappers import *
from LEDScraper.DataInterface import *

def load_state():
	state_path = 'state.pickle'
	if os.path.isfile(state_path):
		return pickle.load(open(state_path,'rb'))
	else:
		return {}

def set_state(STATE,var,value):
	STATE[var] = value
	return STATE

def save_state(STATE):
	pickle.dump(STATE,open('state.pickle','wb'))
	return True

def make_sequence(pointer,original_seq):
	new_seq = list(original_seq)
	index = new_seq.index(pointer)
	return new_seq[index:] + new_seq[:index]

if __name__ == "__main__":

	# proxy = '8.213.129.34:80'
	options = Options()
	# options.headless = HEADLESS
	options.add_argument("--window-size=1920,1080")
	options.add_argument("--start-maximized")
	# options.add_argument(f"--proxy-server={proxy}")
	if HEADLESS:
		options.add_argument("--disable-web-security")
		options.add_argument("--disable-site-isolation-trials")
		options.add_argument("--headless")
		options.add_argument("--disable-gpu")
		user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36'
		options.add_argument(f"--user-agent={user_agent}")
	driver = webdriver.Chrome(DRIVER_DIR, options=options)

	loc_last_time = datetime.now()
	loc_last_status = 'success'

	# get state
	STATE = load_state()

	while True:

		print('-'*30)
		print(datetime.now())

		province_seq = make_sequence(
			STATE['last_province'],
			PROVINCE_SCOPE.keys()
		)

		for province in province_seq:

			eng_province = ENG_TRANSLATE_PROVINCE[province]
			district_dict = LED_DISTRICT_ID[province]

			district_id_seq = make_sequence(
				STATE['last_district_id']+1,
				PROVINCE_SCOPE[province]
			)

			for district_id in district_id_seq:
				
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

				if len(out_dict)>0:
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

				STATE = set_state(STATE, 'last_province', province)
				STATE = set_state(STATE, 'last_district_id', district_id)
				save_state(STATE)