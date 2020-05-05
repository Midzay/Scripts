import os
import sys
import time
import asyncio
import aiohttp
from urllib.parse import urlparse
from moduls import pars_arg, ignore_aiohttp_ssl_eror


def find_all_files(inputdir):
    all_files = []
    for file in os.listdir(inputdir):
        if file.endswith('.txt'):
            all_files.append(os.path.join(inputdir, file))
    return all_files


def all_hosts(all_files):
    hosts = []
    for file in all_files:
        with open(file, 'r') as f:
            hosts += [line.strip() for line in f]
        os.remove(file)
    return hosts


async def check_hosts(session, host):
    if 'http' not in host:
        host = 'https://'+host
    try:
        async with session.get(host) as response:
            return response.status, host
    except:
        return 'Name or service not known', host


async def main(hosts):
    tasks = []
    result = []
    async with aiohttp.ClientSession() as session:
        for host in hosts:
            tasks.append(check_hosts(session, host))
        result = await asyncio.gather(*tasks)
    with open(params.out_file_name, 'a+') as f_out:
        for el in result:
            f_out.write(f'Host-name: {el[1]}\t  status:  {el[0]}\n')


if __name__ == '__main__':
    ''' 
    Checks the hosts from the specified directory and saves the result to a file. 
    -h --help
    Example : check_hosts.py -d test -f file.csv
    If such a directory does not exist it will be created

    Default : input_dir='inputdir', out_file_name='result.csv'
    '''
    params = pars_arg(sys.argv[1:])
    if not os.path.exists(params.input_dir):
        os.mkdir(params.input_dir)

    all_files = []
    while True:
        time.sleep(2)
        all_files = find_all_files(params.input_dir)
        if all_files:
            hosts = all_hosts(all_files)
            if hosts:
                now = time.time()
                loop = asyncio.get_event_loop()
                ignore_aiohttp_ssl_eror(loop)
                loop.run_until_complete(main(hosts))
                print(time.time()-now)
