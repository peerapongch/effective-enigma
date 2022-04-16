import os
import pandas as pd
import pickle

def get_existing_db(
  # output to list of dict
  data_dir=None,
  province=None,
  district_id=None,
  full_path=None
):
  
  filename = f'{province}_district{district_id}.pickle'
  
  # sync with s3 to temp
  try:
    os.system(f'aws s3 cp s3://effective-enigma/data/{filename} ./data/{filename}')
  except:
    print(f'No DB exists on S3: {filename}')

  # read from temp to memory
  if not full_path:

    full_path = os.path.join(
      data_dir,
      filename
    )

  if os.path.isfile(full_path):
    db = pickle.load(open(full_path,'rb'))
  else:
    db = {}

  if type(db) == pd.core.frame.DataFrame:
    db = db.set_index('entry_id').to_dict(orient='index')

  return db

def save_db(
  data,
  data_dir=None,
  province=None,
  district_id=None,
  full_path=None
):

  filename = f'{province}_district{district_id}.pickle'
  
  # write to temp
  if not full_path:
    full_path = os.path.join(
      data_dir,
      filename
    )

  pickle.dump(
    data,
    open(
      full_path,
      'wb'
    )
  )

  # push to s3
  try:
    os.system(f'aws s3 cp ./data/{filename} s3://effective-enigma/data/{filename}')
  except:
    print(f'Write failed --> CHEEECK: {filename}')

  return True