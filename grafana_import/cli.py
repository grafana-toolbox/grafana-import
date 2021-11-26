#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Mon March 15th 2021

@author: jfpik

Suivi des modifications :
    V 0.0.0 - 2021/03/15 - JF. PIK - initial version

"""
#***********************************************************************************************
#
#
# TODO:
#***********************************************************************************************


from grafana_import.constants import (PKG_NAME, PKG_VERSION, JSON_CONFIG_NAME)

import argparse, json, sys, os, re, socket, logging
import unicodedata, traceback

from datetime import datetime

from grafana_api.grafana_face import GrafanaFace
import grafana_api.grafana_api as GrafanaApi

from grafana_import.jsonConfig import jsonConfig

#******************************************************************************************
config = None

#******************************************************************************************
def get_dashboard_content(config, args, grafana_api, dashboard_name):

   try:
      res = grafana_api.search.search_dashboards(
	type_='dash-db'
	, limit=config['grafana']['search_api_limit']
	)
   except Exception as e:
      print("error: {}".format(traceback.format_exc()) )
#      print("error: {} - message: {}".format(e.__doc__, e.message) )
      return None
   dashboards = res
   board = None
   b_found = False
   if args.verbose:
      print("There are {0} dashboards:".format(len(dashboards)))
   for board in dashboards:
      if board['title'] == dashboard_name:
         b_found = True
         if args.verbose:
            print("dashboard found")
         break
   if b_found and board:
      try:
         board = grafana_api.dashboard.get_dashboard(board['uid'])
      except Exception as e:
         print("error: {}".format(traceback.format_exc()) )
   else:
      board = None

   return board

#******************************************************************************************
def get_folder(config, args, grafana_api, folder_name):

   try:
      res = grafana_api.folder.get_all_folders()
   except Exception as e:
      print("error: {}".format(traceback.format_exc()) )
#      print("error: {} - message: {}".format(e.__doc__, e.message) )
      return None

   folders = res
   folder = None

   if args.verbose:
      print("There are {0} folderss:".format(len(folders)))
   for tmp_folder in folders:
      if tmp_folder['title'] == folder_name:
         if args.verbose:
            print("Folder found")
         folder = tmp_folder
         break

   return folder

#******************************************************************************************
def remove_accents_and_space(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    res = u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
    res = re.sub('\s+', '_', res)
    return res

#******************************************************************************************
def save_dashboard(config, args, base_path, dashboard_name, params, action):

    output_file = base_path + '/'

    if 'exports_path' in config['general']:
       output_file += config['general']['exports_path'] + '/'

    if 'export_suffix' in config['general']:
       dashboard_name += datetime.today().strftime(config['general']['export_suffix'])

    file_name = remove_accents_and_space( dashboard_name )
    output_file += file_name + '.json'
    try:
       output = open(output_file, 'w')
    except OSError as e:
       print('File {0} error: {1}.'.format(output_file, e.strerror))
       sys.exit(2)

    content = None
    if args.pretty:
       content = json.dumps( params, sort_keys=True, indent=2 )
    else:
       content = json.dumps( params )
    output.write( content )
    output.close()
    print("OK: dashboard {1} to '{0}'.".format(output_file, action))
 
#******************************************************************************************
class myArgs:
  attrs = [ 'pattern'
                , 'base_path', 'config_file'
                , 'dashboard_name'
                , 'pretty', 'overwrite', 'verbose'
                ]
  def __init__(self):

    for attr in myArgs.attrs:
        setattr(self, attr, None)

  def __repr__(self):
    obj = {}
    for attr in myArgs.attrs:
        val = getattr(self, attr)
        if not val is None:
           obj[attr] = val
    return json.dumps(obj)

 
#***********************************************************************************************
def main():
   #******************************************************************
   # get command line arguments

   parser = argparse.ArgumentParser(description='play with grafana dashboards json files.')
   parser.add_argument('-b', '--base_path'
			, help='set base directory to find default files.')
   parser.add_argument('-c', '--config_file'
			, help='path to config files.')

   parser.add_argument('-d', '--dashboard_name'
			, help='name of dashboard to export.')

   parser.add_argument('-f', '--grafana_folder'
			, help='the folder name where to import into Grafana.')

   parser.add_argument('-i', '--dashboard_file'
			, help='path to the dashboard file to import into Grafana.')

   parser.add_argument('-o', '--overwrite'
			, action='store_true'
			, help='if a dashboard with same name exists in folder, overwrite it with this new one.')

   parser.add_argument('-p', '--pretty'
			, action='store_true'
			, help='use JSON indentation when exporting or extraction of dashboards.')

   parser.add_argument('-v ', '--verbose'
			, action='store_true'
			, help='verbose mode; display log message to stdout.')

   parser.add_argument('-V', '--version'
			, action='version', version='{0} {1}'.format(PKG_NAME, PKG_VERSION)
			, help='display program version and exit..')

   parser.add_argument('action', metavar='ACTION'
			, nargs='?'
			, choices=['import', 'export']
			, default='import'
			, help='action to perform. Is one of \'export\' or \'import\' (default).\nexport: lookup for dashboard name in Grafana and dump it to local file.\nimport: import a local dashboard file (previously exported) to Grafana.') 
   inArgs = myArgs()
   args = parser.parse_args(namespace=inArgs)

   base_path = '.'
#   base_path = os.path.dirname(os.path.abspath(__file__))
   if args.base_path is not None:
      base_path = inArgs.base_path

   config_file = base_path + '/' + JSON_CONFIG_NAME
   if args.config_file is not None:
      config_file = inArgs.config_file

   confObj = jsonConfig(config_file)
   if confObj is None:
       print( 'init config failure !')
       sys.exit(2)
   config = confObj.load()
   if config is None:
       print( confObj.err_msg )
       sys.exit(2)

   if args.verbose is None:
      if 'debug' in config['general']:
         args.verbose = config['general']['debug']
      else:
         args.verbose = False
  
   #print( json.dumps(config, sort_keys=True, indent=4) )

#************
   if args.dashboard_name is not None:
      config['general']['dashboard_name'] = args.dashboard_name

   if args.action == 'exporter' and ( not 'dashboard_name' in config['general'] or config['general']['dashboard_name'] is None) :
      print("ERROR: no dashboard has been specified.")
      sys.exit(2)

#************
   config['check_folder'] = False
   if args.grafana_folder is not None:
      config['general']['grafana_folder'] = args.grafana_folder
      config['check_folder'] = True

#************
   if 'export_suffix' not in config['general'] or config['general']['export_suffix'] is None:
      config['general']['export_suffix'] = "_%Y%m%d%H%M%S"

#************
   grafana_api = GrafanaFace(
	auth=config['grafana']['token']
	, host=config['grafana']['host']
	, protocol=config['grafana']['protocol']
	, port=config['grafana']['port']
	, verify=config['grafana']['verify_ssl']
   )
   try:
      res = grafana_api.health.check()
      if res['database'] != 'ok':
         print("grafana health_check is not KO.")
         sys.exit(2)
      elif args.verbose:
         print("grafana health_check is OK.")
   except e:
      print("error: {} - message: {}".format(status_code, e.message) )
      sys.exit(2)

   if args.action == 'import':
      if args.dashboard_file is None:
         print('no file to import provided!')
         sys.exit(2)
      import_path = ''
      import_file = args.dashboard_file
      if not re.search(r'^(?:(?:/)|(?:\.?\./))', import_file):
         import_path = base_path + '/'
         if 'imports_path' in config['general']:
            import_path += config['general']['imports_path'] + '/'
      import_path += import_file
      try:
         input = open(import_path, 'r')
      except OSError as e:
         print('File {0} error: {1}.'.format(import_path, e.strerror))
         sys.exit(2)

      data = input.read()
      input.close()

      try:
         dash = json.loads(data)
      except json.JSONDecodeError as e:
         print("error reading '{0}': {1}".format(import_path, e))
         sys.exit(2)

      #** check dashboard existence
      #** dash from file has no meta data (folder infos)
      new_dash = { 'dashboard': dash }

      if 'uid' in dash:
         try:
            old_dash = grafana_api.dashboard.get_dashboard(dash['uid'])
         except GrafanaApi.GrafanaClientError:
            old_dash = None

         if old_dash is not None:
            new_dash['overwrite'] = True
            if not config['check_folder']:
               if 'meta' in old_dash and 'folderUrl' in old_dash['meta']:
                  config['general']['grafana_folder'] = old_dash['meta']['folderTitle']
                  new_dash['folderId'] = old_dash['meta']['folderId']
                  config['check_folder'] = False
               else:
                  config['general']['grafana_folder'] = 'General'
            if config['general']['grafana_folder'] == 'General':
               config['check_folder'] = False
         else:
            new_dash['overwrite'] = args.overwrite
            dash['version'] = 1
            if not config['check_folder']:
               config['general']['grafana_folder'] = 'General'
               config['check_folder'] = False

         #** check folder existence
         if config['check_folder']:
            res = get_folder(config, args, grafana_api, config['general']['grafana_folder'])
            if res is None:
               try:
                  res = grafana_api.folder.create_folder(config['general']['grafana_folder'])
               except Exception as e:
                  print("error: {}".format(traceback.format_exc()) )
                  sys.exit(1)

               if res:
                  if args.verbose:
                     print("folder created")
                  #** update folder
                  new_dash['folderId'] = res['id']
               else:
                 print("KO: folder creation failed.")
                 sys.exit(1)
            else:
               new_dash['folderId'] = res['id']
         elif 'folderId' not in dash:
            new_dash['folderId'] = 0 # 0 for  default 'General' pseudo folder
         new_dash['message'] = 'imported from grafana-import.'
         try:
            res = grafana_api.dashboard.update_dashboard(new_dash)
         except GrafanaApi.GrafanaClientError as e:
            print("ERROR({1}): {0} ".format(e.message,e.status_code))
            print("maybe you want to set --overwrite option.")
            sys.exit(1)

         except Exception as e:
            print("error: {}".format(traceback.format_exc()) )
            sys.exit(1)

         if res['status']:
            print("OK: dashboard {0} imported into '{1}'.".format(dash['title'], config['general']['grafana_folder']))
            sys.exit(0)
         else:
            print("KO: dashboard {0} not imported into '{1}'.".format(dash['title'], config['general']['grafana_folder']))
            sys.exit(2)
      else:
         print("error invalid dashboard file '{0}': can't find dashboard uid".format(import_path))
         sys.exit(2)
   else:   # export
     dash = get_dashboard_content(config, args, grafana_api, config['general']['dashboard_name'])
     if dash is not None:
        save_dashboard(config, args, base_path, config['general']['dashboard_name'], dash['dashboard'], 'exported')
        sys.exit(0)

# end main...
#***********************************************************************************************
#***********************************************************************************************

if __name__  == '__main__':
   main()
