# Network
import urllib.request, urllib.parse, urllib.error
import http.cookiejar

# Concurrency
import threading
import queue
import itertools
import time

# Global variables
proxy_directory = './proxy/tocheck'
socks5_outfilename = './proxy/live/SOCKS5.txt'
socks4_outfilename = './proxy/live/SOCKS4.txt'
http_outfilename = './proxy/live/HTTP.txt'
test_url = 'http://www.google.com/humans.txt'

proxyNumber = int(0)
deadProxyNumber = int(0)
thread_number = 1000
timeout_value = 10
socks5_good_proxies = itertools.count()
socks4_good_proxies = itertools.count()
http_good_proxies = itertools.count()
start_time = time.time()

# Safe print()
mylock = threading.Lock()
def sprint(*a, **b):
    with mylock:
        print(*a, **b)

class PrintThread(threading.Thread):
    def __init__(self, queue, socks5_outfile, socks4_outfile, http_outfile):
        threading.Thread.__init__(self)
        self.queue = queue
        self.socks5_outfile = open(socks5_outfilename, 'w')
        self.socks4_outfile = open(socks4_outfilename, 'w')
        self.http_outfile = open(http_outfilename, 'w')
        self.shutdown = False

    def write(self, line, file):
        print(line, file=file)

    def run(self):
        global proxyNumber
        while not self.shutdown:
            proxy, proxy_type = self.queue.get()
            if proxy_type == 'SOCKS5':
                self.write(proxy, self.socks5_outfile)
            elif proxy_type == 'SOCKS4':
                self.write(proxy, self.socks4_outfile)
            elif proxy_type == 'HTTP':
                self.write(proxy, self.http_outfile)
            proxyNumber += 1
            sprint('#{:<8d}\t{:24s}\t{:s}'.format(proxyNumber, proxy, proxy_type))
            self.queue.task_done()

    def terminate(self):
        self.socks5_outfile.close()
        self.socks4_outfile.close()
        self.http_outfile.close()
        self.shutdown = True

class ProcessThread(threading.Thread):
    def __init__(self, id, task_queue, out_queue):
        threading.Thread.__init__(self)
        self.task_queue = task_queue
        self.out_queue  = out_queue
        self.id = id

    def run(self):
        while True:
            task   = self.task_queue.get()
            result = self.process(task)

            if result is not None:
                proxy, proxy_type = result
                if proxy_type == 'SOCKS5':
                    next(socks5_good_proxies)
                elif proxy_type == 'SOCKS4':
                    next(socks4_good_proxies)
                elif proxy_type == 'HTTP':
                    next(http_good_proxies)
                self.out_queue.put(result)

            self.task_queue.task_done()

    def process(self, task):
        global deadProxyNumber
        proxy = task
        cj =  http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),urllib.request.HTTPRedirectHandler(),
            urllib.request.ProxyHandler({ 'socks5' : proxy }))
        try:
            t1 = time.time()
            response = opener.open(test_url, timeout=timeout_value).read()
            t2 = time.time()
        except Exception as e:
            cj =  http.cookiejar.CookieJar()
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),urllib.request.HTTPRedirectHandler(),
                urllib.request.ProxyHandler({ 'socks4' : proxy }))
            try:
                t1 = time.time()
                response = opener.open(test_url, timeout=timeout_value).read()
                t2 = time.time()
            except Exception as e:
                cj =  http.cookiejar.CookieJar()
                opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),urllib.request.HTTPRedirectHandler(),
                    urllib.request.ProxyHandler({ 'http' : proxy }))
                try:
                    t1 = time.time()
                    response = opener.open(test_url, timeout=timeout_value).read()
                    t2 = time.time()
                except Exception as e:
                    deadProxyNumber += 1
                    sprint('@{:<8d}\t{:24s}\t{:s}'.format(deadProxyNumber, proxy, 'DEAD'))
                    return None

                return proxy, 'HTTP'

            return proxy, 'SOCKS4'

        return proxy, 'SOCKS5'

    def terminate(self):
        None

# MAIN

input_queue  = queue.Queue()
result_queue = queue.Queue()

# Spawn worker threads
workers = []
for i in range(0, thread_number):
    t = ProcessThread(i, input_queue, result_queue)
    t.setDaemon(True)
    t.start()
    workers.append(t)

# Spawn printer thread to print
f_printer = PrintThread(result_queue, socks5_outfilename, socks4_outfilename, http_outfilename)
f_printer.setDaemon(True)
f_printer.start()

# Add some stuff to the input queue
start_time = time.time()

proxy_list = []
import os
for root, dirs, files in os.walk(proxy_directory):
    for file in files:
        if file.endswith('.txt'):
            file_line_list = [line.rstrip('\n') for line in open(os.path.join(root, file), 'r')]
            proxy_list.extend(file_line_list)

for proxy in proxy_list:
    input_queue.put(proxy)

total_proxies = len(proxy_list)
print('%d Proxies To Check' % total_proxies)

if total_proxies == 0:
    print('No proxy found to Check')
    exit()

# Wait for queue to get empty
input_queue.join()
result_queue.join()

while (not input_queue.empty()):
   time.sleep(1)

# Shutdown
f_printer.terminate()
for worker in workers:
    worker.terminate()

# Print some info
good_proxies = float(next(socks5_good_proxies) + next(socks4_good_proxies) + next(http_good_proxies))
print("\n\nIn: %d. Good: %d, that's %.2f%%" % (total_proxies, good_proxies, good_proxies/total_proxies*100.0))

end_time = time.time()
print("Total Time elapsed: %.1f seconds." % (end_time - start_time))
