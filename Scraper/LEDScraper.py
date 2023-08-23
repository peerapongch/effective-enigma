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

    def __init__(self, driver):
        self.driver = driver
        self.results_dict = {}
    
    def goto(self, url):
        self.driver.get(url)

    def goto_led(self):
        self.goto(self.LED_URL)

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
        rows = listing_table.find_elements(By.CSS_SELECTOR, 'tr')

        res = {}
        for entry in tqdm(rows):
            
            # asset_type = entry.find_elements(By.CSS_SELECTOR, 'td')[3].text
            
            entry_id = '|'.join([
                x.text.strip() for x in entry.find_elements(By.CSS_SELECTOR,'td')
            ])

            res[entry_id] = {
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
                'created_on': datetime.now(),
                'last_updated': datetime.now()
            }

        self.results_dict.update(res)

        return res, rows
    
    def extract_entry_details(self, rows):

        for entry in tqdm(rows):
            entry.click()
            self.driver.switch_to.window(self.driver.window_handles[1])

            # detect a 
            wait = WebDriverWait(self.driver, self.WAIT_TIME)\
            .until(
                EC.presence_of_element_located(
                    (By.XPATH, self.DETAIL_ELEM_DETECT)
                )
            )

            print('yay')
            time.sleep(1)
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            #TODO

    def check_entry_exists(self, res, rows):
        '''
        This method considers the current page's gathered entries to see if they are new.
        Detail extraction is only done for entries which are new so to minimize access frequency.
        '''


        

    def util_format_number(self, string):
        return np.round(float(string.replace('-','0').replace(',','')), 4)