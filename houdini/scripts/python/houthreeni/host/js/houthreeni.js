
class HTN_Math {
	static matrixInterpolate(m1, m2, frac) {
		var t = new THREE.Vector3(), t2 = new THREE.Vector3();
		var r = new THREE.Quaternion(), r2 = new THREE.Quaternion();
		var s = new THREE.Vector3(), s2 = new THREE.Vector3();
		m1.decompose(t, r, s);
		m2.decompose(t2, r2, s2);
		var _t = t.lerp(t2, frac);
		var _r = r.slerp(r2, frac);
		var _s = s.lerp(s2, frac);
		return new THREE.Matrix4().compose(_t, _r, _s);
	}
}

class HTN_Frame {
	positions = [];
	colors = [];
	transforms = [];

	constructor(channels, input) {
		if(channels.position) {
			input['pos'].forEach(p =>
				this.positions.push(new THREE.Vector3().fromArray(p))
		);}
		if(channels.transforms) {
			input['transforms'].forEach(m => {
				var mat = new THREE.Matrix4().fromArray(m);
				this.transforms.push(mat);
				if('position' in channels)
					this.positions.push(new THREE.Vector3().setFromMatrixPosition(mat));
			});
		}
		if(channels.color) {
			input['col'].forEach(c =>
				this.colors.push(new THREE.Color().fromArray(c))
		);}
	}
}

class HTN_Geo {
	parent = null;
	frames = [];
	animated = 0;
	rest = new THREE.Matrix4();
	name = "";
	path = "";
	mesh = null;
	material = null;
	loaded = false;

	constructor(parent, name, input) {
		this.parent = parent;
		this.name = name;
		this.path = parent.workDir + parent.name + "/" + name + ".obj";
		this.animated = input["animated"];
		if(!this.animated) {
			this.rest.fromArray(input["rest"]);
		}
		else {
			input["frames"].forEach(m =>
				this.frames.push(new THREE.Matrix4().fromArray(m)));
		}

		var loader = new THREE.OBJLoader();
		let _this = this;
		loader.load(this.path, function(obj) {
			_this.mesh = obj;
			_this.material = new THREE.MeshPhongMaterial({color: 0xCCCCCC});
			_this.mesh.material = _this.material;

			_this.mesh.matrixAutoUpdate = false;
			var m = null;
			if(_this.animated)
				m = _this.frames[0];
			else
				m = _this.rest;
			_this.mesh.applyMatrix4(m);

			_this.loaded = true;
			parent.scene.add(_this.mesh);
		});
	}

	update(frame, frac, nextFrame) {
		if(!this.animated)
			return;
		
		var df1 = this.frames[f];
		var m = df1;
		if(this.parent.subframesInterpolation) {
			var df2 = this.frames[nextFrame];
			m = HTN_Math.matrixInterpolate(df1, df2, frac);
		}
		this.mesh.matrix = m;
	}
}

class HTN_Packed {
	parent = null;
	frames = [];
	fragments = [];
	material = null;
	loaded = false;

	constructor(parent, input) {
		this.parent = parent;

		input.frames.forEach(f =>
			this.frames.push(new HTN_Frame({'transforms': 1}, f)));

		var loader = new THREE.OBJLoader();
		this.material = new THREE.MeshNormalMaterial(/*{color: 0xCCCCCC}*/);
		var path = parent.workDir + parent.name + "/packed.obj";
		let _this = this;
		let i = 0;
		loader.load(path, function(obj) {
			for(var c of obj.children) {
				var mesh = new THREE.Mesh(c.geometry, _this.material);
				mesh.matrixAutoUpdate = false;
				_this.fragments.push(mesh);

				if(++i == obj.children.length) {
					_this.fragments.forEach(f => parent.scene.add(f));
					_this.loaded = true;
				}
			}
		});
	}

	update(frame, frac, nextFrame) {
		if(!this.loaded)
			return;

		var df1 = this.frames[frame];
		var df2 = this.frames[nextFrame];

		for(var frag = 0; frag < this.fragments.length; frag++) {
			var m = df1.transforms[frag];
			if(this.parent.subframesInterpolation) {
				m = HTN_Math.matrixInterpolate(df1.transforms[frag], df2.transforms[frag], frac);
			}
			this.fragments[frag].matrix = m;
		}
	}
}

class HTN_Instances {
	parent = null;
	meshes = [];
	loaded = false;

	constructor(parent, input) {
		this.parent = parent;
		var loader = new THREE.OBJLoader();
		this.material = new THREE.MeshNormalMaterial(/*{color: 0xCCCCCC}*/);
		let _this = this;
		let count = Object.keys(input).length;
		let i = 0;
		for(let inst in input) {
			var path = parent.workDir + parent.name + "/inst_" + inst + ".obj";
			loader.load(path, function(obj) {
				input[inst].forEach((idx) => {
					var mesh = new THREE.Mesh(obj.children[0].geometry, _this.material);
					mesh.name = idx.toString() + "_" + inst;
					mesh.matrixAutoUpdate = false;
					_this.meshes[idx] = mesh;
				});

				if(++i == count) {
					_this.meshes.forEach(m => parent.scene.add(m));
					_this.loaded = true;
				}
			});
		}
	}

	update(pointIndex, dataFrame, frac, dataNextFrame) {
		if(!this.loaded)
			return;
		
		var m = dataFrame.transforms[pointIndex];
		if(this.parent.subframesInterpolation) {
			m = HTN_Math.matrixInterpolate(m, dataNextFrame.transforms[pointIndex], frac);
		}
		this.meshes[pointIndex].matrix = m;
	}
}
class HTN_Instances_GPU {
	instancedMeshes = [];
	indicesTable = [];

	constructor(parent, input) {
		var loader = new THREE.OBJLoader();
		this.material = new THREE.MeshBasicMaterial({color: 0xCCCCCC});
		let _this = this;
		for(let inst in input) {
			var path = parent.workDir + parent.name + "/inst_" + inst + ".obj";
			loader.load(path, function(obj) {
				var count = input[inst].length;
				var buffer = new THREE.InstancedBufferGeometry(obj);
				var im = new THREE.InstancedMesh(buffer, _this.material, count);
				_this.instancedMeshes.push(im);
				input[inst].forEach((idx) => _this.indicesTable[idx] = inst);

				parent.scene.add(im);
			});
		}
	}
}

class HTN_PointCloud {
	parent = null;
	frames = [];
	channels = {};
	count = 0;
	particles = null;
	material = null;
	particleSystem = null;
	instances = null;

	constructor(parent, input, instInput=null) {
		this.parent = parent;
		this.channels = input.channels;
		this.count = this.channels.count;
		delete this.channels['count'];

		input.frames.forEach(f =>
			this.frames.push(new HTN_Frame(this.channels, f)));
			
		this.particles = new THREE.Geometry();
		this.particles.dynamic = true;
		this.material = new THREE.PointsMaterial({
			vertexColors: THREE.VertexColors,
			size: 0.02
		});
		this.particleSystem = new THREE.Points(this.particles, this.material);
		
		for(var i = 0; i < this.count; i++) {
			this.particles.vertices.push(new THREE.Vector3());
			this.particles.colors.push(new THREE.Color());
		}

		this.parent.scene.add(this.particleSystem);

		if(instInput != null) {
			this.instances = new HTN_Instances(this.parent, instInput);
		}
	}

	update(frame, frac, nextFrame) {
		var df1 = this.frames[frame];
		var df2 = this.frames[nextFrame];

		for(var pt = 0; pt < this.count; pt++) {
			// pos
			var p = new THREE.Vector3().copy(df1.positions[pt]);
			if(this.parent.subframesInterpolation) {
				p.lerp(df2.positions[pt], frac);
			}
			this.particles.vertices[pt] = p;
			// col
			if(this.channels["color"]) {
				var c = new THREE.Color().copy(df1.colors[pt]);
				if(this.parent.subframesInterpolation) {
					c.lerp(df2.colors[pt], frac);
				}
				this.particles.colors[pt] = c;
			}

			// instances
			if(this.instances != null) {
				this.instances.update(pt, df1, frac, df2);
			}
		}
		this.particles.verticesNeedUpdate = true;
		if(this.channels["color"])
			this.particles.colorsNeedUpdate = true;
	}
}

class HTN_Data {
	pointcloud = null;
	geos = [];
	packed = null;
	instances = null;
	
	name = "";
	workDir = "";
	frameCount = 0;

	loaded = false;
	loop = true;
	framesPerSecond = 30;
	subframesInterpolation = true;

	fframe = 0.0;
	playing = true;
	scene = null;
	
	constructor(scene, dir, json_file, callback) {
		this.scene = scene;
		this.workDir = dir;		
		if(!this.workDir.endsWith("/"))
			this.workDir += "/";
		let _this = this;
		$.getJSON(_this.workDir + json_file, function(result) {
			console.log("file opened");
			_this.name = result.header.name;
			_this.frameCount = result.header.frames;

			if('bb_min' in result.header && 'bb_max' in result.header) {
				var bb_min = new THREE.Vector3().fromArray(result.header['bb_min']);
				var bb_max = new THREE.Vector3().fromArray(result.header['bb_max']);
				_this.bbox = new THREE.Box3(bb_min, bb_max);
			}

			if(result.header.pointcloud) {
				var inst = null;
				if(result.header.instances)
					inst = result.instances;
				_this.pointcloud = new HTN_PointCloud(_this, result.pointcloud, inst);
			}

			if (result.header.geos > 0) {
				for(var g in result.geos) {
					_this.geos.push(new HTN_Geo(_this, g, result.geos[g]));
				}
			}

			if(result.header.packed) {
				_this.packed = new HTN_Packed(_this, result.packed);
			}
		
			_this.clock = new THREE.Clock();

			callback.call(this);
			_this.loaded = true;
		});
	}
	
	removeFromScene() {
		if(this.pointcloud != null) {
			this.scene.remove(this.pointcloud.particleSystem);
			if(this.pointcloud.instances != null) {
				if(this.pointcloud.instances.loaded) {
					this.pointcloud.instances.meshes.forEach(m =>
						this.scene.remove(m));
				}
			}
		}
		for(var i = 0; i < this.geos.length; i++) {
			if(this.geos[i].loaded && this.geos[i].mesh != null) {
				this.scene.remove(this.geos[i].mesh);
			}
		}
		if(this.packed) {
			
		}
	}

	update() {
		if(!this.loaded)
			return;
		
		var delta = this.clock.getDelta();
		if(this.playing) {
			this.fframe += delta * this.framesPerSecond;
		}	
		if(this.fframe >= this.frameCount) {
			if(this.loop) {
				this.fframe = 0.0;
			}
			else {
				this.fframe = this.frameCount - 1;
			}
		}
		var f = Math.floor(this.fframe);
		var frac = this.fframe - f;
		var nfIdx = Math.min(f+1,  this.frameCount-1);
		
		// pointcloud + instances
		if(this.pointcloud != null) {
			this.pointcloud.update(f, frac, nfIdx);
		}

		// pack
		if(this.packed != null) {
			this.packed.update(f, frac, nfIdx);
		}
		
		// geos
		for(var g of this.geos) {
			g.update(f, frac, nfIdx);
		}
	}
}