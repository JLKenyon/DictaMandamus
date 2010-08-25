#!/usr/bin/env python

import yaml
import sys
import glob
import os
import argparse

from pprint import pprint

class in_directory:
    def __init__(self, new_directory):
        self.new_dir = new_directory
        self.old_dir = os.getcwd()
    def __enter__(self):
        os.chdir(self.new_dir)
    def __exit__(self, type, value, traceback):
        os.chdir(self.old_dir)

class Application:
    def main(self):
        parser = argparse.ArgumentParser(description="")
        parser.add_argument('-q',  dest='quiet',   action='store_const', const=True, default=False)
        parser.add_argument('-n',  dest='dry_run', action='store_const', const=True, default=False)
        parser.add_argument('config_files', type=str,  nargs='+')
        self.opts = parser.parse_args()
        for full_name in self.opts.config_files:
            self.process_file(full_name)
    
    def process_file(self, full_name):
        dname = os.path.dirname(full_name)
        fname = os.path.basename(full_name)
        
        if not os.path.isfile(full_name):
            print "Invalid file given: %(full_name)s"%locals()
        else:
            with in_directory(dname):
                with file(fname) as fin:
                    self.process_config(fin)
    
    def process_config(self, fin):
        file_map = dict()
        config = yaml.load(fin)
        for dest, source_text in config.iteritems():
            #if not os.path.isdir(dest):
            #    print "Error, Destination must be a directory"
            #    print os.getcwd(),dest
            if len(glob.glob(dest)) == 1:
                print "Destination must be unique, may not use wild-cards in destination"
            else:
                source_paths = glob.glob(source_text)
                for source in source_paths:
                    self.build_file_map(dest, source)
                    #file_map.update(self.build_file_map(dest, source))
        pass # apply file_map?


    def build_file_map(self, dest, source):
        ret = dict()
        files_list = self.findFiles(source)
        pprint(files_list)
        pass
    
    def findFiles(self, root):
        vals = {}
        def collector(arg, dirname, fnames):
            for f in fnames:
                full_name = dirname + os.path.sep + f
                if os.path.isfile(full_name) or os.path.islink(full_name):
                    arg[full_name[len(dirname):]] = full_name # !!!
        os.path.walk(root, collector, vals)
        return vals

    def perform_action(self, command):
        if not self.opts.quiet:
            print command
        if not self.opts.dry_run:
            os.system(command)
            
if __name__ == '__main__':
    app = Application()
    app.main()

##!/usr/bin/env python
#
### ------------- CODE -------------
#
#import os
#import sys
#
#def findFiles(root):
#    vals = {}
#    def collector(arg,dirname,fnames):
#        for f in fnames:
#            fullname = dirname+'/'+f
#            if os.path.isfile(fullname) or os.path.islink(fullname):
#                arg[fullname[1+len(root):]] = fullname
#    os.path.walk(root,collector,vals)
#    return vals
#
#def do(s):
#    if '-q' not in sys.argv:
#        print(s)
#    if '-n' not in sys.argv:
#        os.system(s)
#
#def main():
#    config = dict()
#    config_file = sys.argv[-1]
#    assert(os.path.isfile(config_file))
#    execfile(config_file, config)
#    directories = config['directories']
#
#    di = dict()
#    map(di.update,[findFiles(d) for d in directories.strip().split()[::-1]])
#
#    defunct_links = filter(lambda a : not os.path.exists(a),findFiles('.'))
#    for dl in defunct_links:
#        do("rm %s         # Removing defunct link"%(dl))
#
#    for relpath in set([os.path.dirname(x) for x in di.iterkeys()]):
#        if relpath != '':
#            if not os.path.isdir(relpath):
#                do("mkdir -p %s   # Making missing directory"%(relpath))
#    
#    for destination,real in di.iteritems():
#        if not os.path.realpath(destination) == os.path.realpath(real):
#            if os.path.islink(destination):
#                do('rm %s         # Removing old link...' % destination)
#            do('ln -sf %s %s  # ... Generating new link'%(real,destination))
#
#if __name__=='__main__':
#    main()
#
