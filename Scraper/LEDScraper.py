from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
import numpy as np
import os
import time
import pickle
from tqdm import tqdm
from datetime import datetime

from config import DATA_DIR, LED_DATA

class LEDScraper:

    LED_URL = 'http://asset.led.go.th/newbidreg/'
    PROVINCE_BOX = '/html/body/div[4]/div/div[1]/div/div/div[3]/div/div[2]/table/tbody/tr/td[2]/input'
    CAPTCHA_TEXT = '/html/body/div[4]/div/div[1]/table/tbody/tr[1]/td[1]/strong/font/font'
    CAPTCHA_BOX = '/html/body/div[4]/div/div[1]/table/tbody/tr[1]/td[2]/input'

    LISTING_TABLE = '/html/body/div[4]/div/div[2]/div[2]/table/tbody'
    WAIT_TIME = 5
    DETAIL_ELEM_DETECT = '/html/body/div[1]/div/div/div[1]/table[2]/tbody/tr/td[1]/strong/font/font'

    auction_order_xpath = '/html/body/div[1]/div/div/div[1]/table[2]/tbody/tr/td[1]/strong/font/font'
    info_table_xpath = '/html/body/div[1]/div/div/div[4]/div/div'
    auction_table_xpath = '/html/body/div[1]/div/div/div[6]/div/table/tbody/tr'
    price_table_xpath = '/html/body/div[1]/div/div/div[7]/div/div'
    deposit_xpath = '/html/body/div[1]/div/div/div[8]/strong[1]/font'
    condition_xpath = '/html/body/div[1]/div/div/div[7]/div/h5'

    deep_extract_xpath = {
        'property': {
            'auction_order_xpath': '/html/body/div[1]/div/div/div[1]/table[2]/tbody/tr/td[1]/strong/font/font',
            'info_table_xpath': '/html/body/div[1]/div/div/div[4]/div/div',
            'auction_table_xpath': '/html/body/div[1]/div/div/div[6]/div/table/tbody/tr',
            'price_table_xpath': '/html/body/div[1]/div/div/div[7]/div/div',
            'deposit_xpath': '/html/body/div[1]/div/div/div[8]/strong[1]/font',
            'condition_xpath': '/html/body/div[1]/div/div/div[7]/div/h5',
        },
        'equity': {

        }
    }

    def __init__(self, driver):
        self.driver = driver
        self.results_dict = {}

        self.db = self.read_db()

    def goto(self, url):
        self.driver.get(url)

    def goto_led(self):
        self.goto(self.LED_URL)

    def goto_next(self):
        next_button = self.driver\
        .find_elements(
            By.XPATH,
            '/html/body/div[4]/div/div[2]/table[2]/tbody/tr/td[3]/div/a'
        )[-2]
        next_button.click()

    def input_province(self, province):
        input_box = self.driver.find_element(By.XPATH, self.PROVINCE_BOX)
        input_box.send_keys(province)
    
    def input_captcha(self):
        captcha_text = self.driver.find_elements(By.XPATH, self.CAPTCHA_TEXT)[0].get_attribute('innerHTML')
        captcha_box = self.driver.find_element(By.XPATH, self.CAPTCHA_BOX)

        captcha_box.send_keys(captcha_text)
        captcha_box.send_keys(Keys.ENTER)

    def extract_listing_table(self):
        '''
        Extracts the listing table on any given page.
        Doesn't do anymore than this - delegate navigation logic elsewhere.
        '''

        listing_table = self.driver.find_elements(By.XPATH, self.LISTING_TABLE)[0]
        elem_list = listing_table.find_elements(By.CSS_SELECTOR, 'tr')

        listing_table_pointer = {}
        data_dict = {}
        for entry in tqdm(elem_list):
            
            asset_category = entry.find_elements(By.CSS_SELECTOR, 'td')[3].text
            asset_category = 'property' if asset_category!='หุ้น' else 'equity'
            
            entry_id = '|'.join([
                x.text.strip() for x in entry.find_elements(By.CSS_SELECTOR,'td')[:3]
            ])

            data_dict[entry_id] = {
                'lot_no': entry.find_elements(By.CSS_SELECTOR,'td')[0].text,
                'sequence_no': entry.find_elements(By.CSS_SELECTOR,'td')[1].text,
                'case_id': entry.find_elements(By.CSS_SELECTOR,'td')[2].text,
                'asset_type': entry.find_elements(By.CSS_SELECTOR,'td')[3].text,
                'area_rai': self.util_format_number(entry.find_elements(By.CSS_SELECTOR,'td')[4].text),
                'area_ngan': self.util_format_number(entry.find_elements(By.CSS_SELECTOR,'td')[5].text),
                'area_sqwam': self.util_format_number(entry.find_elements(By.CSS_SELECTOR,'td')[6].text),
                'assigned_start_price': self.util_format_number(entry.find_elements(By.CSS_SELECTOR,'td')[7].text),
                'subdistrict': entry.find_elements(By.CSS_SELECTOR,'td')[8].text.replace(' ',''),
                'district': entry.find_elements(By.CSS_SELECTOR,'td')[9].text.replace(' ',''),
                'province': entry.find_elements(By.CSS_SELECTOR,'td')[10].text.replace(' ',''),
                'asset_category': asset_category,
                'created_on': datetime.now(),
                'last_updated': datetime.now()
            }
            listing_table_pointer[entry_id] = entry

        # self.results_dict.update(data_dict)

        return data_dict, listing_table_pointer
    
    def extract_entry_details(self, data_dict, listing_table_pointer):

        for entry_id in tqdm(data_dict.keys()):
            
            elem = listing_table_pointer[entry_id]
            asset_category = data_dict[entry_id]['asset_category']

            if entry_id not in list(self.db.keys()):

                deep_extract_success = False

                while(not deep_extract_success):

                    try:
                        elem.click()
                        self.driver.switch_to.window(self.driver.window_handles[1])

                        # detect a 
                        wait = WebDriverWait(self.driver, self.WAIT_TIME)\
                        .until(
                            EC.presence_of_element_located(
                                (By.XPATH, self.DETAIL_ELEM_DETECT)
                            )
                        )

                        ### DEEP EXTRACT 1: INFO DATA
                        info_data = self.deep_extract_info(
                            auction_order_xpath=self.deep_extract_xpath[asset_category]['auction_order_xpath'],
                            info_table_xpath=self.deep_extract_xpath[asset_category]['info_table_xpath']
                        )

                        auction_data, latest_status = self.deep_extract_auction(
                            auction_table_xpath=self.deep_extract_xpath[asset_category]['auction_table_xpath']
                        )
                        
                        price_data = self.deep_extract_price(
                            latest_status,
                            price_table_xpath=self.deep_extract_xpath[asset_category]['price_table_xpath'],
                            deposit_xpath=self.deep_extract_xpath[asset_category]['deposit_xpath'],
                            condition_xpath=self.deep_extract_xpath[asset_category]['condition_xpath']
                        )

                        # results_dict --> keeps track of new listings
                        self.results_dict[entry_id] = data_dict[entry_id].copy()
                        self.results_dict[entry_id].update(info_data)
                        self.results_dict[entry_id].update(auction_data)
                        self.results_dict[entry_id].update(price_data)
                    
                        time.sleep(1)

                        # record this extraction
                        self.db[entry_id] = data_dict[entry_id]
                        # self.save_db()
                        deep_extract_success = True

                    except Exception as e:
                        print(f'Deep extraction failed {e}')
                        time.sleep(5)
                    
                    finally:
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])


    def deep_extract_auction(
            self,
            auction_table_xpath = '/html/body/div[1]/div/div/div[1]/table[2]/tbody/tr/td[1]/strong/font/font'
    ):
        auction_table = self.driver\
        .find_elements(By.XPATH, auction_table_xpath)

        auction_data = {}

        for row in auction_table:
            round_no = row.find_elements(By.CSS_SELECTOR, 'td')[0].text.strip()
            auction_data[f'auction_round{round_no}_date'] = row.find_elements(By.CSS_SELECTOR, 'td')[1].text
            auction_data[f'auction_round{round_no}_status'] = row.find_elements(By.CSS_SELECTOR, 'td')[2].text
        
        latest_status = list(auction_data.values())[-1]
        
        return auction_data, latest_status

            
    def deep_extract_price(
        self,
        latest_status,
        price_table_xpath = '/html/body/div[1]/div/div/div[7]/div/div',
        deposit_xpath = '',
        condition_xpath = ''
    ):
        unavailable = any([
            x in latest_status for x in ['ขายได้','งดขาย','ถอนการยึด','งดการบังคับคดี']
        ])
    #     if latest_status.split(' ')[0] in ['ขายได้','งดขาย','ถอนการยึด']:
        if unavailable:
    #         print('skipping price extraction: asset sold')
    #         logger.info('skipping price extraction: asset sold or unavailable')
            return {}
        else:
            price_table = self.driver\
            .find_elements(By.XPATH, price_table_xpath)
            price_string = price_table[0].text

            price_list = price_string.split('\n')

            def clean_price(string):
                out = float(
                    string\
                    .replace('จำนวน','')\
                    .replace('บาท','')\
                    .replace('ไม่มี','0')\
                    .replace(',','')\
                    .strip()
                )
                return out

            price_data = {
                price_list[0]: clean_price(
                    price_list[1]
                ),
                price_list[2]: clean_price(
                    price_list[3]
                ),
                price_list[4]: clean_price(
                    price_list[5]
                ),
                price_list[6]: clean_price(
                    price_list[7]
                )
            }
            
            price_data['max_start_price'] = max(
                list(price_data.values())
            )
            price_data['min_start_price'] = min(
                [x for x in list(price_data.values()) if x > 0]
            )
            price_data['deposit_amt'] = clean_price(
                self.driver.find_elements(By.XPATH,deposit_xpath)[0].text
            )
            price_data['sales_conditions'] = self.driver.find_elements(By.XPATH,condition_xpath)[0].text

            return price_data

    def deep_extract_info(
        self,
        auction_order_xpath='/html/body/div[1]/div/div/div[1]/table[2]/tbody/tr/td[1]/strong/font/font',
        info_table_xpath='/html/body/div[1]/div/div/div[4]/div/div'
    ):
        this_data = {}

        # auction order
        auction_order = self.driver\
        .find_elements(
            By.XPATH,
            auction_order_xpath
        )
        auction_order = auction_order[0].text\
        .replace('ทรัพย์ที่จะขาย','')\
        .strip()

        this_data.update(self.util_to_dict(auction_order))

        # body of stuff
        body = self.driver\
        .find_elements(
            By.XPATH,
            info_table_xpath
        )[0]

        content = list(
            set(
                x.text for x in body.find_elements(By.CSS_SELECTOR, 'div')
            )
        )
        for x in content:
            for y in x.split('\n'):
                this_data.update(self.util_to_dict(y.strip()))

        # deed no
        if 'ที่ดิน' in this_data.keys():
            deed_str = this_data['ที่ดิน']
            deed_no = deed_str.split(' ')[1]
            this_data.update({'deed_no': deed_no})

        def format_number(string):
            return np.round(float(string.replace('-','0')),4)

        # area
        if 'เนื้อที่' in this_data.keys():
            area_str = this_data['เนื้อที่']
            area_list = area_str.split(' ')
            area_rai = format_number(area_list[0])
            area_ngan = format_number(area_list[2])
            area_sqwam = format_number(area_list[4])
            this_data.update({
                'area_rai': area_rai,
                'area_ngan': area_ngan,
                'area_sqwam': area_sqwam
            })
        
        return this_data

    def save_db(self):
        db = pd.DataFrame(self.db).T
        db.index.name = 'entry_id'
        db.to_csv(os.path.join(DATA_DIR, LED_DATA))

    def read_db(self):
        db_path = os.path.join(DATA_DIR, LED_DATA)
        if os.path.exists(db_path):
            db = pd.read_csv(db_path)
            db = db.set_index('entry_id')
            db = db.to_dict(orient='index')
        else:
            db = {}
        return db
    
    def save_new_results(self, file_name):
        new_results = pd.DataFrame(self.results_dict).T
        new_results.index.name = 'entry_id'

        save_path = os.path.join(DATA_DIR,'daily',str(datetime.today().date()))
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        new_results.to_csv(os.path.join(save_path,f'{file_name}.csv'))
    
    def util_to_dict(self, string):
        # key space value
        data = string.split(' ')
        return {
            data[0]: ' '.join(data[1:]).strip()
        }

    def util_format_number(self, string):
        return np.round(float(string.replace('-','0').replace(',','')), 4)
    
    def end_session(self):
        self.driver.quit()