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
  if not full_path:

    filename = f'{province}_district{district_id}.pickle'
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
  if not full_path:

    filename = f'{province}_district{district_id}.pickle'
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

  return True