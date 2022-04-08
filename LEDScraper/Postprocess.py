import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

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

    data = pd.DataFrame(out_dict.values())

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

    # cleaning: auction identifiers
    data['auction_identifier'] = data[['lot_no','sequence_no']].agg('|'.join, axis=1)

    # postprocess: auction rounds
    data['all_auction_status'] = data[auction_status_cols].agg('|'.join, axis=1)
    data['asset_status'] = [
        'unavailable' if (x.find('ขายได้')!=-1) | (x.find('ถอน')!=-1) else 'available' for x in data['all_auction_status']
    ]
    data[['next_auction_date','next_auction_round']] = \
    data[auction_date_cols+['asset_status']].apply(earliest_next,axis=1)

    # reorder columns
    cols = data.columns
    focus_cols = [
        'auction_identifier',
        'asset_status',
        'next_auction_date',
        'next_auction_round',
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