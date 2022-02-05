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


from grafana_import.constants import (PKG_NAME, PKG_VERSION, CONFIG_NAME)

import argparse, json, sys, os, re, traceback

from datetime import datetime

import grafana_client.client as GrafanaApi
import grafana_import.grafana as Grafana

import yaml

#******************************************************************************************
config = None

#******************************************************************************************
def save_dashboard(config, args, base_path, dashboard_name, dashboard, action):

   output_file = base_path

   if 'exports_path' in config['general'] and \
      not re.search(r'^(\.|\/)?/', config['general']['exports_path']):
      output_file = os.path.join(output_file, config['general']['exports_path'] )

   if 'export_suffix' in config['general']:
      dashboard_name += datetime.today().strftime(config['general']['export_suffix'])

   if 'meta' in dashboard and 'folderId' in dashboard['meta'] and dashboard['meta']['folderId'] != 0:
      dashboard_name = dashboard['meta']['folderTitle'] + '_' + dashboard_name

   file_name = Grafana.remove_accents_and_space( dashboard_name )
   output_file = os.path.join(output_file, file_name + '.json')
   try:
      output = open(output_file, 'w')
   except OSError as e:
      print('File {0} error: {1}.'.format(output_file, e.strerror))
      sys.exit(2)

   content = None
   if args.pretty:
      content = json.dumps( dashboard['dashboard'], sort_keys=True, indent=2 )
   else:
      content = json.dumps( dashboard['dashboard'] )
   output.write( content )
   output.close()
   print("OK: dashboard {1} to '{0}'.".format(output_file, action))
 
#******************************************************************************************
class myArgs:
  attrs = [ 'pattern'
                , 'base_path', 'config_file'
                , 'grafana', 'dashboard_name'
                , 'pretty', 'overwrite', 'allow_new', 'verbose'
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

   parser.add_argument('-a', '--allow_new'
			, action='store_true'
         , default=False
			, help='if a dashboard with same name exists in an another folder, allow to create a new dashboard with same name it that folder.')

   parser.add_argument('-b', '--base_path'
			, help='set base directory to find default files.')
   parser.add_argument('-c', '--config_file'
			, help='path to config files.')

   parser.add_argument('-d', '--dashboard_name'
			, help='name of dashboard to export.')

   parser.add_argument('-g', '--grafana_label'
			, help='label in the config file that represents the grafana to connect to.'
         , default='default')

   parser.add_argument('-f', '--grafana_folder'
			, help='the folder name where to import into Grafana.')

   parser.add_argument('-i', '--dashboard_file'
			, help='path to the dashboard file to import into Grafana.')

   parser.add_argument('-o', '--overwrite'
			, action='store_true'
         , default=False
			, help='if a dashboard with same name exists in same folder, overwrite it with this new one.')

   parser.add_argument('-p', '--pretty'
			, action='store_true'
			, help='use JSON indentation when exporting or extraction of dashboards.')

   parser.add_argument('-v', '--verbose'
			, action='store_true'
			, help='verbose mode; display log message to stdout.')

   parser.add_argument('-V', '--version'
			, action='version', version='{0} {1}'.format(PKG_NAME, PKG_VERSION)
			, help='display program version and exit..')

   parser.add_argument('action', metavar='ACTION'
			, nargs='?'
			, choices=['import', 'export', 'remove']
			, default='import'
			, help='action to perform. Is one of \'export\', \'import\' (default), or \'remove\'.\n' \
            'export: lookup for dashboard name in Grafana and dump it to local file.\n' \
            'import: import a local dashboard file (previously exported) to Grafana.\n' \
            'remove: lookup for dashboard name in Grafana and remove it from Grafana server.'
            )
   inArgs = myArgs()
   args = parser.parse_args(namespace=inArgs)

   base_path = '.'
#   base_path = os.path.dirname(os.path.abspath(__file__))
   if args.base_path is not None:
      base_path = inArgs.base_path

   config_file = os.path.join(base_path, CONFIG_NAME)
   if args.config_file is not None:
      if not re.search(r'^(\.|\/)?/', config_file):
         config_file = os.path.join(base_path,args.config_file)
      else:
         config_file = args.config_file

   config = None
   try:
      with open(config_file, 'r') as cfg_fh:
         try:
            config = yaml.safe_load(cfg_fh)
         except yaml.scanner.ScannerError as exc:
            mark = exc.problem_mark
            print("Yaml file parsing unsuccessul : %s - line: %s column: %s => %s" % (config_file, mark.line+1, mark.column+1, exc.problem) )
   except Exception as exp:
      print('ERROR: config file not read: %s' % str(exp))

   if config is None:
      sys.exit(1)

   if args.verbose is None:
      if 'debug' in config['general']:
         args.verbose = config['general']['debug']
      else:
         args.verbose = False

   if args.allow_new is None:
      args.allow_new = False

   if args.overwrite is None:
      args.overwrite = False
  
   if args.pretty is None:
      args.pretty = False

   #print( json.dumps(config, sort_keys=True, indent=4) )

#************
   if args.dashboard_name is not None:
      config['general']['dashboard_name'] = args.dashboard_name

   if args.action == 'exporter' and ( not 'dashboard_name' in config['general'] or config['general']['dashboard_name'] is None) :
      print("ERROR: no dashboard has been specified.")
      sys.exit(1)

#************
   config['check_folder'] = False
   if args.grafana_folder is not None:
      config['general']['grafana_folder'] = args.grafana_folder
      config['check_folder'] = True

#************
   if 'export_suffix' not in config['general'] or config['general']['export_suffix'] is None:
      config['general']['export_suffix'] = "_%Y%m%d%H%M%S"

   if not args.grafana_label in config['grafana']:
      print("ERROR: invalid grafana config label has been specified (-g {0}).".format(args.grafana_label))
      sys.exit(1)
   
   #** init default conf from grafana with set label.
   config['grafana'] = config['grafana'][args.grafana_label]

#************
   if not 'token' in config['grafana']:
      print("ERROR: no token has been specified in grafana config label '{0}'.".format(args.grafana_label))
      sys.exit(1)

   params = {
      'host': config['grafana'].get('host', 'localhost'),
      'protocol': config['grafana'].get('protocol', 'http'),
      'port': config['grafana'].get('port', '3000'),
      'token': config['grafana'].get('token'),
      'verify_ssl': config['grafana'].get('verify_ssl', True),
      'search_api_limit': config['grafana'].get('search_api_limit', 5000),
      'folder': config['general'].get('grafana_folder', 'General'),
      'overwrite': args.overwrite,
      'allow_new': args.allow_new,
   }

   try:
      grafana_api = Grafana.Grafana( **params )
   except Exception as e:
      print("ERROR: {} - message: {}".format(e) )
      sys.exit(1)

   #*******************************************************************************
   if args.action == 'import':
      if args.dashboard_file is None:
         print('ERROR: no file to import provided!')
         sys.exit(1)
      import_path = ''
      import_file = args.dashboard_file
      if not re.search(r'^(?:(?:/)|(?:\.?\./))', import_file):
         import_path = base_path
         if 'imports_path' in config['general']:
            import_path = os.path.join(import_path, config['general']['imports_path'] )
      import_path = os.path.join(import_path, import_file)

      try:
         input = open(import_path, 'r')
      except OSError as e:
         print('ERROR: File {0} error: {1}.'.format(import_path, e.strerror))
         sys.exit(1)

      data = input.read()
      input.close()

      try:
         dash = json.loads(data)
      except json.JSONDecodeError as e:
         print("ERROR: reading '{0}': {1}".format(import_path, e))
         sys.exit(1)

      try:
         res = grafana_api.import_dashboard( dash )
      except GrafanaApi.GrafanaClientError as exp:
         print('ERROR: {0}.'.format(exp))
         print("maybe you want to set --overwrite option.")
         sys.exit(1)

      if res:
         print("OK: dashboard '{0}' imported into '{1}'.".format(dash['title'], grafana_api.grafana_folder))
         sys.exit(0)
      else:
         print("KO: dashboard '{0}' not imported into '{1}'.".format(dash['title'], grafana_api.grafana_folder))
         sys.exit(1)

   #*******************************************************************************
   elif args.action == 'remove':
      try:
         res = grafana_api.remove_dashboard(config['general']['dashboard_name'])
         print("OK: dashboard '{0}' removed.".format(config['general']['dashboard_name']))
      except Grafana.GrafanaDashboardNotFoundError as exp:
         print("KO: dashboard '{0}' not found in '{1}".format(exp.dashboard, exp.folder))
         sys.exit(0)
      except Grafana.GrafanaFolderNotFoundError as exp:
         print("KO: folder '{0}' not found".format(exp.folder))
         sys.exit(0)
      except GrafanaApi.GrafanaBadInputError as exp:
         print("KO: dashboard '{0}' not removed: {1}".format(config['general']['dashboard_name'], exp))
         sys.exit(1)
      except Exception as exp:
         print("error: dashboard '{0}' remove exception '{1}'".format(config['general']['dashboard_name'], traceback.format_exc()))
         sys.exit(1)

   #*******************************************************************************
   else:   # export or
      try:
         dash = grafana_api.export_dashboard(config['general']['dashboard_name'])
      except Grafana.GrafanaNotFoundError:
         print("KO: dashboard name not found '{0}'".format(config['general']['dashboard_name']))
         sys.exit(1)
      except Exception as exp:
         print("error: dashboard '{0}' export exception '{1}'".format(config['general']['dashboard_name'], traceback.format_exc()))
         sys.exit(1)

      if dash is not None:
         save_dashboard(config, args, base_path, config['general']['dashboard_name'], dash, 'exported')
         sys.exit(0)

# end main...
#***********************************************************************************************

if __name__  == '__main__':
   main()

#***********************************************************************************************
# over
