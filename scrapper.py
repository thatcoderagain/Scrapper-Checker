import sys
import time
import requests
from bs4 import BeautifulSoup

'''
http://multiproxy.org/all_proxy.htm
http://proxy-daily.com/
https://www.socks-proxy.net/
https://www.proxy-list.download/
http://spys.one/en/socks-proxy-list/
https://sockslist.net/list/proxy-socks-5-list/
http://www.gatherproxy.com/sockslist
https://www.my-proxy.com/free-socks-5-proxy.html
https://list.proxylistplus.com/Socks-List-1
'''

def live_socks(max_page):
    url = 'http://www.live-socks.net/'
    page = 1
    proxies = set()
    while page <= max_page:
        try:
            source_code = requests.get(url).text
        except Exception as e:
            print("Internet Connection Error")
        soup = BeautifulSoup(source_code, 'html.parser')
        links = []
        for tag in soup.findAll('h3', {'class': 'post-title entry-title'}):
            links.append(tag.a.get('href'))
        # print('\nLinks: '+str(links)+'\n\n')
        for link in links:
            # print('visiting link - '+link)
            proxies = proxies | live_socks_link(link)
        proxies.remove('')

        for tag in soup.findAll('span', {'id': 'blog-pager-older-link'}):
            url = tag.a.get('href')
            # print('\nURL changed to -' + url)
        page += 1
    print('Total #' + str(len(proxies)) + ' proxies found')
    return proxies


def live_socks_link(url):
    try:
        source_code = requests.get(url).text
    except Exception as e:
        print("Internet Connection Error")
    soup = BeautifulSoup(source_code, 'html.parser')
    proxies = set()
    for tag in soup.findAll('textarea', {'class': ''}):
        proxies = set((tag.text).split('\n'))
        # print(proxies)
    print(str(len(proxies)) + ' proxies found')
    return proxies

# GRAB PROXIES
# AGRS: NO OF PAGES TO VISIT
proxies = live_socks(10)
destination = r'./private/proxies.txt'
fx = open(destination, "w")
for proxy in proxies:
    fx.write(proxy+'\n')


