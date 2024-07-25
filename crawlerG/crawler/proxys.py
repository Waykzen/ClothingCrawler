import requests

ROTATING_PROXY_LIST = [
    'http://103.237.144.232:1311',

    'http://37.27.82.72:80',
    
]

url = 'http://httpbin.org/ip'

for proxy in ROTATING_PROXY_LIST:
    try:
        response = requests.get(url, proxies={'http': proxy, 'https': proxy}, timeout=5)
        if response.status_code == 200:
            print(f'Proxy {proxy} is working')
        else:
            print(f'Proxy {proxy} returned status code {response.status_code}')
    except Exception as e:
        print(f'Proxy {proxy} failed: {e}')