# -*- coding: utf-8 -*-

import re
import sys
import os.path
import shutil
import os
import MySQLdb
from datetime import datetime
import subprocess
from utils import *

if __name__ == "__main__":

    PRODUCTION = '/production'
    MAIN_NGINX = '/etc/nginx/sites-platform'
    MAIN_SUPERVISOR = '/etc/supervisor/sites-platform'

    user = 'user_db'
    password = 'pass_db'
    host = 'host_db'

    if len(sys.argv) != 2:
        print('One arg: path to old dir in production')
    else:
        path_dir = sys.argv[1]
        all_dir = [site_name for site_name in os.listdir(path_dir) if
                   os.path.isdir(os.path.join(path_dir, site_name))]
        sites = [site for site in all_dir if site.startswith('site_')]
        print sites
        all_sites = len(sites)
        print ' Всего сайтов: ', all_sites
        print 'PRESS'
        raw_input()

        moved_sites_file = 'ok_moved.txt'
        ok_moved = []
        if os.path.isfile(os.path.join(path_dir, moved_sites_file)):
            with open(os.path.join(path_dir, moved_sites_file), 'rb') as f:
                ok_moved = f.readlines()
            ok_moved = [s.strip() for s in ok_moved]
            print ok_moved, 'PRESS'
            raw_input()

        for site_name in sites:

            if site_name not in ok_moved:

                old_site_path = os.path.join(path_dir, site_name)

                print site_name, old_site_path

                new_production_APPS_SITE = os.path.join(
                    '/new_production/apps/', site_name)
                new_production_FILE_SITE_MEDIA = os.path.join('/new_production/files/media/',
                                                           site_name)
                new_production_FILE_PRIVATE = os.path.join('/new_production/files/private/',
                                                        site_name)

                check_project, DB_NAME = get_check_project_database(
                    new_production_APPS_SITE)
                print 'chek_project: ', check_project
                print 'database: ', DB_NAME
                raw_input()

                config_file_name = site_name + '.conf'
                PATH_FOLDER_FOR_COPY = os.path.join(
                    '/home/user/FOLDER_FOR_COPY', site_name)

                if not os.path.isdir(PATH_FOLDER_FOR_COPY):
                    try:
                        os.makedirs(PATH_FOLDER_FOR_COPY)
                    except OSError:
                        print("Creation of the directory %s failed" %
                              PATH_FOLDER_FOR_COPY)

                print 'PATH_FOLDER_FOR_COPY: ', PATH_FOLDER_FOR_COPY
                now = datetime.now()
                now = '-'.join(str(now).split())
                try:
                    os.popen("mysqldump -u %s -p%s -h %s %s  > %s.sql" % (
                        user, password, host, DB_NAME, PATH_FOLDER_FOR_COPY + '/' + DB_NAME + "-" + str(now)))
                except Exception as e:
                    print 'Errors dump sql', e

                print 'sqldump'
            
                move_media_files(
                    old_site_path, new_production_FILE_SITE_MEDIA, new_production_FILE_PRIVATE)

                print 'move media'
                move_app_files(old_site_path, new_production_APPS_SITE)
                print 'move apps'

                add_template_to_base(host, user, password,
                                     check_project, DB_NAME)
                print 'add_template: '

                shutil.copy(old_site_path + '/manage.py',
                            new_production_APPS_SITE)

                if site_name.endswith('_rn'):
                    shutil.copy('/home/user/SETTINGS/RN/settings.py',
                                new_production_APPS_SITE + '/site_type/')
                else:
                    shutil.copy('/home/user/SETTINGS/settings.py',
                                new_production_APPS_SITE + '/site_type/')

                python_path = '/new_production/envs/mainenv/bin/python'
                manage_path = new_production_APPS_SITE + '/manage.py'

                command = python_path + ' ' + manage_path + ' migrate --noinput'
                subprocess.call(command.split())

                command = python_path + ' ' + manage_path + ' collectstatic -c --noinput'
                subprocess.call(command.split())

                print 'collectstatic: '

                command = python_path + ' ' + manage_path + ' thumbnail clear'
                subprocess.call(command.split())

                command = python_path + ' ' + manage_path + ' update_index'
                subprocess.call(command.split())
                print 'PRESS '
                raw_input()

                move_configs_files(MAIN_NGINX, MAIN_SUPERVISOR,
                                   PATH_FOLDER_FOR_COPY, config_file_name)
                move_prod2_config(config_file_name)

                print 'move all congig: '

                command = ' sudo supervisorctl update'
                subprocess.call(command.split())

                command = ' sudo service nginx reload'
                subprocess.call(command.split())

                command = 'head ' + PATH_FOLDER_FOR_COPY + '/nginx/' + site_name + '.conf'
                subprocess.call(command.split())

                os.popen("sudo chown -R www-data:www-data " +
                         new_production_FILE_SITE_MEDIA)
                os.popen("sudo chown -R  www-data:www-data " +
                         new_production_FILE_PRIVATE)

                if os.path.isfile(os.path.join(path_dir, moved_sites_file)):
                    with open(os.path.join(path_dir, moved_sites_file), 'a') as f:
                        f.writelines(site_name + '\n')
                else:
                    with open(os.path.join(path_dir, moved_sites_file), 'w') as f:
                        f.writelines(site_name + '\n')

                with open(os.path.join(old_site_path, 'move.txt'), 'w') as f:
                    f.write('ok')

                    all_sites -= 1
                    print 'Осталось: ', all_sites
                    print 'PRESS'
                    raw_input()

        if os.path.isfile('/home/user/moved_dir.txt'):
            with open('/home/user/moved_dir.txt', 'a') as f:
                f.writelines(path_dir + '\n')
        else:
            with open('/home/user/moved_dir.txt', 'w') as f:
                f.writelines(path_dir + '\n')
