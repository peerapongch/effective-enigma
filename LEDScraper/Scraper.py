from selenium import webdriver
from selenium.webdriver.support.ui import Select

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
import numpy as np
import os
import pickle
from tqdm import tqdm

def select_province(driver, province='กรุงเทพมหานคร'):
    # province selection
    prov_xpath = '/html/body/div[4]/div/div/div/div/div[3]/div/div[1]/table/tbody/tr/td[2]/select'

    prov_menu = driver\
    .find_elements_by_xpath(
        prov_xpath
    )[0]

    prov_select = Select(prov_menu)
    prov_select.select_by_visible_text(province)

def get_districts(driver):
    select = Select(
        driver\
        .find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[3]/div/div[3]/table/tbody/tr/td[2]/select')
    )
    
    districts = [x.text for x in select.options]
    
    print(len(districts[1:]))

    return districts[1:]

def select_district(driver, district='วัฒนา                '):
    district_xpath = '/html/body/div[4]/div/div[1]/div/div/div[3]/div/div[3]/table/tbody/tr/td[2]/select'

    district_menu = driver\
    .find_elements_by_xpath(
        district_xpath
    )[0]

    district_select = Select(district_menu)
    district_select.select_by_visible_text(district)

def fuck_captcha(driver):
    # captcha
    captcha_xpath = '/html/body/div[4]/div/div[1]/table/tbody/tr[1]/td[1]/strong/font/font'

    captcha_text = driver\
    .find_elements_by_xpath(
        captcha_xpath
    )[0]

    captcha_text = captcha_text.get_attribute('innerHTML')
    # print(captcha_text)

    captcha_box_xpath = '/html/body/div[4]/div/div[1]/table/tbody/tr[1]/td[2]/input'

    captcha_box = driver\
    .find_elements_by_xpath(
        captcha_box_xpath
    )[0]

    captcha_box.send_keys(captcha_text)
    captcha_box.send_keys(Keys.ENTER)

def go_to_page(start_page):
    # go to page
    current_page, total_pages = get_page_info(driver)
    while current_page != start_page:
        # navigate to the starting page
        if current_page < start_page:
            farnext_button = driver\
            .find_elements_by_xpath(
                '/html/body/div[4]/div/div[2]/table[1]/tbody/tr/td[3]/div/a'
            )[-3]
            farnext_button.click()
        else:
            last_button = driver\
            .find_elements_by_xpath(
                '/html/body/div[4]/div/div[2]/table[1]/tbody/tr/td[3]/div/a'
            )[1]
            last_button.click()

        current_page, total_pages = get_page_info(driver)

def to_dict(string):
    # key space value
    data = string.split(' ')
    return {
        data[0]: ' '.join(data[1:]).strip()
    }

def deep_extract(driver,entry_id,out_dict,asset_type='property'):

    if asset_type=='property':
        auction_order_xpath = '/html/body/div[1]/div/div/div[1]/table[2]/tbody/tr/td[1]/strong/font/font'
        info_table_xpath = '/html/body/div[1]/div/div/div[4]/div/div'
        
        auction_table_xpath = '/html/body/div[1]/div/div/div[6]/div/table/tbody/tr'
        
        price_table_xpath = '/html/body/div[1]/div/div/div[7]/div/div'
        deposit_xpath = '/html/body/div[1]/div/div/div[8]/strong[1]/font'
        condition_xpath = '/html/body/div[1]/div/div/div[7]/div/h5'
        
    elif asset_type=='equity':
        auction_order_xpath = '/html/body/div[1]/div/div/div[1]/table[2]/tbody/tr/td[1]/strong/font/font'
        info_table_xpath = '/html/body/div[1]/div/div/div[3]/div/div'
        
        auction_table_xpath = '/html/body/div[1]/div/div/div[4]/div/table/tbody/tr'
        
        # /html/body/div[1]/div/div/div[4]/div/table/tbody
        price_table_xpath = '/html/body/div[1]/div/div/div[5]/div/div'
        deposit_xpath = '/html/body/div[1]/div/div/div[6]/strong[1]/font'
        condition_xpath = '/html/body/div[1]/div/div/div[5]/div/h5'
    
    wait = WebDriverWait(driver, 3)\
    .until(
        EC.presence_of_element_located(
            (By.XPATH, info_table_xpath)
        )
    )

    info_data = info_extract(
        driver,
        auction_order_xpath=auction_order_xpath,
        info_table_xpath=info_table_xpath
    )
    
    auction_data, latest_status = auction_extract(
        driver,
        auction_table_xpath=auction_table_xpath
    )
    
    price_data = price_extract(
        driver,
        latest_status,
        price_table_xpath=price_table_xpath,
        deposit_xpath=deposit_xpath,
        condition_xpath=condition_xpath
    )
    
    # out_dict[entry_id] = info_data
    # out_dict[entry_id].update(price_data)
    # out_dict[entry_id].update(auction_data)

    info_data.update(price_data)
    info_data.update(auction_data)
    
    return info_data

def price_extract(
    driver,
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
        price_table = driver\
        .find_elements_by_xpath(price_table_xpath)
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
            driver.find_elements_by_xpath(deposit_xpath)[0].text
        )
        price_data['sales_conditions'] = driver.find_elements_by_xpath(condition_xpath)[0].text

        return price_data

def auction_extract(
    driver,
    auction_table_xpath = '/html/body/div[1]/div/div/div[6]/div/table/tbody/tr'
):
    auction_table = driver\
    .find_elements_by_xpath(auction_table_xpath)

    auction_data = {}

    for row in auction_table:
        round_no = row.find_elements_by_css_selector('td')[0].text.strip()
        auction_data[f'auction_round{round_no}_date'] = row.find_elements_by_css_selector('td')[1].text
        auction_data[f'auction_round{round_no}_status'] = row.find_elements_by_css_selector('td')[2].text
    
    latest_status = list(auction_data.values())[-1]
    
    return auction_data, latest_status

def info_extract(
    driver,
    auction_order_xpath='/html/body/div[1]/div/div/div[1]/table[2]/tbody/tr/td[1]/strong/font/font',
    info_table_xpath='/html/body/div[1]/div/div/div[4]/div/div'
):
    this_data = {}

    # auction order
    auction_order = driver\
    .find_elements_by_xpath(
        auction_order_xpath
    )
    auction_order = auction_order[0].text\
    .replace('ทรัพย์ที่จะขาย','')\
    .strip()

    this_data.update(to_dict(auction_order))

    # body of stuff
    body = driver\
    .find_elements_by_xpath(
        info_table_xpath
    )[0]

    content = list(
        set(
            x.text for x in body.find_elements_by_css_selector('div')
        )
    )
    for x in content:
        for y in x.split('\n'):
            this_data.update(to_dict(y.strip()))

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
    
def _property_extract(driver):
    this_data = {}

    # auction order
    auction_order = driver\
    .find_elements_by_xpath(
        '/html/body/div[1]/div/div/div[1]/table[2]/tbody/tr/td[1]/strong/font/font'
    )
    auction_order = auction_order[0].text\
    .replace('ทรัพย์ที่จะขาย','')\
    .strip()

    this_data.update(to_dict(auction_order))

    # body of stuff
    body = driver\
    .find_elements_by_xpath(
        '/html/body/div[1]/div/div/div[4]/div/div'
    )[0]

    content = list(
        set(
            x.text for x in body.find_elements_by_css_selector('div')
        )
    )
    for x in content:
        for y in x.split('\n'):
            this_data.update(to_dict(y.strip()))

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
    
def get_page_info(driver):
    page_object = driver\
    .find_elements_by_xpath(
        '/html/body/div[4]/div/div[2]/table[1]/tbody/tr/td[2]/div'
    )[0]
    
    current_page, total_pages = page_object.text.replace('หน้าที่','').strip().split('/')
    return int(current_page), int(total_pages)

def scraper_extract(driver, out_dict, province, district):
    current_page, total_pages = get_page_info(driver)
    counter = [0,0]

    print('-'*30)
    print(f'Total Pages: {total_pages}')

    while current_page <= total_pages:

        # get listing table
        main_table = driver\
        .find_elements_by_xpath(
            '/html/body/div[4]/div/div[2]/div[2]/table/tbody'
        )[0]

        print('-'*30)
        print(f'Scanning page {current_page} of {total_pages}')

        for entry in tqdm(main_table.find_elements_by_css_selector('tr')):

            asset_type = entry.find_elements_by_css_selector('td')[3].text
            asset_type = 'property' if asset_type!='หุ้น' else 'equity'

            def format_number(string):
                return np.round(float(string.replace('-','0').replace(',','')),4)

            # initial entry info
            entry_info = {
                'lot_no': entry.find_elements_by_css_selector('td')[0].text,
                'sequence_no': entry.find_elements_by_css_selector('td')[1].text,
                'case_id': entry.find_elements_by_css_selector('td')[2].text,
                'asset_type': entry.find_elements_by_css_selector('td')[3].text,
                'area_rai': format_number(entry.find_elements_by_css_selector('td')[4].text),
                'area_ngan': format_number(entry.find_elements_by_css_selector('td')[5].text),
                'area_sqwam': format_number(entry.find_elements_by_css_selector('td')[6].text),
                'assigned_start_price': format_number(entry.find_elements_by_css_selector('td')[7].text),
                'subdistrict': entry.find_elements_by_css_selector('td')[8].text.replace(' ',''),
                'district': entry.find_elements_by_css_selector('td')[9].text.replace(' ',''),
                'province': province.replace(' ','')
            }

            # enter entry
            entry.click()
            driver.switch_to.window(driver.window_handles[1])

            try:
                # detect a 
                wait = WebDriverWait(driver, 5)\
                .until(
                    EC.presence_of_element_located(
                        (By.XPATH, '/html/body/div[1]/div/div/div[1]/table[2]/tbody/tr/td[1]/strong/font/font')
                    )
                )

                # url
                entry_url = driver.current_url
                entry_info.update(
                    {
                        'led_url': entry_url
                    }
                )

                #count
                counter[1] += 1

                if entry_url not in out_dict.keys():
                
                    try:
                        out_dict[entry_url] = deep_extract(
                            driver,
                            entry_url,
                            out_dict,
                            asset_type = asset_type
                        )

                    except Exception as e:
                        out_dict[entry_url] = {}
                        print(f'Error extraction of {district}: {current_page}: {entry_url}: {e}')

                    finally:
                        out_dict[entry_url].update(
                            entry_info
                        )

                counter[0] += 1

            except:
                print('-'*30)
                print('Page didnt load right')
            
            finally:
                # close tab
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

        next_button = driver\
        .find_elements_by_xpath(
            '/html/body/div[4]/div/div[2]/table[1]/tbody/tr/td[3]/div/a'
        )[-2]
        next_button.click()

        # update page
        next_current_page, total_pages = get_page_info(driver)

        if next_current_page == current_page:
            break
        else:
            current_page = next_current_page

    return out_dict

def save_raw(out_dict, scrape_date, province_eng, district_id):
    pickle.dump(
        out_dict,
        open(
            f'./data/{scrape_date}_{province_eng}_district_{str(district_id)}.pickle',
            'wb'
        )
    )