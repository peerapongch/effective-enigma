import os

if __name__ == '__main__':
  os.system(
    'aws s3 cp --recursive s3://effective-enigma/data/ ./data/'
  )