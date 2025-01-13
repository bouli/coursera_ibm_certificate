import requests, sqlite3
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

def extract(url, table_attribs):
    html_page = requests.get(url).text
    html_data = BeautifulSoup(html_page,'html.parser')

    tables = html_data.find_all('tbody')
    count = 0
    df = pd.DataFrame(columns = table_attribs)
    for table in tables:
        lines = table.find_all('tr')
        if len(lines)>0:
            for line in lines:
                col = line.find_all('td')
                if len(col) > 1:
                    links = col[0].find_all('a')
                    if len(links) > 0 and str(col[2].contents[0]) != "—" and str(col[2].contents[0]).replace(',','').isnumeric():
                        data_dict = {
                            table_attribs[0]: links[0].contents[0],
                            table_attribs[1]: col[2].contents[0],
                        }
                        df_append = pd.DataFrame(data_dict, index=[0])
                        df = pd.concat([df, df_append], ignore_index=True)
    return df


def transform(df):
    df['GDP_USD_billions'] = pd.to_numeric(df['GDP_USD_billions'].str.replace(',',''))/1000
    df['GDP_USD_billions'] = df['GDP_USD_billions'].round(2)
    df.rename(columns={'GDP_USD_billions': 'GDP_USD_million',})
    return df

def load_to_csv(df, csv_path):
    df.to_csv(csv_path, index=False)

def load_to_db(df, sql_connection, table_name):
    df.to_sql(table_name, sql_connection, if_exists='replace')

def run_query(query_statement, sql_connection):
    return pd.read_sql_query(query_statement, sql_connection)

def log_progress(message):
    log_file_path = f'{resources_folder}/etl_project_log.txt'
    with open(log_file_path, 'a') as log_file:
        message = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ": " + message + "\n"
        log_file.write(message)
        print(message)


resources_folder = 'resources'
url = 'https://web.archive.org/web/20230902185326/https://en.wikipedia.org/wiki/List_of_countries_by_GDP_%28nominal%29'
csv_path = f'{resources_folder}/Countries_by_GDP.csv'
table_name = 'Countries_by_GDP'
table_attribs = ['Country', 'GDP_USD_billions',]
db_name = f'{resources_folder}/World_Economies.db'
log_progress(f"Preliminaries complete. Initiating ETL process.")


extracted_data = extract(url, table_attribs)
log_progress(f"Data extraction complete. Initiating Transformation process.")

transformed_data = transform(extracted_data)
log_progress(f"Data transformation complete. Initiating Loading process.")

load_to_csv(transformed_data, csv_path)
log_progress(f"Data saved to CSV file.")

conn = sqlite3.connect( db_name )
log_progress(f"SQL Connection initiated.")


load_to_db(transformed_data, conn, table_name)
log_progress(f"Data loaded to Database as table. Running the query.")


query_statement = f"SELECT * from {table_name} WHERE GDP_USD_billions >= 100"
print(run_query(query_statement, conn))

log_progress(f"Process Complete.")

conn.close()
log_progress(f"-")
