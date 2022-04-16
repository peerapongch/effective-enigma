import pickle
import glob
import pandas as pd
from tqdm import tqdm
import os

def run():
  # os.system(
  #   'aws s3 cp --recursive s3://effective-enigma/data/ ./data/'
  # )

  files = glob.glob('./data/bangkok_district*.pickle')
  data = pd.DataFrame()

  data = pd.concat([
    pickle.load(open(f,'rb')) for f in tqdm(files)
  ])

  # measure
  available = data[data['asset_status']=='available'].shape[0]
  got_loc = data[(data['asset_status']=='available') & ~(data['loc_coordinates'].isin(['NA','']))].shape[0]
  unique_loc = data['loc_coordinates'].nunique()

  print(f'Collected: {data.shape[0]}')
  print(f'Available: {available}')
  print(f'Has loc: {got_loc}')
  print(f'Unique loc: {unique_loc}')

if __name__ == '__main__':
  run()