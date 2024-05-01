from collections import OrderedDict
import os, shutil
import hou

from classes import Exporter
import server, session


# export entry point
def export(node):
    # check for errors
    errors_node = node.node("ERRORS")
    errors_node.cook(True)
    if errors_node.geometry().findGlobalAttrib("err"):
        hou.ui.displayMessage("Fix the reported errors before exporting")
        return

    out_path = node.evalParm("path")
    exp_pack = node.evalParm("packed")
    exp_xform = node.evalParm("xform")
    exp_inst = node.evalParm("instance")
    exp_sprite = node.evalParm("sprite")
    mode = node.evalParm("mode")
    start_frame = node.evalParm("rangex")
    use_xform = exp_xform and exp_inst

    session.Current = Exporter(
        name = os.path.splitext(os.path.basename(out_path))[0],
        pointcloud = 0 if mode == 0 else 1,
        packed = exp_pack,
        instances = exp_inst,
        geos = node.evalParm("geos"),
        fp_acc = node.evalParm("dec_acc"),
        frames = node.evalParm("rangey") - start_frame + 1)

    # force HDA to recook
    node.setHardLocked(True)
    node.setHardLocked(False)

    # clear data
    _d = session.get_data_dir(node)
    if os.path.exists(_d):
        session.clear_dir(_d)
    
    # pointcloud export
    in_geo = node.node("IN").geometry()
    if mode > 0:        
        session.Current.pointcloud['channels'] = {
            'count': len(in_geo.iterPoints()),
            'mode': ["none","fix","dynamic"][mode],
            'position': not use_xform,
            'transforms': use_xform,
            'color': node.evalParm("col"),
            'sprite': {'path': node.evalParm("sprite_path"), 'scale': node.evalParm("sprite_scale")}
                if exp_sprite else None
        }
    if mode > 0 or exp_pack:
        frames_node = node.node("ALL_FRAMES")
        # network trigger : evaluate all frames
        frames_node.cook(True)
        bbox = frames_node.geometry().boundingBox()
        if mode > 0:
            session.Current.meta['bb_min'] = list(bbox.minvec())
            session.Current.meta['bb_max'] = list(bbox.maxvec())
        if mode == 2:
            max_count = max([f.get_count() for f in session.Current.pointcloud.frames])
            session.Current.pointcloud['channels']['count'] = max_count

    # packed
    if exp_pack:
        # network trigger : save packed fragments
        packed_node = node.node("ALL_PACKED")
        packed_node.cook(True)
    
    # geos
    geos = node.evalParm("geos")
    if geos:
        # network trigger : save all geos
        geo_node = node.node("ALL_GEO")
        geo_node.cook(True)

        _geo_nodes = OrderedDict()
        for g in range(1, geos+1):
            n = node.parm("geo" + str(g)).evalAsNode()
            a = node.evalParm("animated"+str(g))
            session.Current.geos.values()[g-1]["animated"] = a
            _geo_nodes[n] = a
        
        for f in range(start_frame, node.evalParm("rangey")+1):
            for i,g in enumerate(_geo_nodes):
                if not _geo_nodes[g]:
                    if f == start_frame:
                        t = hou.frameToTime(start_frame)
                        m = g.worldTransformAtTime(t).asTuple()
                        session.Current.geos.values()[i]["rest"] = m
                else:
                    t = hou.frameToTime(f)
                    m = g.worldTransformAtTime(t).asTuple()
                    session.Current.geos.values()[i]["frames"].append(m)
        
    print("")
    if session.Current.pointcloud:
        print(str(len(session.Current.pointcloud['frames'])) + " point cloud  frames saved")
    if session.Current.packed:
        print(str(len(session.Current.packed['frames'])) + " packed transforms frames saved")
        print(str(len(session.Current.packed['fragments'])) + " packed fragments saved")
    print(str(geos) + " geos saved")
    print(str(len(session.Current.instances.keys())) + " instance meshes saved")

    session.Current.dump(out_path)
    #session.Current = None

    # server copy
    if node.evalParm("copy_server"):
        cpy = True
        if node.evalParm("only_run"):
            if not server.is_server_running():
                cpy = False
        if cpy:
            server.copy_to_server(node)