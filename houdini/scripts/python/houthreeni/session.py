from __future__ import print_function
import hou
import os, sys, shutil
from collections import OrderedDict

from classes import Exporter
import server


Current = None

def is_exporting():
    return not Current == None

def get_data_dir(node):
    path = node.evalParm("path")
    _dir = os.path.dirname(path)
    _name = os.path.splitext(os.path.basename(path))[0]
    return _dir + "/" + _name + "/"

def clear_dir(dir_path):
    for f in os.listdir(dir_path):
        os.remove(os.path.join(dir_path, f))