# houTHREEni

## Presentation
### Houdini exporter &amp; JavaScript importer for THREE.js

This toolset offers an exporter for Houdini and Javascript loading scripts to be used with [THREE.js](https://threejs.org/).

Showcase : http://gratien-vernier.com/houthreeni \
More tests will appear in the top-right list as development evolves.

## Features

Can be exported and played back in browser :
- Fix count point cloud animated
- Supports PC geometry instancing
    - Built-in instancer by attribute (replace CopyToPoint SOP)
    - Automatic models export / loading
- Packed Primitives playback
    - Automatic fragments optimized export
- Object level (scene) export with transforms animations
    - Automatic export
- Runtime sub-frames interpolation
    - Allow to reduce payload size (faster client loading time !) and slow motion while keeping smooth animation playback
- HDA can hosts local HTTP server which loads a lightweight HTML / JS setup to test what your exporting in your browser in real time !

## How-To

### Install
Copy the **/houdini** folder from this repository root in your *$HOME* or *$HSITE*, according to your environment pipeline.

Or just reference your local GitHub repository in your *houdini.env* file.

```
HOUTHREENI = C:\Path\To\GitHub\houTHREEni\houdini
HOUDINI_PATH = $HOUTHREENI;&
```

### Export

Once installed, simply use the **threejs_exporter** SOP node. \
Consult the attached *examples.hip* file to learn how to use it with different setups.

### Playback

To use the JS loader, you'll need to copy these files to your web site / app from the **/houdini/scripts/python/houthreeni/host/js** folder :
- three.js \
Obviously this is THREE.js framework, copy it if you don't use it yet
- houthreeni.js \
This is the loader for the files generated from houdini
- jquery.js \
JQuery framework; used to async load JSON file

**dat.gui.js** and **OrbitControls.js** are used for the integrated player (UI and camera controls). They are not mandatory but you can get them too if you want these.

You can consult **../index.html** for an example of integration into a web page.

## Future / To-Do

Improvements Backlog :
- GPU instancing option for PC instances
- Better model loading routine (too much is still assumed)
- Match THREE.js Object3D structure for classes, improve scene management
- Rewing loop mode
- Test and adapt new SOP RBD workflow with packed prims export
- Particle sprites
- Dynamic particles count (birth & death)
- Render options
    - Impact web runtime
    - Settable from houdini HDA, patches file without full re-export
    - Set the way the scene is rendered (materials, PC visibility, ...)
- More scene objects exports (lights)
- Point cloud with primitives (lines, surfaces)