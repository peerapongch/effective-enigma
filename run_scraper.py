from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

from datetime import datetime
import pickle
import requests
import json
import time
import boto3
import sys

from config import *

from LEDScraper.Scraper import scraper_extract, select_province, fuck_captcha, select_district
from LEDScraper.Postprocess import run_postprocess, run_location_finder, test_find_location
from LEDScraper.Mappers import *
from LEDScraper.DataInterface import *

def load_state():
	#s3 to temp
	try:
		os.system(f'aws s3 cp s3://effective-enigma/state.pickle ./state.pickle')
	except:
		print(f'State not found')

	# load from local
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

	try:
		os.system(f'aws s3 cp ./state.pickle s3://effective-enigma/state.pickle')
	except:
		print(f'Write failed --> CHEEECK: state.pickle')

	return True

def make_sequence(pointer,original_seq):
	new_seq = list(original_seq)
	index = new_seq.index(pointer)
	return new_seq[index:] + new_seq[:index]

def make_driver():

	def get_aws_proxy_ip():
		
		proxy_name = 'test-instance'
		proxy_ip = None

		while not proxy_ip:
			indexes = []
			try:
				print('Fetching Proxy from AWS')
				ec2 = boto3.client('ec2')
				response = ec2.describe_instances()

				for i in range(len(response['Reservations'])):
					for t in response['Reservations'][i]['Instances'][0]['Tags']:
						if (t['Key']=='Name') and (t['Value']==proxy_name):
							indexes.append(i)
				
				print(f'Found {len(indexes)} matching the proxy instance name. Looking for the correct one.')
				for index in indexes:
					try:
						proxy_ip = response['Reservations'][index]['Instances'][0]['NetworkInterfaces'][0]['PrivateIpAddresses'][0]['Association']['PublicIp']
						print('Found that damn proxy.')
					except:
						pass
			except:
				print('Proxy Fetch Failed: Retrying')
				time.sleep(5)
		return proxy_ip

	success = False
	while not success:
		try:
			proxy_ip = get_aws_proxy_ip()
			print(f'Trying proxy ip {proxy_ip} at port 8888')
			proxy_options = {
					'proxy': {
							# 'http': f'http://scraperapi:{api_key}@proxy-server.scraperapi.com:8001',
							'http': f'http://{proxy_ip}:8888',
							'no_proxy': 'localhost,127.0.0.1'
					}
			}
			options = Options()
			options.add_argument("--window-size=1920,1080")
			options.add_argument("--start-maximized")

			driver = webdriver.Chrome(
				DRIVER_DIR,
				options=options,
				seleniumwire_options=proxy_options
			)

			driver.get('http://httpbin.org/ip')
			driver.find_element_by_xpath('/html/body/pre')
			success = True
		
		except KeyboardInterrupt:
			print('Interrupted')
			try:
				sys.exit(0)
			except SystemExit:
				os._exit(0)
		
		except:
			print('Driver failed to make connection to http')

	return driver

if __name__ == "__main__":

	# driver
	driver = make_driver()

	# setting driver status for checking
	loc_last_time = datetime.now()
	loc_last_status = 'failure'

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
				(STATE['last_district_id']+1) % len(PROVINCE_SCOPE[province]),
				PROVINCE_SCOPE[province]
			)

			try:

				for district_id in district_id_seq:

					while loc_last_status!='success':
						print('-'*30)
						print('Attempting dirver via proxy server')
						driver = make_driver()
						loc_last_status = 'success'
						# loc_last_time, loc_last_status = test_find_location(driver)

					driver.get(LED_SEARCH_URL)
					select_province(driver, province=province)
					fuck_captcha(driver)

					district = district_dict[district_id]
					
					# load preexisting db
					in_dict = get_existing_db(
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
						in_dict.copy(),
						province,
						district,
						page_limit=1
					)

					if len(out_dict)>0:
						# postprocess
						out_db = run_postprocess(
							out_dict
						)
						
						out_db, loc_last_time, loc_last_status = run_location_finder(
							driver,
							out_db,
							search_limit=LOCATION_SEARCH_LIMIT
						)
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

			except KeyboardInterrupt:
				print('Interrupted')
				try:
					sys.exit(0)
				except SystemExit:
					os._exit(0)
			
			except:
				print('Possible proxy server reset. Re-establishing driver.')
				loc_last_time = datetime.now()
				loc_last_status = 'failure'