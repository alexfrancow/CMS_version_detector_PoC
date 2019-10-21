from bs4 import BeautifulSoup
import pandas as pd
import concurrent.futures
import requests
import threading
import time
from multiprocessing import Pool
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from termcolor import colored


threadLocal = threading.local()


def get_session():
    if not hasattr(threadLocal, "session"):
        threadLocal.session = requests.Session()
    return threadLocal.session


def get_wp_version(url):
    headers = {
        'X-Api-Key': 'wappalyzer.api.demo.key',
    }
    try:
        response = requests.get('https://api.wappalyzer.com/lookup/v1/?url='+url, headers=headers).json()
        for r in response:
            for k, v in r.items():
                if k == "applications":
                    for aplication in v:
                        if "WordPress" in aplication.get("name", ):
                            name = aplication.get("name", )
                            version = aplication.get("versions", )

        version = ''.join(version)
        return version
    except:
        return "Null"


def get_wp_manual_version(url):
    session = get_session()
    try:
        with session.get(url, verify=False, timeout=5) as response:
            if response.status_code == 200:
                try:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    version = soup.find('meta', content=re.compile("WordPress\s\d"))
                    version = version.get('content').split(" ")[1]
                    return version
                except:
                    return "Null"
            else:
                return "Null"
    except:
        return "Null"


def get_bytes(url):
    session = get_session()
    try:
        with session.get(url, verify=False, timeout=5) as response:
            if response.status_code == 200:
                bytess = len(response.content)
            elif response.status_code != 200:
                bytess = 0
    except:
        bytess = 0
    return bytess


def create_dataset_to_predict(url):
    df = pd.read_csv('dataset/cols.csv').drop(columns="Unnamed: 0")
    client = df['Files'].values

    main_array = []
    bytess = []
    time_scan = time.time()
    session = get_session()
    version = get_wp_manual_version(url)
    urlypath = []
    for c in client:
        if "Version" in c:
            continue
        urlypath.append(url+c)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        bytess = list(executor.map(get_bytes, urlypath))
        for b in bytess:
            main_array.append(b)

    main_array.append(version)
    df = pd.DataFrame(columns=client)
    if len(main_array) == 46:
        try:
            df.loc[len(df)] = main_array
            X = df.iloc[:, 0:-1].values
            return X

        except:
            print(url)

 
def create_dataset(url):
    ##clear_output()
    main_array = []
    global count_iter
    
    #if not count_iter%100:
        #clear_output()
    count_iter += 1
    
    bytess = []
    time_scan = time.time()
    session = get_session()
    version = get_wp_manual_version(url)
    # Si no encuentra la versión ya descartamos la url y añadimos un array de ceros.
    if version != "Null":
        urlypath = []
        for c in client:  
            if "Version" in c:
                continue
            urlypath.append(url+c)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            bytess = list(executor.map(get_bytes, urlypath))
            for b in bytess:
                main_array.append(b)            
 
        print(colored("["+str(count_iter)+"] "+url+" | WP-Version: "+version+" ("+str(round(float(0.00000095367432)*sum(bytess), 3))+"/Kb) "+ f' | Tiempo Escaneo: {round(time.time() - time_scan, 3)}', "green", attrs=['bold']))
    else:
        listofzeros = [0] * 45
        for z in listofzeros:
            main_array.append(z)
        print(colored("["+str(count_iter)+"] "+url+" | WP-Version: "+version+" ("+str(round(float(0.00000095367432)*sum(bytess), 3))+"/Kb) "+ f' | Tiempo Escaneo: {round(time.time() - time_scan, 3)}', "red"))
    
    main_array.append(version) 
    if len(main_array) == 46:
        try:
            df.loc[len(df)] = main_array
            return df
        except:
            print(url)



def create_dataset_multiple(urls):
    global count_iter 
    count_iter = -12
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        df = pd.concat(executor.map(create_dataset, urls))
        # Al concatenar perderemos el index lo reseteamos
        #df.reset_index()
    return df


def get_array(file):
    with open(file, "r") as f:
        urls = []
        for line in f:
            urls.append(line.replace("\n", "")) 
    return urls
