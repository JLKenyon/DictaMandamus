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
        dname = os.path.dirname (full_name)
        fname = os.path.basename(full_name)
        
        if not os.path.isfile(full_name):
            print "Invalid file given: %(full_name)s"%locals()
        else:
            with in_directory(dname):
                with file(fname) as fin:
                    self.process_config(fin)
    
    def process_config(self, fin):
        dest_source_file_map   = dict()
        dest_file_list = set()
        config = yaml.load(fin)
        for dest, source_text in config.iteritems():
            dest_file_list.update(self.find_files(dest))
            if len(glob.glob(dest)) == 1:
                print "Destination must be unique, may not use wild-cards in destination"
            else:
                source_paths = glob.glob(source_text)
                for source in source_paths:
                    dest_source_file_map.update(self.build_dest_source_file_map(dest, source))
        self.process_data(dest_file_list, dest_source_file_map)

    def process_data(self, dest_file_list, dest_source_file_map):
        source_file_list = set(dest_source_file_map.iterkeys())

        cull_file_list    = dest_file_list - source_file_list
        missing_file_list = source_file_list - dest_file_list
        common_file_list  = dest_file_list.intersection(source_file_list)

        directories = set([os.path.dirname(os.path.realpath(x)) for x in missing_file_list])
        for d in directories:
            if not os.path.isdir(d):
                self.create_directory(d)

        for fname in cull_file_list:
            self.remove_link(fname)

        for fname in missing_file_list:
            self.create_link(dest_source_file_map[fname], fname)

        for fname in common_file_list:
            if os.path.realpath(fname) == os.path.realpath(dest_source_file_map[fname]):
                print "We're good!"
            else:
                self.update_link(dest_source_file_map[fname], fname)

    def build_dest_source_file_map(self, dest, source):
        dest   = dest.lstrip(os.path.sep)
        source = source.lstrip(os.path.sep)
        ret = dict()
        files_list = self.find_files(source)
        for fname in files_list:
            fname = fname.lstrip(os.path.sep)
            ret[os.path.join(dest, fname)] = os.path.join(source, fname)
        return ret
    
    def find_files(self, root):
        vals = set()
        def collector(arg, dirname, fnames):
            for f in fnames:
                full_name = os.path.join(dirname, f)
                if os.path.isfile(full_name) or os.path.islink(full_name):
                    arg.add(full_name[len(root):])
        os.path.walk(root, collector, vals)
        return list(vals)

    # File System action wrappers
    def create_directory(self, directory):
        directory = os.path.realpath(directory)
        self.perform_action('mkdir -p %(directory)s'%locals())

    def remove_link(self, fname):
        fname = os.path.realpath(fname)
        self.perform_action('rm %(fname)s'%locals())

    def create_link(self, source, dest):
        source = os.path.realpath(source)
        dest   = os.path.realpath(dest)
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

