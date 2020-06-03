from __future__ import print_function
import hou
import json
import os
from collections import OrderedDict


class Frame(object):
    def __init__(self, idx=-1):
        self.index = idx
        self.positions = []
        self.colors = []
        self.transforms = []

    def get_count(self):
        return max(len(self.positions), len(self.transforms))

    def to_dict(self):
        d = {}
        if self.positions:
            d["pos"] = self.positions
        if self.transforms:
            d["transforms"] = self.transforms
        if self.colors:
            d["col"] = self.colors
        return d

class Exporter(object):
    def __init__(self, **kwargs):
        self.meta = kwargs
        self.pointcloud = {}
        self.geos = OrderedDict()
        self.packed = {}
        self.instances = {}

        if self.meta["packed"]:
            self.packed = {'fragments': [], 'frames': []}
        if self.meta["pointcloud"]:
            self.pointcloud = {'channels': {}, 'frames': []}

        self.fpf = self.fp_list_format

    def add_point(self, frame, point):
        if not self.meta["pointcloud"]:
            return
        if self.pointcloud['channels']['position']:
            frame.positions.append(self.fpf(point.position()))   
        if self.pointcloud['channels']['transforms']:
            frame.transforms.append(self.fpf(point.attribValue("xform")))   
        if self.pointcloud['channels']['color']:
            frame.colors.append(self.fpf(point.attribValue("Cd")))
        
    def add_pc_frame(self, frame):
        if not self.meta["pointcloud"]:
            return
        self.pointcloud['frames'].append(frame)

    def add_pack(self, frame, pprim):
        if not self.meta["packed"]:
            return
        frame.transforms.append(self.fpf(pprim.fullTransform().asTuple()))

    def add_pack_frame(self, frame):
        if not self.meta["packed"]:
            return
        self.packed['frames'].append(frame)

    def fp_list_format(self, tuple_obj):
        return [round(p,self.meta['fp_acc']) for p in list(tuple_obj)]

    def dump(self, path):
        for g in self.geos:
            self.geos[g]["frames"] = [self.fpf(m) for m in self.geos[g]["frames"]]

        dump = { 'header': self.meta }
        if self.meta['pointcloud'] and self.pointcloud:
            self.pointcloud['frames'] = [f.to_dict() for f in self.pointcloud['frames']]
            dump['pointcloud'] = self.pointcloud
        if self.meta['packed'] and self.packed:
            self.packed['frames'] = [f.to_dict() for f in self.packed['frames']]
            dump['packed'] = self.packed
        if self.meta['geos'] and self.geos:
            dump['geos'] = self.geos
        if self.meta['instances'] and self.instances:
            dump['instances'] = self.instances

        if not path.endswith(".json"):
            path += ".json"
        with open(path, "w+") as f:
            json.dump(dump, f)