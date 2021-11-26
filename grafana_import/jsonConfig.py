# -*- coding: utf-8 -*-
__version__ = '0.0.1'

#******************************************************************************************

import json, sys, os, re

#******************************************************************************************
class jsonConfig(object):
    """
    Class for call Centreon Web Rest webservices
    """

    #*************************************************
    def __init__(self, filepath):
        """
        Constructor with singleton for webservices
        """
        self.filepath = filepath

    #*************************************************
    def load(self, **kwargs):

        filepath = kwargs.get('filepath', None)
        if filepath is not None:
            self.filepath = filepath

        try:
            fh = open(self.filepath,'r')
        except IOError as e:
            self.err_msg = 'File {0} not present.'.format(self.filepath)
            return None

        buf = ''
        for line in fh:
            #remove line starting with // : one line comment
            if re.search(r'^\s*//', line):
                #print('find comment: {}'.format(line))
                continue
            buf += line.strip() + '\n'
            #print( buf )

        fh.close()
        #** remove multi-line C-style comments /* ... */ sequence
#        regex = re.compile(r"/\*.*\*/", re.MULTILINE + re.DOTALL)
        regex = re.compile(r"/[*][^*]*[*]+(?:[^/*][^*]*[*]+)*/", re.MULTILINE + re.DOTALL)
        buf = regex.sub('', buf)

        try:
            self.config = json.loads(buf)
        except json.JSONDecodeError as e:
            pos = e.pos
            start = 0
            if pos > 20:
                start = '...' + buf[pos - 20: pos-1]
            else:
                start = buf[0: pos-1]

            start += ' --> '
            if pos + 20  < len(buf):
                start += buf[pos:pos+20] + '...'
            else:
                start += buf[pos:len(buf)-1]

            self.err_msg = "error reading '{}': {}".format(self.filepath, e) \
		+ 'error near -->: ' + start
            self.config = None
        return self.config

