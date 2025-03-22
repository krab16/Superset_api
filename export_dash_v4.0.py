import requests
import json
import os
from datetime import datetime
import argparse

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #Disable ssl - warning

SUPERSET_USERNAME = "USER"
SUPERSET_PASSWORD = "PASS"
SUPERSET_DOMAIN = "https://HOST:PORT/"
output_dir = "C:\\Users\\USERNAME\\Desktop\\ss_api\\dashb\\exported"

now = str(datetime.now().date())
if not os.path.exists(os.path.join(output_dir, now)):
    os.mkdir(os.path.join(output_dir, now))
    
output_dir = os.path.join(output_dir, now)
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
