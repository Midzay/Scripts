# -*- coding: utf-8 -*-
'''
Функции, которые необходмы для перемещения данных
'''
import re
import sys
import os.path
import shutil
import os
import MySQLdb


def move_configs_files(MAIN_NGINX, MAIN_SUPERVISOR, PATH_FOLDER_FOR_COPY, config_file_name):
    nginx_file = MAIN_NGINX + '/' + config_file_name
    supervisor_file = MAIN_SUPERVISOR + '/' + config_file_name

    if not os.path.isdir(PATH_FOLDER_FOR_COPY + '/nginx'):
        os.mkdir(PATH_FOLDER_FOR_COPY + '/nginx')
    if not os.path.isdir(PATH_FOLDER_FOR_COPY + '/supervisor'):
        os.mkdir(PATH_FOLDER_FOR_COPY + '/supervisor')

    if os.path.isfile(nginx_file):
        shutil.move(nginx_file, PATH_FOLDER_FOR_COPY + '/nginx')
    else:
        raise Exception('Problem with  nginx')

    if os.path.isfile(supervisor_file):
        shutil.move(supervisor_file, PATH_FOLDER_FOR_COPY + '/supervisor')
    else:
        raise Exception('Problem with  supervisor')


def move_media_files(old_site_path, new_production_FILE_SITE_MEDIA, new_production_FILE_PRIVATE):
    path_media = old_site_path + '/media/'
    if not os.path.isdir(path_media):
        raise Exception('path_media not exist')

    files = os.listdir(path_media)
    for f in files:
        if not f.startswith('cache'):
            try:
                shutil.move(path_media + f, new_production_FILE_SITE_MEDIA)
            except Exception as e:
                print 'Errors move media_files: ', e

    path_private = old_site_path + '/private_files/'
    if not os.path.isdir(path_private):
        raise Exception('path_private not exist')
    files = os.listdir(path_private)
    for f in files:
        try:
            shutil.move(path_private + f, new_production_FILE_PRIVATE)
        except Exception as e:
            print 'Errors move private_files: ', e


def move_app_files(old_site_path, new_production_APPS_SITE):
    path_app = old_site_path + '/site_type/'
    if not os.path.isdir(path_app):
        raise Exception('path_app not exist')
    files = os.listdir(path_app)
    for f in files:
        if os.path.isdir(os.path.join(path_app, f)):
            dir_to = os.path.join(*[new_production_APPS_SITE, 'site_type', f])
            shutil.copytree(os.path.join(path_app, f), dir_to)
        else:
            if not f.endswith("pyc"):
                try:
                    shutil.copy(
                        path_app + f, new_production_APPS_SITE + '/site_type/')
                except Exception as e:
                    print 'Errors move app_files: ', e


def move_prod2_config(config_file_name):
    PATH_CONFIGS = '/new_production/configs'
    try:
        shutil.move(PATH_CONFIGS + '/_nginx/' + config_file_name,
                    PATH_CONFIGS + '/nginx/' + config_file_name)
        shutil.move(PATH_CONFIGS + '/_supervisor/' + config_file_name,
                    PATH_CONFIGS + '/supervisor/' + config_file_name)
    except Exception as e:
        print e


#  Мутация базы данных
def return_connect(host, user, password, base_name):
    return MySQLdb.connect(host, user, password, base_name, charset='utf8')


def add_template_to_base(host, user, password, check_project, db):
    conn = return_connect(host, user, password, db)
    cursor = conn.cursor()
    sql = "SELECT TABLE_NAME FROM information_schema.columns WHERE COLUMN_NAME  like 'template' AND TABLE_SCHEMA ='{}'".format(
        db)
    cursor.execute(sql)
    table_name = cursor.fetchall()

    for t in table_name:
        sql = "UPDATE {}.{} SET template = concat ('{}/',template) WHERE template NOT like  '{}/%'".format(db, t[0],
                                                                                                           check_project,
                                                                                                           check_project)
        cursor.execute(sql)
        conn.commit()

    conn.close()
    return db, len(table_name)


def get_check_project_database(path):
    with open(path + '/site_type/settings_vars.py', 'rb') as file:
        for line in file.readlines():
            if 'TEMPLATE_PROJECT_VAR' in line:
                res = re.findall("\'(\w+)", line)
                check_project = res[0]
            if 'MSQL_NAME_VAR' in line:
                res = re.findall("\'(\w+)", line)
                database = res[0]
    return check_project, database
