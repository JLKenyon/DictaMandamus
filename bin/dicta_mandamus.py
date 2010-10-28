#!/usr/bin/env python

import yaml
import sys
import glob
import os
import argparse
import itertools

from pprint import pprint

class in_directory:
    def __init__(self, new_directory):
        self.new_dir = new_directory
        self.old_dir = os.getcwd()
    def __enter__(self):
        try:
            os.chdir(self.new_dir)
        except: pass
    def __exit__(self, type, value, traceback):
        try:
            os.chdir(self.old_dir)
        except: pass

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
        dname = os.path.dirname (full_name)
        fname = os.path.basename(full_name)
        
        if not os.path.isfile(full_name):
            print "Invalid file given: %(full_name)s"%locals()
        else:
            with in_directory(dname):
                with file(fname) as fin:
                    self.process_config(fin)
    
    def process_config(self, fin):
        dest_source_file_map = dict()
        dest_file_map        = dict()

        ignore_files = list()

        config = yaml.load(fin)
        if config.has_key('ignore'):
            ignore_stmt = config['ignore']
            if type(ignore_stmt) is list():
                ignore_files = ignore_stmt
            else:
                ignore_files.append(ignore_stmt)
            del(config['ignore'])
        for dest, source_text in config.iteritems():
            dest_file_map.update(self.find_files(dest))
            if len(glob.glob(dest)) > 1:
                print "Destination must be unique, may not use wild-cards in destination"
            else:
                if type(source_text) is str:
                    source_paths = glob.glob(source_text)
                elif type(source_text) is list:
                    flatten = lambda x : list(itertools.chain.from_iterable(x))
                    source_paths = flatten([glob.glob(x) for x in source_text])

                for source in source_paths:
                    dest_source_file_map.update(self.build_dest_source_file_map(dest, source))

        for key in dest_source_file_map.keys():
            if key in ignore_files or os.path.basename(key) in ignore_files:
                del(dest_source_file_map[key])

        self.process_data(dest_file_map, dest_source_file_map)

    def process_data(self, dest_file_map, dest_source_file_map):
        dest_file_set   = set(dest_file_map.iterkeys())
        source_file_set = set(dest_source_file_map.iterkeys())
        
        cull_file_set    = dest_file_set - source_file_set
        missing_file_set = source_file_set - dest_file_set
        common_file_set  = dest_file_set.intersection(source_file_set)
        
        directories = set([os.path.dirname(os.path.realpath(x)) for x in missing_file_set])
        for d in directories:
            if not os.path.isdir(d):
                self.create_directory(d)
        
        for fname in cull_file_set:
            if os.path.islink(fname):
                self.remove_link(fname)
        
        for fname in missing_file_set:
            self.create_link(dest_source_file_map[fname], fname)
        
        for fname in common_file_set:
            if os.path.realpath(fname) == os.path.realpath(dest_source_file_map[fname]):
                pass
                #print "We're good!"
            else:
                self.update_link(dest_source_file_map[fname], fname)
    
    def build_dest_source_file_map(self, dest, source):
        dest   = dest.lstrip(os.path.sep)
        source = source.lstrip(os.path.sep)
        ret = dict()
        files_list = self.find_files(source).values()
        for fname in files_list:
            fname = fname.lstrip(os.path.sep)
            ret[os.path.join(dest, fname)] = os.path.join(source, fname)
        return ret
    
    def find_files(self, root):
        vals = dict()
        def collector(arg, dirname, fnames):
            for f in fnames:
                full_name = os.path.join(dirname, f)
                if os.path.isfile(full_name) or os.path.islink(full_name):
                    #arg.add(full_name[len(root):])
                    #print '$',full_name,root
                    arg[full_name] = full_name[len(root):]
        os.path.walk(root, collector, vals)
        return vals
    
    # File System action wrappers
    def create_directory(self, directory):
        directory = os.path.abspath(directory)
        self.perform_action('mkdir -p %(directory)s'%locals())

    def remove_link(self, fname):
        fname = os.path.abspath(fname)
        self.perform_action('rm %(fname)s'%locals())

    def create_link(self, source, dest):
        source = os.path.abspath(source)
        dest   = os.path.abspath(dest)
        self.perform_action('ln -sf %(source)s %(dest)s'%locals())

    def update_link(self, source, dest):
        self.remove_link(dest)
        self.create_link(source,dest)

    # Action wrapper
    def perform_action(self, command):
        if not self.opts.quiet:
            print command
        if not self.opts.dry_run:
            os.system(command)
            
if __name__ == '__main__':
    app = Application()
    app.main()

