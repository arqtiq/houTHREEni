from __future__ import print_function
import hou
import os

from classes import Frame
import session
    

def sop_pre_save_register_instances(node):
    if not session.is_exporting():
        return
    geo = node.geometry()
    ref_geo = node.inputs()[1].geometry()
    inst = ref_geo.attribValue("instance")
    session.Current.instances[inst] = [p.attribValue("index") for p in ref_geo.iterPoints()]

    save_path = os.path.join(session.get_data_dir(node.parent()), "inst_"+inst+".obj")
    geo.addAttrib(hou.attribType.Global, "path", "", False, False)
    geo.setGlobalAttribValue("path", save_path)

def sop_write_pc_frame(geo, idx):
    if not session.is_exporting():
        return
    if not session.Current.meta["pointcloud"]:
        return
    frame = Frame(idx)
    for p in geo.iterPoints():
        session.Current.add_point(frame, p)
    session.Current.add_pc_frame(frame)

def sop_write_pack_frame(geo, idx):
    if not session.is_exporting():
        return
    if not session.Current.meta["packed"]:
        return
    packed_prims = [p for p in geo.iterPrims()
        if issubclass(type(p), hou.PackedPrim)]
    frame = Frame(idx)
    for ppr in packed_prims:   
        session.Current.add_pack(frame, ppr)
    session.Current.add_pack_frame(frame)

def sop_pre_save(node):
    if not session.is_exporting():
        return
    path = session.get_data_dir(node.parent())
    geo = node.geometry()
    geo_op = geo.attribValue("imp")

    save_path = ""
    if geo_op:
        _op = geo_op.replace("/", "_").strip('_')
        save_path = path + _op + ".obj"
        session.Current.geos[_op] = {"frames": []}

    geo.addAttrib(hou.attribType.Global, "path", "", False, False)
    geo.setGlobalAttribValue("path", save_path)

def sop_pre_save_register_pack(node):
    if not session.is_exporting():
        return
    geo = node.geometry()
    for pr in geo.iterPrims():
        p = pr.attribValue("path")
        p = p.split('/')[-1]
        session.Current.packed['fragments'].append(p)

    path = os.path.join(session.get_data_dir(node.parent()), "packed.obj")
    geo.addAttrib(hou.attribType.Global, "path", "", False, False)
    geo.setGlobalAttribValue("path", path)