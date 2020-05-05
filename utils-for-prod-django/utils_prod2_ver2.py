# -*- coding: utf-8 -*-
import sys
import argparse
import os, os.path
from urlparse import urlparse
import re
import subprocess, shlex
import argparse
from subprocess import Popen, PIPE



PATH_TO_SUPERVISOR = '/new_production/configs/supervisor/'
PATH_TO_NGINX = '/new_production/configs/nginx/'
PATH_TO_APPS = '/new_production/apps/'

python = '/new_production/envs/mainenv/bin/python'


def pars_arg(args):
    parser = argparse.ArgumentParser(description='Enter domain name or mask all-  sites')
    parser.add_argument(
        '--select',
        dest="select_sites",
        nargs='+',
        default='no_args',
        help='"all" - all sites, "other_text"- mask for search')
    parser.add_argument(
        '--commands',
        dest="commands",
        nargs='+',
        default=False,
        choices=['restart_supervisor', 'colstat', 'make_migrate', 'clear_cache', 'all_commands'],
    )
    parser.add_argument(
        '-a',
        dest="manual",
        action='store_true',
        default=False,
        help='-a then avtomat data entry ')

    parser.add_argument(
        '--check_errors',
        dest="check_errors",
        action='store_true',
        default=False,
        help='for check errors ')

    return parser.parse_args(args)


def red_text(text, mask):
    pos = text.find(mask)
    red_text = text[:pos] + bcolors.FAIL + text[pos:pos + len(mask)] + bcolors.ENDC + text[pos + len(mask):]
    return red_text


def black_text(text):
    black_text = bcolors.FAIL + bcolors.ENDC + text
    return black_text


def get_list_sites_on_mask(mask_for_search):
    list_siites = []
    list_all = []
    for mask in mask_for_search:
        for fname in os.listdir(PATH_TO_NGINX):
            with open(os.path.join(PATH_TO_NGINX, fname), 'r') as file_nginx:
                for line in file_nginx.readlines():
                    if 'server_name' in line:
                        line = [el.strip() for el in line.split()[1:]]
                        domains = ' '.join(line)
                        if (mask in fname) or (mask in domains):
                            list_siites.append(fname)
                            if mask in fname:
                                fname_conf = red_text(fname, mask)
                            else:
                                fname_conf = black_text(fname)
                            list_all.append(fname_conf)
                            if mask in domains:
                                domen_sites = red_text(domains, mask)
                            else:
                                domen_sites = black_text(domains)
                            print '{:-<65}'.format(fname_conf.strip()), domen_sites

    return set(list_siites)


def restart_supervisor(site_name):
    command = 'sudo supervisorctl restart ' + site_name
    proc1 = subprocess.Popen(command.split(), stdout=PIPE, stderr=PIPE)
    text = proc1.communicate()
    print params
    if int(params.check_errors) and 'error' in text[0].lower():
        raise Exception('Ошибка  При перезапуске ')
    else:
        print text[0].split('\n')

def open_supervisor(conf_file):
    conf_file = os.path.join(PATH_TO_SUPERVISOR, conf_file)
    if os.path.exists(conf_file):
        command = 'sudo nano ' + conf_file
        subprocess.call(command.split())
    else:
        print bcolors.FAIL + 'Нет такого файла SUPERVISOR' + bcolors.ENDC


def open_nginx(conf_file):
    conf_file = os.path.join(PATH_TO_NGINX, conf_file)
    if os.path.exists(conf_file):
        command = 'sudo nano ' + conf_file
        subprocess.call(command.split())
    else:
        print bcolors.FAIL + 'Нет такого файла NGINX' + bcolors.ENDC


def colstat(site_name):
    command = python + ' ' + os.path.join(PATH_TO_APPS,
                                          site_name) + '/manage.py collectstatic -c --noinput'
    proc1 = subprocess.Popen(command.split(), stderr=PIPE)
    text = proc1.communicate()
    print text
    if int(params.check_errors) and text[1] != '':
        raise Exception('Ошибка  При сборке статики ')


def create_superuser(site_name, login, passwd):
  
    com2 = 'echo "from django.contrib.auth.models import User; User.objects.create_superuser(\'' + login + '\', \'exampl@example.com\', \'' + passwd + '\')"'
    com3 = ' | '
    com4 = python + ' ' + os.path.join(PATH_TO_APPS, site_name) + '/manage.py shell'
    command = com2 + com3 + com4
    print command.split()
    proc1 = subprocess.Popen(command, shell=True, stdout=PIPE, stderr=PIPE )

    text = proc1.communicate()
    print text
    if int(params.check_errors) and len(text[1]) > 200:
        raise Exception('Ошибка  При добавлении пользователя')
    print text[1]


def change_password_user(site_name, login, passwd, first_name, last_name):
    com2 = 'echo "from django.contrib.auth.models import User; u = User.objects.get(username__exact=\'' + login + '\');'
    if len(passwd) != 0:
        com2 += 'u.set_password(\'' + passwd + '\');'
    if len(first_name) != 0:
        com2 += 'u.first_name=\'' + first_name + '\';'
    if len(last_name) != 0:
        com2 += 'u.last_name=\'' + last_name + '\';'
    com2 += 'u.save()"'

    com3 = ' | '
    com4 = python + ' ' + os.path.join(PATH_TO_APPS, site_name) + '/manage.py shell'
    command = com2 + com3 + com4
    print site_name
    proc1 = subprocess.Popen(command, shell=True, stderr=PIPE, stdout=PIPE, )
    text = proc1.communicate()
    print text
    if int(params.check_errors) and len(text[1]) > 200:
        raise Exception('Ошибка  При изменении пользователя пользователя')


def make_migrate(site_name):
    command = python + ' ' + os.path.join(PATH_TO_APPS, site_name) + '/manage.py makemigrations --noinput'
    
    proc1 = subprocess.Popen(command, shell=True, stderr=PIPE, stdout=PIPE, )
    text = proc1.communicate()
    
    command = python + ' ' + os.path.join(PATH_TO_APPS, site_name) + '/manage.py migrate --noinput'
    
    proc1 = subprocess.Popen(command, shell=True, stderr=PIPE, stdout=PIPE, )
    text = proc1.communicate()
   


def clear_cache(site_name):
    command = python + ' ' + os.path.join(PATH_TO_APPS,
                                          site_name) + '/manage.py thumbnail clear'
    subprocess.call(command.split())


CHOISE_COMANDS = ['открыть файл supervisor:', 'открыть файл nginx', 'supervisor restart', 'собрать статику:',
                  'создать и применить миграции:', 'почистить cache:', 'stat+migr+cache+supervisor:',
                  'create_superuser', 'Изменить Пароль', '0 - выход:']


def run_manual_commands(list_sites):
    if len(list_sites) == 1:
        conf_file = list(list_sites)[0]
        i = 0
    else:
        i = 2
    while True:
        n = 0
        print
        for com in CHOISE_COMANDS[i:-1]:
            n += 1
            print n, '-', com
        print '0 - выход:'
        try:
            choise = int(raw_input('Enter number \n'))
            if choise == 0:
                break
        except KeyboardInterrupt:
            print ' EXIT'
            break
        if choise + i == 8:
            login = raw_input('Введите login: ')
            passwd = raw_input('Введите passwd: ')

            for site in list_sites:
                site_name = site.split('.')[0]
                create_superuser(site_name, login, passwd, )
        if choise + i == 9:
            login = raw_input('Введите login: ')
            passwd = raw_input('Введите новый passwd: ')
            first_name = raw_input('Введите first_name: ')
            last_name = raw_input('Введите last_name: ')
            for site in list_sites:
                site_name = site.split('.')[0]
                change_password_user(site_name, login, passwd, first_name, last_name)
        for site in list_sites:
            site_name = site.split('.')[0]
            if choise + i == 1:
                open_supervisor(conf_file)
            elif choise + i == 2:
                open_nginx(conf_file)
            elif choise + i == 3:
                restart_supervisor(site_name)
            elif choise + i == 4:
                colstat(site_name)
            elif choise + i == 5:
                make_migrate(site_name)
            elif choise + i == 6:
                clear_cache(site_name)
            elif choise + i == 7:
                colstat(site_name)
                make_migrate(site_name)
                clear_cache(site_name)
                restart_supervisor(site_name)


class bcolors:
    # HEADER = '\033[95m'
    # OKBLUE = '\033[94m'
    # OKGREEN = '\033[92m'
    # WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    # BOLD = '\033[1m'
    # UNDERLINE = '\033[4m'


def avtomatic_commands(list_commands, list_sites):
    for site_name in list_sites:
        site_name = site_name.split('.')[0]
        for cmd in list_commands:
            if cmd == 'restart_supervisor':
                restart_supervisor(site_name)
                print
            elif cmd == 'colstat':
                colstat(site_name)
            elif cmd == 'make_migrate':
                make_migrate(site_name)
            elif cmd == 'clear_cache':
                clear_cache(site_name)
            elif cmd == 'all_commands':
                colstat(site_name)
                make_migrate(site_name)
                clear_cache(site_name)
                restart_supervisor(site_name)


if __name__ == "__main__":
    try:
        params = pars_arg(sys.argv[1:])
        if 'all' in params.select_sites:
            list_sites = os.listdir(PATH_TO_NGINX)
            for site in list_sites:
                print site
            print
            print 'Итого:', len(list_sites)
            if not params.commands or params.manual:
                run_manual_commands(list_sites)
            else:
                avtomatic_commands(params.commands, list_sites)
        else:
            list_sites = get_list_sites_on_mask(params.select_sites)
            print len(list_sites)
            print
            if not params.commands or not params.manual:
                run_manual_commands(list(list_sites))
            else:
                avtomatic_commands(params.commands, list_sites)
    except KeyboardInterrupt:
        print ' Exit'
