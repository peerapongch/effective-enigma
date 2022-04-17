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
from tqdm import tqdm
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

    # postprocess: columns and nulls
    data = correct_columns(data)

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
        'unavailable' if (x.find('ขายได้')!=-1) | (x.find('ถอน')!=-1) | (x.find('งดขายในนัดที่เหลือ')!=-1) else 'available' for x in data['all_auction_status']
    ]

    # debug
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

def correct_columns(data,max_schema=MAX_SCHEMA):
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
    max_wait_time=2,
    driver_path='./chromedriver.exe',
    led_search_url='https://landsmaps.dol.go.th/',
    headless=False,
    deed_limit=10
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
    n_stale = 0

    if entry['deed_no'] not in ['',None,np.nan]:

        entry_province = entry['province']
        entry_district = entry['district']

        clean_province = PROVINCE_MAPPER[entry_province]
        possible_districts = DISTRICT_MAPPER[entry_province][entry_district.replace(' ','')]

        terminate = False

        # print(possible_districts)

        for d in possible_districts:
            
            # print(entry['deed_no'].split(','))
            
            # imposed limit to 10 deeds
            deed_list = entry['deed_no'].split(',')
            upto = min(deed_limit,len(entry['deed_no'].split(',')))
            for deed in deed_list[:upto]:

                print('-'*30)
                print(f'Searching {d}:{deed}')

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

                    wait = WebDriverWait(driver, max_wait_time)\
                    .until(
                        EC.presence_of_element_located(
                            (By.XPATH, '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[9]/div[2]')
                        )
                    )
                    
                    # wait time for page to respond
                    time.sleep(4)

                    coor = driver.find_elements_by_xpath(
                        '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[10]/div[2]/a'
                    )[0].text

                    gmap = driver.find_elements_by_xpath(
                        '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[10]/div[2]/a'
                    )[0].get_attribute('href').replace('%20','')

                    price = driver.find_elements_by_xpath(
                        '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[9]/div[2]'
                    )[0].text.split(' ')[0]

                    price_unit = driver.find_elements_by_xpath(
                        '/html/body/div[1]/div[3]/span/div/div[2]/div[2]/div/div[2]/div[9]/div[2]'
                    )[0].text.split(' ')[1]
                    
                    if (coor=='') and (gmap not in ['NA','',None,np.nan]):
                        coor = gmap.split('=')[1]

                    possible_locations.append(
                        [
                            coor,
                            gmap,
                            f'{price} {price_unit}',
                            d,
                            deed
                        ]
                    )
                    
                    terminate = len(possible_locations) == max_locations_per_entry
                    if terminate:
                        break
                        
                except Exception as e:
                    n_stale += 1
                    print(f'District: {d}; Deed: {deed}; Coordinates: NA; Price NA; Gmap: NA')
                    print(e)
                    pass

                finally:
                    print(f'Terminate: {str(terminate)}')
                    print(f'Possible loc: {len(possible_locations)}')
                    print(possible_locations)

            if terminate:
                break
                    
    if len(possible_locations)==0:
        possible_locations.append(['NA']*5)
        
    # print(possible_locations)
    results = [*possible_locations[0],str(possible_locations)]
    # print(results)
    
    return pd.Series(results), n_stale

def load_loc_search_page(driver,location_search_url,wait_time = 3):

    # close landing layer if exists
    try:
        driver.get(location_search_url)
        
        wait = WebDriverWait(driver, wait_time)\
        .until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/div[25]/div/div/div/div[1]/button/i')
            )
        )
    except:
        print('This weird thing ')

    time.sleep(2)

    try:
        close = driver.find_elements_by_xpath('/html/body/div[25]/div/div/div/div[1]/button/i')
        close[0].click()
    except:
        print('button not found')

def run_location_finder(
    driver,
    data,
    location_search_url = 'https://landsmaps.dol.go.th/',
    entry_tolerance = 10,
    deed_tolerance = 20,
    search_limit = 50
    ):

    find_cond = (
        data['asset_status']=='available'
    ) & (
        data['loc_coordinates']=='NA'
    ) & (
        (
            pd.Series([(x-y).total_seconds()<7200 for x,y in zip(data['last_updated'],data['created_on'])])
        ) | (
            pd.Series([(datetime.now()-x).total_seconds()>172800 for x in data['last_updated']])
        )
    )

    do_find = data[find_cond]
    dont_find = data[~find_cond]
    loc_last_status = 'success' # default value

    print('-'*30)
    print(f'Finding: {do_find.shape[0]} locations')

    if do_find.shape[0]>0:

        counter = 0
        stale_entry_counter = 0
        n_stale = 0 # deed stale counter
        last_coor = '0,0'
        last_deed = 'NA'
        

        load_loc_search_page(driver,location_search_url)

        for index, row in tqdm(do_find.iterrows(), total=do_find.shape[0]):

            counter += 1

            row_update, this_n_stale = find_location(
                row,
                driver=driver
            )
            n_stale += this_n_stale # counting total stale deed searches
            print(f'Current stale deed count: {n_stale}')

            # reject results conditions
            stale_entry = (row_update[0]==last_coor) and (row_update[4]!=last_deed)
            if stale_entry:
                # skipping update because it is shit
                stale_entry_counter += 1
                print(f'Found stale entry: {stale_entry_counter}')

                # last_coor = '0.0' # for next search
                # last_deed = 'NA' # for next search
            else:
                # entry isnt stale
                # but the underlying deed search may be stale or just cannot find anything which confounds staleness
                if row_update[0]!='NA':
                    stale_entry_counter = 0
                    n_stale = 0
                    print(f'Reset -- pass counter: {stale_entry_counter}; n_stale: {n_stale}')

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

                    last_coor = row_update[0] # for next search
                    last_deed = row_update[4] # for next search

                do_find.loc[index,'last_updated'] = datetime.now()
            
            # limiter on search for quick checkpointing
            if stale_entry_counter>entry_tolerance:
                print(f'Too many stale entries: {stale_entry_counter}')
                loc_last_status = 'failure'
                break
            if n_stale>deed_tolerance:
                print(f'Too many stale deeds: {n_stale}')
                loc_last_status = 'failure'
                break
            if counter>search_limit:
                print(f'Search limit reached: {search_limit}')
                break

    else:
        print('-'*30)
        print('No location to search')
        # loc_last_status remains success

    return pd.concat([do_find,dont_find]), datetime.now(), loc_last_status

def test_find_location(
    driver,
    led_search_url='https://landsmaps.dol.go.th/'
    ):
    
    print('-'*30)
    print('Testing location search with known deed')

    # close landing layer if exists
    try:
        load_loc_search_page(driver,led_search_url)

        # time.sleep(8)

        # wait = WebDriverWait(driver, 10)\
        # .until(
        #     EC.presence_of_element_located(
        #         (By.XPATH, '/html/body/div[25]/div/div/div/div[1]/button/i')
        #     )
        # )
        # try:
        #     close = driver.find_elements_by_xpath('/html/body/div[25]/div/div/div/div[1]/button/i')
        #     close[0].click()
        # except:
        #     print('button not found')

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

        wait = WebDriverWait(driver, 2)\
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
        print('Driver working properly')
            
    except Exception as e:

        loc_last_status = 'failure'
        print('-'*30)
        print('Something\'s wrong')

    return datetime.now(), loc_last_status

# deprecated
def if_find_location(
    driver,
    loc_last_time,
    loc_last_status,
    cooldown=10800
    ):

    do_find_loc = False

    if loc_last_status == 'success':
        do_find_loc = True
    elif (datetime.now()-loc_last_time).total_seconds()>cooldown:
        loc_last_time, loc_last_status = test_find_location(driver)
        if loc_last_status == 'success':
            do_find_loc = True

    return do_find_loc, loc_last_time, loc_last_status