from datetime import datetime
import requests
import pandas as pd
import numpy as np
import sqlite3
from bs4 import BeautifulSoup

def log_progress(message):
  with open(log_path, 'a') as f:
    message = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' - ' + message + '\n'
    f.write(message)
    print(message)

def extract_data(url, table_attrs_extract):
  df = pd.DataFrame(columns=table_attrs_extract)

  response = requests.get(url)
  tables = BeautifulSoup(response.content, 'html.parser').find_all('table')
  if(len(tables) > 0):
    for table in tables:
      rows = table.find_all('tr')
      if(rows[0].find_all('th')[2].text[0:10] == 'Market cap'):

        for row in rows[1:]:
          dict_data = {
            table_attrs_extract[0]: str.strip(row.find_all('td')[1].text),
            table_attrs_extract[1]: str.strip(row.find_all('td')[2].text),
          }
          df = pd.concat([df, pd.DataFrame(dict_data, index=[0])], ignore_index=True)

  return df


def transform_data(df, csv_path):
  df['MC_USD_Billion'] = pd.to_numeric(df['MC_USD_Billion'])
  df_exchange = pd.read_csv(csv_path)
  for index, exchange_rate in df_exchange.iterrows():
    df['MC_'+exchange_rate['Currency']+'_Billion'] = [np.round(x*exchange_rate['Rate'],2) for x in df['MC_USD_Billion']]
  return df

def load_to_csv(df, csv_path):
  df.to_csv(csv_path, index=False)

def load_to_db(df, sql_connection, table_name):
  df.to_sql(table_name, sql_connection, if_exists='replace', index=False)

def run_query(query_statement, sql_connection):
  df = pd.read_sql(query_statement, sql_connection)
  return df



url = 'https://web.archive.org/web/20230908091635 /https://en.wikipedia.org/wiki/List_of_largest_banks'
table_attrs_extract = ['Name', 'MC_USD_Billion']
table_attrs = ['Name', 'MC_USD_Billion', 'MC_GBP_Billion', 'MC_EUR_Billion', 'MC_INR_Billion']
table_name = 'Largest_banks'
resource_folder = 'resources'
csv_path = resource_folder + '/Largest_banks_data.csv'
exchange_csv_path = resource_folder + '/exchange_rate.csv'
db_name = resource_folder + '/Banks.db'
log_path = resource_folder + '/code_log.txt'

log_progress('Preliminaries complete. Initiating ETL process')

df = extract_data(url, table_attrs_extract)
log_progress('Data extraction complete. Initiating Transformation process')

df = transform_data(df, exchange_csv_path)
log_progress('Data transformation complete. Initiating Loading process')

load_to_csv(df, csv_path)
log_progress('Data saved to CSV file')

conn = sqlite3.connect(db_name)
log_progress('SQL Connection initiated')

load_to_db(df, conn, table_name)
log_progress('Data loaded to Database as a table, Executing queries')

print(run_query('SELECT Name from Largest_banks LIMIT 5', conn))
log_progress('Process Complete')

log_progress('Server Connection closed')
