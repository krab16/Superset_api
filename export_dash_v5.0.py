import requests
import json
import os
from datetime import datetime
import argparse
import psycopg2
import urllib3
import re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #Disable ssl - warning

SUPERSET_USERNAME = "LOGIN"
SUPERSET_PASSWORD = "PASS"
SUPERSET_DOMAIN = "https://HOST:PORT"
output_dir = "C:\\Users\\USER\\Desktop\\ss_api\\dashb\\exported"

## DEV SS DB
LOGIN_DEV = 'LOGIN' ## login to UAT Superset DataBase
PASSWORD_DEV = 'PASS' ## password to UAT superset database
HOST_DEV = 'HOST:POSRT' 
DATABASE_DEV = 'DATABASE_NAME' 
SHEMA_DEV = 'SHEMA'
sreda = 'DEV' #dev #prod ##Select to import target server #for future funcion

now = str(datetime.now().date())
output_dir = os.path.join(output_dir, now)
os.makedirs(output_dir, exist_ok=True)
    

CSS_root_dir = os.path.join(output_dir, 'CSS')  #folder with CSS file
os.makedirs(CSS_root_dir, exist_ok=True)
dashboard_dict = list()
session = requests.session()

endpoint = "/api/v1/security/login"
url = f"{SUPERSET_DOMAIN}{endpoint}"
jwt_token =session.post(
    url = f"{SUPERSET_DOMAIN}{endpoint}",
    json={
        "username": SUPERSET_USERNAME,
        "password": SUPERSET_PASSWORD,
        "provider": "ldap",
        "refresh": False
        } ,
    verify = False  
)
if jwt_token.status_code != 200:
    Exception(f"Got HTTP code of {jwt_token.status_code} from {url}; expected 200")
else:
    jwt_token = jwt_token.json()["access_token"]  
    
def get_dashboard_ids(jwt_token):
    url = f"{SUPERSET_DOMAIN}/api/v1/dashboard/?q=(page:0,page_size:250)"
    headers = {'Authorization': f'Bearer {jwt_token}'}
    response = requests.get(url,verify = False, headers=headers,)
    if response.status_code != 200:
        raise Exception(f"Failed to get dashboard IDs: {response.text}")
    
    # Формируем список с ids дашбордов и именами
    dashboards = response.json()['result']
    dashboard_ids = [dashboard['id'] for dashboard in dashboards]
    for i in dashboards:
        dashboard_dict.append({'id': i['id'], 'name': i['dashboard_title']})
    return dashboard_ids

def export_dashboards(jwt_token, dashboard_ids, output_dir, filename):
    url = f"{SUPERSET_DOMAIN}/api/v1/dashboard/export/?q={json.dumps(dashboard_ids)}"
    headers = {'Authorization': f'Bearer {jwt_token}'}
    response = requests.get(url, verify = False, headers=headers, stream=True)
    if response.status_code == 200:
        zip_file_path = os.path.join(output_dir, filename)
        with open(zip_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=128):
                f.write(chunk)
        return zip_file_path
    else:
        raise Exception(f"Failed to export dashboards: {response.text}")

def create_parser():  # создание парсера
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--select', dest="select", type=str, choices=['all', 'single'], 
                        help="'all/none' to export all, 'single' to export single")
    parser.add_argument("-n", "--num", dest="num", type=int, default=0, help="num das")
    return parser    

parser = create_parser()
namespace = parser.parse_args()
dashboard_ids = get_dashboard_ids(jwt_token)
current_date = datetime.now().strftime("%Y-%m-%d")

if namespace.select == 'all':
    for dash_id in dashboard_ids:
        dashboard_name = next(dashboard['name'] for dashboard in dashboard_dict if dashboard['id'] == dash_id)
        filename = f"dashboards_{dashboard_name}.zip"
        zip_file_path = export_dashboards(jwt_token, [dash_id], output_dir, filename)
        print(f"Дашборд '{dashboard_name}' успешно экспортирован в {zip_file_path}")

elif namespace.num:
    # # Выгрузка одного дашборда с названием dashboard_<ID>_<дата>.zip
    if namespace.num not in [dashboard['id'] for dashboard in dashboard_dict]:
        print('Not valid dashboard ID')
    else:
        selected_dashboard_id = namespace.num #select_single_dashboard()
        dashboard_name = next(dashboard['name'] for dashboard in dashboard_dict if dashboard['id'] == selected_dashboard_id)
        filename = f"dashboards_{dashboard_name}.zip"
        zip_file_path = export_dashboards(jwt_token, [selected_dashboard_id], output_dir, filename)
        print(f"Дашборд '{dashboard_name}' успешно экспортирован в {zip_file_path}")
        
session.close()

## get chart list to edit CSS

URI = f'postgresql://{LOGIN_DEV}:{PASSWORD_DEV}@{HOST_DEV}/{DATABASE_DEV}' #URI to connect to Superset database

##check connect to DB
try:
    conn = psycopg2.connect(URI)
    cur = conn.cursor() #connect
except:
    print("Can't connect to database")
chart_list_dev = os.path.join(CSS_root_dir,'chart_list_dev.txt')
## for log file 
try:
    os.remove(chart_list_dev)
except FileNotFoundError:
    pass


## get chart id/name from UAT db SS and save to file
cur.execute(f"select concat(id,', ', slice_name) from {SHEMA_DEV}.slices order by id" )
chart_list = cur.fetchall()
    
with open(chart_list_dev, 'a', encoding="utf-8") as out:
    for i, value in enumerate(chart_list):    
        out.writelines(str(chart_list[i]).replace("(", "").replace(",)"," "))     

work_dir = os.path.join(CSS_root_dir, sreda)
os.makedirs(work_dir, exist_ok=True)  # Создаем директорию, если она не существует   

def remove_empty_lines(filename): ## для очистки от лишних переносов строк
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines=[line for line in file if line.strip() != '']
        with open (filename, 'w', encoding='utf-8') as file:
            file.writelines(lines)
            
    except Exception as e:
        print(f'Ошибка при обработке {filename}: {e}')


def save_rows_to_file(rows): ## сохраняем CSS в файл 
    for row in rows:
        dashboard_title = row[0]
        css_content = row[1]        
        filename = f"{dashboard_title}_dev.css"     # Формируем имя файла
        css_with_comment = f"/* {dashboard_title} */\n{css_content}"    # Добавляем комментарий с dashboard_title в начало CSS-кода
                # Сохраняем в файл
        with open(os.path.join(work_dir, filename), 'w', encoding='utf-8') as file:
            file.write(css_with_comment)
            
        remove_empty_lines(os.path.join(work_dir,filename))
        
        
cur.execute(f"SELECT dashboard_title, css FROM {SHEMA_DEV}.dashboards")  
CSS_full_text = cur.fetchall() 

if CSS_full_text:
    save_rows_to_file(CSS_full_text)  
        
        
cur.close()
conn.close()            