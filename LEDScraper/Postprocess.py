from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
import numpy as np
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from .Mappers import *
from .DBConfig import MAX_SCHEMA

def run_postprocess(out_dict):

    def earliest_next(input_list):
        date_str_list = input_list[:-1]
        status = input_list[-1]

        if status == 'unavailable':
            return pd.Series(['NA-unavailable','NA-unavailable'])
        else:
            date_list = [
                datetime(x[2]-543,x[1],x[0]) for x in [
                    list(map(int, y.split('/'))) for y in date_str_list
                ]
            ]

            is_future = [1 if x>=datetime.now()+relativedelta(days=-1) else 0 for x in date_list]

            try:
              earliest_index = is_future.index(1)
              return pd.Series([date_str_list[earliest_index],earliest_index+1])

            except:
              return pd.Series(['NA-nofuture','NA-nofuture'])           

    data = pd.DataFrame.from_dict(out_dict,orient='index')\
    .reset_index().rename({'index':'entry_id'},axis=1)

    # postprocess: area
    data['total_area_sqwa'] = [
        z/4 if a.find('ห้องชุด')!=-1 else x*400+y*100+z for x,y,z,a in zip(
            data['area_rai'],
            data['area_ngan'],
            data['area_sqwam'],
            data['asset_type']
        )
    ]
    data['total_area_sqm'] = [
        z if a.find('ห้องชุด')!=-1 else (x*400+y*100+z)*4 for x,y,z,a in zip(
            data['area_rai'],
            data['area_ngan'],
            data['area_sqwam'],
            data['asset_type']
        )
    ]

    # postprocess: columns and nulls
    data = correct_columns(data)

    # postprocess: price
    data['max_start_thb_per_sqwa'] = data['max_start_price']/data['total_area_sqwa']
    data['max_start_thb_per_sqm'] = data['max_start_price']/data['total_area_sqm']
    data['assigned_start_thb_per_sqwa'] = data['assigned_start_price']/data['total_area_sqwa']
    data['assigned_start_thb_per_sqm'] = data['assigned_start_price']/data['total_area_sqm']

    # get max number of rounds
    max_round = max(
      [int(x.replace('auction_round','').replace('_status','').replace('_date','')) for x in data.columns if x.find('auction_round')!=-1]
    )
    auction_status_cols = [f'auction_round{x}_status' for x in range(1,max_round)]
    auction_date_cols = [f'auction_round{x}_date' for x in range(1,max_round)]
    data[auction_status_cols] = data[auction_status_cols].fillna('NA')
    data[auction_date_cols] = data[auction_date_cols].fillna('01/01/2022') # some arbitrary date in the past

    # cleaning: deed number
    data['deed_no'] = data['deed_no'].apply(clean_deed)

    # cleaning: auction identifiers
    data['auction_identifier'] = data[['lot_no','sequence_no']].agg('|'.join, axis=1)

    # postprocess: auction rounds
    data['all_auction_status'] = data[auction_status_cols].agg('|'.join, axis=1)
    data['asset_status'] = [
        'unavailable' if (x.find('ขายได้')!=-1) | (x.find('ถอน')!=-1) else 'available' for x in data['all_auction_status']
    ]
    data[['next_date','next_round']] = \
    data[auction_date_cols+['asset_status']].apply(earliest_next,axis=1)

    # reorder columns
    cols = data.columns
    focus_cols = [
        'auction_identifier',
        'asset_status',
        'next_date',
        'next_round',
        'province',
        'district',
        'subdistrict',
        'lot_no',
        'sequence_no',
        # 'deed_no',
        # 'case_id',
        # 'asset_type',
        # 'area_rai',
        # 'area_ngan',
        # 'area_sqwam',
        'total_area_sqwa',
        'total_area_sqm',
        'max_start_price',
        'assigned_start_price',
        'max_start_thb_per_sqwa',
        'max_start_thb_per_sqm',
        'assigned_start_thb_per_sqwa',
        'assigned_start_thb_per_sqm',    
        'led_url'
    ]
    remaining_cols = list(set(cols)-set(focus_cols))
    new_cols = focus_cols + remaining_cols
    
    return data[new_cols]

def correct_columns(
    data,
    max_schema=MAX_SCHEMA
):
    current_cols = data.columns
    for col in max_schema.keys():
        if col not in current_cols:
            data[col] = max_schema[col]
        else:
            data[col] = data[col].fillna(max_schema[col])
    return data

def get_deed_range(x):
    
    from_deed = int(x.split('-')[0].strip())
    to_deed = int(x.split('-')[1].strip())+1
    
    if to_deed < from_deed:
        to_deed = int(
            str(from_deed)[:-1] + str(to_deed)
        )
        
    return list(
        range(
            from_deed,
            to_deed
        )
    )
    
def clean_deed(deed_str):
    
    try:
        deed_list = [x for x in deed_str.split(',') if len(x)>0]
        deed_list = [
            [int(x)] if x.find('-')==-1 else get_deed_range(x) for x in deed_list
        ]
        deed_list_int = [elem for entry in deed_list for elem in entry]
        return str(deed_list_int).replace('[','').replace(']','').replace(' ','')
    except:
        return deed_str

def find_location(
    entry,
    driver=None,
    max_locations_per_entry=1,
    max_wait_time=5,
    driver_path='./chromedriver.exe',
    led_search_url='https://landsmaps.dol.go.th/',
    headless=False
    ):

    if not driver:
        options = Options()
        options.headless = headless
        
        driver = webdriver.Chrome("./chromedriver.exe", options=options)
        driver.get(led_search_url)

        wait = WebDriverWait(driver, 60)\
        .until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/nav/form[1]/div/select')
            )
        )
        prov_select = Select(driver.find_elements_by_xpath('/html/body/nav/form[1]/div/select')[0])
        prov_select.select_by_visible_text('กรุงเทพมหานคร')


    possible_locations = []
    
    if entry['deed_no'] is not np.nan:

        entry_province = entry['province']
        entry_district = entry['district']

        clean_province = PROVINCE_MAPPER[entry_province]
        possible_districts = DISTRICT_MAPPER[entry_province][entry_district.replace(' ','')]

        # print(possible_districts)

        for d in possible_districts:
            
            # print(entry['deed_no'].split(','))
            
            for deed in entry['deed_no'].split(','):

                wait = WebDriverWait(driver, max_wait_time)\
                .until(
                    EC.presence_of_element_located(
                        (By.XPATH, '/html/body/nav/form[2]/div/select')
                    )
                )

                prov_select = Select(driver.find_elements_by_xpath('/html/body/nav/form[1]/div/select')[0])
                prov_select.select_by_visible_text(clean_province)

                district_select = Select(driver.find_elements_by_xpath('/html/body/nav/form[2]/div/select')[0])
                district_select.select_by_visible_text(d)

                deed_box = driver\
                .find_elements_by_xpath(
                    '/html/body/nav/form[3]/span/input'
                )[0]

                deed_box.clear()
                deed_box.send_keys(deed)
                deed_box.send_keys(Keys.ENTER)

                try:
                    # elemets = [
                    #     '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[10]/div[2]/a',
                    #     '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[10]/div[2]/a',
                    #     '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[9]/div[2]',
                    #     '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[9]/div[2]'
                    # ]
                    # for elem in elements:
                    #     WebDriverWait(driver, max_wait_time/4)\
                    #     .until(
                    #         EC.presence_of_element_located(
                    #             (By.XPATH, elem)
                    #         )
                    #     )
                    # time.sleep(max_wait_time)
                    # WebDriverWait(driver, max_wait_time)
                    wait = WebDriverWait(driver, max_wait_time)\
                    .until(
                        EC.presence_of_element_located(
                            (By.XPATH, '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[9]/div[2]')
                        )
                    )
                    
                    time.sleep(2)
                    
                    coor = driver.find_elements_by_xpath(
                        '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[10]/div[2]/a'
                    )[0].text

                    gmap = driver.find_elements_by_xpath(
                        '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[10]/div[2]/a'
                    )[0].get_attribute('href')

                    price = driver.find_elements_by_xpath(
                        '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[9]/div[2]'
                    )[0].text.split(' ')[0]

                    price_unit = driver.find_elements_by_xpath(
                        '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[9]/div[2]'
                    )[0].text.split(' ')[1]

                    print(f'District: {d}; Deed: {deed}; Coordinates: {coor}; Price {price} {price_unit}; Gmap: {gmap}')
                    
                    possible_locations.append(
                        [
                            coor,
                            gmap,
                            f'{price} {price_unit}',
                            d,
                            deed
                        ]
                    )
                    
                    if len(possible_locations) == max_locations_per_entry:
                        break
                        
                except Exception as e:
                    
                    print(f'District: {d}; Deed: {deed}; Coordinates: NA; Price NA; Gmap: NA')
                    print(e)
                    pass
                    
    if len(possible_locations)==0:
        possible_locations.append(['NA']*5)
        
    # print(possible_locations)
    results = [*possible_locations[0],str(possible_locations)]
    # print(results)
    
    return pd.Series(results)

def run_location_finder(
    driver,
    data,
    location_search_url = 'https://landsmaps.dol.go.th/'
    ):

    driver.get(location_search_url)

    # close landing layer if exists
    try:
        wait = WebDriverWait(driver, 60)\
        .until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/div[25]/div/div/div/div[1]/button/i')
            )
        )
        time.sleep(2)
        close = driver.find_elements_by_xpath('/html/body/div[25]/div/div/div/div[1]/button/i')
        close[0].click()
    except:
        print('button not found')

    do_find = data[
        (data['asset_status']=='available')\
        & (data['loc_coordinates']=='NA')
    ]
    loc_last_status = 'success'

    if do_find.shape[0]>0:

        for index, row in do_find.iterrows():
            # do_find[[
            #     'loc_coordinates',
            #     'loc_google_maps',
            #     'loc_price_per_unit',
            #     'loc_district',
            #     'loc_deed',
            #     'loc_possibilities'
            # ]] = do_find.apply(
            #     find_location,
            #     axis=1,
            #     driver=driver
            # )

            row_update = find_location(
                row,
                driver=driver
            )
            do_find.loc[
                index,
                [
                    'loc_coordinates',
                    'loc_google_maps',
                    'loc_price_per_unit',
                    'loc_district',
                    'loc_deed',
                    'loc_possibilities'
                ]
            ] = row_update.values
        
        cant_find_any = all([x == 'NA' for x in do_find['loc_coordinates'].tolist()])
        loc_last_status = 'failure' if cant_find_any else 'success'

    else:
        print('-'*30)
        print('No location to search')
        # loc_last_status remains success

    dont_find = data[
        ~(data['asset_status']=='available')\
        | ~(data['loc_coordinates']=='NA')
    ]

    return pd.concat([do_find,dont_find]), datetime.now(), loc_last_status

def if_find_location(
    driver,
    loc_last_time,
    loc_last_status,
    cooldown=10800
    ):

    do_find_loc = False

    if loc_last_status == 'success':
        do_find_loc = True
    elif (datetime.now()-loc_last_time).seconds>cooldown:
        loc_last_time, loc_last_status = test_find_location(driver)
        if loc_last_status == 'success':
            do_find_loc = True

    return do_find_loc, loc_last_time, loc_last_status

def test_find_location(
    driver,
    led_search_url='https://landsmaps.dol.go.th/'
    ):
    
    print('-'*30)
    print('Testing location search with known deed')
    
    driver.get(location_search_url)

    # close landing layer if exists
    try:
        wait = WebDriverWait(driver, 60)\
        .until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/div[25]/div/div/div/div[1]/button/i')
            )
        )
        time.sleep(2)
        close = driver.find_elements_by_xpath('/html/body/div[25]/div/div/div/div[1]/button/i')
        close[0].click()
    except:
        print('button not found')

    prov_select = Select(driver.find_elements_by_xpath('/html/body/nav/form[1]/div/select')[0])
    prov_select.select_by_visible_text('กรุงเทพมหานคร')

    district_select = Select(driver.find_elements_by_xpath('/html/body/nav/form[2]/div/select')[0])
    district_select.select_by_visible_text('38-ลาดพร้าว')

    deed_box = driver\
    .find_elements_by_xpath(
        '/html/body/nav/form[3]/span/input'
    )[0]

    deed_box.clear()
    deed_box.send_keys('2234')
    deed_box.send_keys(Keys.ENTER)

    try:

        wait = WebDriverWait(driver, max_wait_time)\
        .until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[9]/div[2]')
            )
        )
        
        time.sleep(2)
        
        coor = driver.find_elements_by_xpath(
            '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[10]/div[2]/a'
        )[0].text

        gmap = driver.find_elements_by_xpath(
            '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[10]/div[2]/a'
        )[0].get_attribute('href')

        price = driver.find_elements_by_xpath(
            '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[9]/div[2]'
        )[0].text.split(' ')[0]

        price_unit = driver.find_elements_by_xpath(
            '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[9]/div[2]'
        )[0].text.split(' ')[1]

        loc_last_status = 'success'

        print('-'*30)
        print('Time out expired: Location search activated')
            
    except Exception as e:

        loc_last_status = 'failure'
        print('-'*30)
        print('Time out persists: Consider increasing cooldown value')

    return datetime.now(), loc_last_status