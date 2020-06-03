from __future__ import print_function
import hou
import os, sys, shutil
import subprocess
import webbrowser

import session


Server = None

host_tree = ["js", "hou.html", "favicon.ico"]


def start_server(node, browse):
    if is_server_running():
        print("Server already running")
        return
    global Server
    path = node.evalParm("path")
    if not os.path.exists(path):
        hou.ui.displayMessage("Data never exported yet ! Can't start server.")
    copy_to_server(node)
    # start server
    port = str(node.evalParm("port"))
    v = int(sys.version[0])
    mod = ["", "", "SimpleHTTPServer", "http.server"][v]
    os.chdir(get_host_path())
    Server = subprocess.Popen(["python", "-m", mod, port])
    print("Server started")
    if browse:
        webbrowser.open("http://localhost:" + port + "/hou.html")

def get_host_path():
    payload_path = os.path.dirname(__file__)
    payload_path = os.path.join(payload_path, "host")
    return payload_path

def is_server_running():
    if not Server:
        return False
    return Server.poll() == None

def has_data_dir(node):
    _p = ["geos","packed","instance"]
    _p = [node.evalParm(p) for p in _p]
    return any(_p)

def copy_to_server(node):
    export_path = node.evalParm("path")
    sdir = get_host_path()
    target = os.path.join(sdir, "export.json")
    shutil.copy(export_path, target)

    if has_data_dir(node):
        geo_dir = session.get_data_dir(node)
        target_dir = os.path.join(sdir, os.path.basename(os.path.dirname(geo_dir)))
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        shutil.copytree(geo_dir, target_dir)

def stop_server():
    if is_server_running():
        Server.terminate()
        print("Server Stopped")
    else:
        print("Server is not running")

def clean_host_data():
    r,dirs,files = list(os.walk(get_host_path()))[0]
    for d in dirs:
        if d in host_tree:   continue
        shutil.rmtree(os.path.join(r, d))
    for f in files:
        if f in host_tree: continue
        os.remove(os.path.join(r, f))
