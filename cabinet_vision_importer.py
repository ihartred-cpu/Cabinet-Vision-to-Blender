# ============================================================
#  Cabinet Vision DAE Importer for Blender 4.0+ / 5.x
#  File > Import > Cabinet Vision (.dae)
#
#  Diagnostic output: Window > Toggle System Console (Windows)
# ============================================================

bl_info = {
    "name": "Cabinet Vision DAE Importer",
    "author": "Custom",
    "version": (1, 3, 0),
    "blender": (4, 0, 0),
    "location": "File > Import > Cabinet Vision (.dae)",
    "description": "Import Cabinet Vision Collada exports with correct geometry, materials, UVs and hierarchy",
    "category": "Import-Export",
}

import bpy, os, math, mathutils, xml.etree.ElementTree as ET
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator

VERBOSE = True

def _log(*args):
    if VERBOSE:
        print("[CV-DAE]", *args)

def _strip(url):
    return url.strip().lstrip("#") if url else ""

def _cv_part_name(raw):
    """Extract CV part-type code from a library_node name like 'N_TO-Sh3cc841e0_...'."""
    if raw.startswith("N_") and "-" in raw:
        return raw[2:raw.index("-")]
    return raw

# ──────────────────────────────────────────────────────────────
#  Parser
# ──────────────────────────────────────────────────────────────

class DAEParser:
    def __init__(self, filepath):
        self.filepath  = filepath
        self.directory = os.path.dirname(os.path.abspath(filepath))
        self.up_axis    = "Y_UP"
        self.unit_meter = 1.0
        self.images    = {}
        self.effects   = {}
        self.materials = {}
        self.geometries= {}
        self.lib_nodes  = {}   # id -> raw element (from library_nodes)
        self.scene_nodes = []
        tree = ET.parse(filepath)
        self._root = tree.getroot()
        tag = self._root.tag
        self._ns = tag[1:tag.index("}")] if tag.startswith("{") else ""

    def _t(self, n):
        return "{%s}%s" % (self._ns, n) if self._ns else n

    def _find(self, el, *path):
        for n in path:
            if el is None: return None
            el = el.find(self._t(n))
        return el

    def _all(self, el, n):
        return el.findall(self._t(n)) if el is not None else []

    def parse(self):
        self._asset()
        self._images()
        self._effects()
        self._materials()
        self._geometries()
        self._parse_library_nodes()
        self._scene()
        _log("up=%s unit=%s images=%d effects=%d mats=%d geoms=%d nodes=%d" % (
            self.up_axis, self.unit_meter,
            len(self.images), len(self.effects),
            len(self.materials), len(self.geometries),
            len(self.scene_nodes)))

    def _asset(self):
        a = self._find(self._root, "asset")
        if a is None: return
        u = self._find(a, "up_axis")
        if u is not None and u.text: self.up_axis = u.text.strip().upper()
        un = self._find(a, "unit")
        if un is not None:
            try: self.unit_meter = float(un.get("meter", "1.0"))
            except ValueError: pass

    def _resolve(self, raw):
        p = raw.strip()
        for pfx in ("file:///", "file://"):
            if p.lower().startswith(pfx):
                p = p[len(pfx):]
                break
        p = p.replace("%20", " ").replace("%5C", "\\").replace("/", os.sep)
        if not os.path.isabs(p):
            p = os.path.join(self.directory, p)
        return os.path.normpath(p)

    def _images(self):
        lib = self._find(self._root, "library_images")
        for img in self._all(lib, "image"):
            iid = img.get("id", "")
            init = self._find(img, "init_from")
            if init is not None and init.text:
                self.images[iid] = self._resolve(init.text)

    def _effects(self):
        lib = self._find(self._root, "library_effects")
        for eff in self._all(lib, "effect"):
            self.effects[eff.get("id", "")] = self._one_effect(eff)

    def _one_effect(self, eff_el):
        d = {"color":(0.8,0.8,0.8,1.0), "texture_path":None, "roughness":0.5, "metallic":0.0, "emission":(0,0,0)}
        prof = self._find(eff_el, "profile_COMMON")
        if prof is None: return d
        surf_map = {}
        samp_map = {}
        for np in self._all(prof, "newparam"):
            sid = np.get("sid", "")
            sf = self._find(np, "surface")
            if sf is not None:
                i = self._find(sf, "init_from")
                if i is not None and i.text: surf_map[sid] = i.text.strip()
            sm = self._find(np, "sampler2D")
            if sm is not None:
                s = self._find(sm, "source")
                if s is not None and s.text: samp_map[sid] = s.text.strip()
        def rtex(ref):
            s = samp_map.get(ref, ref)
            i = surf_map.get(s, s)
            return self.images.get(i) or self.images.get(ref)
        tech = self._find(prof, "technique")
        if tech is None: return d
        shader = None
        for st in ("phong","lambert","blinn","constant"):
            shader = self._find(tech, st)
            if shader is not None: break
        if shader is None: return d
        diff = self._find(shader, "diffuse")
        if diff is not None:
            ce = self._find(diff, "color")
            te = self._find(diff, "texture")
            if ce is not None and ce.text:
                v = list(map(float, ce.text.split()))
                d["color"] = tuple(v[:4]) if len(v)>=4 else (*v[:3], 1.0)
            elif te is not None:
                p = rtex(te.get("texture",""))
                if p: d["texture_path"] = p
        se = self._find(shader, "shininess")
        if se is not None:
            fe = self._find(se, "float")
            if fe is not None and fe.text:
                try: d["roughness"] = max(0.0, min(1.0, 1.0 - float(fe.text)/128.0))
                except ValueError: pass
        return d

    def _materials(self):
        lib = self._find(self._root, "library_materials")
        for mat in self._all(lib, "material"):
            mid  = mat.get("id","")
            name = mat.get("name", mid)
            inst = self._find(mat, "instance_effect")
            if inst is not None:
                eid = _strip(inst.get("url",""))
                self.materials[mid] = {"name":name, **self.effects.get(eid,{})}
            else:
                self.materials[mid] = {"name":name,"color":(0.8,0.8,0.8,1.0),"texture_path":None,"roughness":0.5,"metallic":0.0}

    def _float_source(self, src_el):
        fa = self._find(src_el, "float_array")
        if fa is None or not fa.text: return []
        vals = list(map(float, fa.text.split()))
        stride = 1
        tc = self._find(src_el, "technique_common")
        if tc is not None:
            acc = self._find(tc, "accessor")
            if acc is not None:
                try: stride = max(1, int(acc.get("stride","1")))
                except ValueError: pass
        return [tuple(vals[i:i+stride]) for i in range(0, len(vals), stride)]

    def _geometries(self):
        lib = self._find(self._root, "library_geometries")
        for geom in self._all(lib, "geometry"):
            gid   = geom.get("id","")
            gname = geom.get("name", gid)
            mesh  = self._find(geom, "mesh")
            if mesh is None: continue

            sources = {}
            for src in self._all(mesh, "source"):
                sid  = src.get("id","").strip()
                data = self._float_source(src)
                if data: sources[sid] = data

            verts_el = self._find(mesh, "vertices")
            verts_id = verts_el.get("id","").strip() if verts_el is not None else ""
            pos_sid  = None
            if verts_el is not None:
                for inp in self._all(verts_el, "input"):
                    if inp.get("semantic") == "POSITION":
                        pos_sid = _strip(inp.get("source",""))
                        break

            prims = []
            for pt in ("polylist","triangles","polygons"):
                for p in self._all(mesh, pt):
                    prims.append((pt, p))

            self.geometries[gid] = {
                "name":gname, "sources":sources,
                "verts_id":verts_id, "pos_sid":pos_sid, "prims":prims
            }
            _log("  geom '%s': pos_sid=%r  sources=%s  prims=%s" % (
                gname, pos_sid, list(sources.keys()), [p for p,_ in prims]))

    def _node_matrix(self, node_el):
        m = mathutils.Matrix.Identity(4)
        for ch in node_el:
            tag = ch.tag.split("}")[-1] if "}" in ch.tag else ch.tag
            if not ch.text or not ch.text.strip(): continue
            try:
                if tag == "matrix":
                    v = list(map(float, ch.text.split()))
                    if len(v) == 16:
                        m = m @ mathutils.Matrix([v[0:4],v[4:8],v[8:12],v[12:16]])
                elif tag == "translate":
                    x,y,z = map(float, ch.text.split())
                    m = m @ mathutils.Matrix.Translation((x,y,z))
                elif tag == "rotate":
                    ax,ay,az,ang = map(float, ch.text.split())
                    axis = mathutils.Vector((ax,ay,az))
                    if axis.length > 1e-8:
                        m = m @ mathutils.Matrix.Rotation(math.radians(ang), 4, axis.normalized())
                elif tag == "scale":
                    sx,sy,sz = map(float, ch.text.split())
                    m = m @ mathutils.Matrix.Diagonal((sx,sy,sz,1.0)).to_4x4()
            except (ValueError, ZeroDivisionError): continue
        return m

    def _parse_library_nodes(self):
        """Index all <node> elements inside <library_nodes> by their id."""
        lib = self._find(self._root, "library_nodes")
        for node in self._all(lib, "node"):
            nid = node.get("id", "").strip()
            if nid:
                self.lib_nodes[nid] = node
        _log("library_nodes indexed: %d" % len(self.lib_nodes))

    def _parse_node(self, node_el):
        nid   = node_el.get("id","")
        name  = _cv_part_name(node_el.get("name", nid) or nid or "Node")
        mat   = self._node_matrix(node_el)
        ginst = []
        for ig in self._all(node_el, "instance_geometry"):
            gid = _strip(ig.get("url",""))
            mm  = {}
            bm = self._find(ig, "bind_material")
            if bm is not None:
                tc = self._find(bm, "technique_common")
                for im in self._all(tc, "instance_material"):
                    mm[im.get("symbol","")] = _strip(im.get("target",""))
            ginst.append({"gid":gid, "mmap":mm})
        children = [self._parse_node(c) for c in self._all(node_el, "node")]
        # Cabinet Vision stores geometry in <library_nodes> and references it
        # from visual scene nodes via <instance_node>.  Resolve those here.
        for inst in self._all(node_el, "instance_node"):
            ref_id = _strip(inst.get("url", ""))
            lib_node_el = self.lib_nodes.get(ref_id)
            if lib_node_el is not None:
                children.append(self._parse_node(lib_node_el))
            else:
                _log("WARNING: instance_node %r not in library_nodes" % ref_id)
        return {"name":name, "mat":mat, "ginst":ginst, "children":children}

    def _scene(self):
        sc = self._find(self._root, "scene")
        if sc is None: return
        ivs = self._find(sc, "instance_visual_scene")
        if ivs is None: return
        sid = _strip(ivs.get("url",""))
        lib = self._find(self._root, "library_visual_scenes")
        for vs in self._all(lib, "visual_scene"):
            if vs.get("id") == sid:
                self.scene_nodes = [self._parse_node(n) for n in self._all(vs, "node")]
                break

# ──────────────────────────────────────────────────────────────
#  Builder
# ──────────────────────────────────────────────────────────────

class BlenderBuilder:
    def __init__(self, parser, report_fn=None):
        self.p      = parser
        self.report = report_fn or (lambda m: None)
        self.bl_mats = {}

        if parser.up_axis == "Y_UP":
            self._corr = mathutils.Matrix.Rotation(math.radians(90), 4, "X")
        elif parser.up_axis == "X_UP":
            self._corr = mathutils.Matrix.Rotation(math.radians(90), 4, "Y")
        else:
            self._corr = mathutils.Matrix.Identity(4)

        self._unit = parser.unit_meter

    def build(self, context):
        name = os.path.splitext(os.path.basename(self.p.filepath))[0]
        root = bpy.data.collections.new(name)
        context.scene.collection.children.link(root)

        for mid, mdata in self.p.materials.items():
            self.bl_mats[mid] = self._make_mat(mid, mdata)

        corr = self._corr @ mathutils.Matrix.Scale(self._unit, 4)
        for node in self.p.scene_nodes:
            self._build_node(node, root, corr)

    def _find_tex(self, path):
        if os.path.exists(path): return path
        base = os.path.basename(path)
        for sub in ("","textures","Textures","images","Images","materials","Maps"):
            c = os.path.join(self.p.directory, sub, base)
            if os.path.exists(c): return c
        return None

    def _make_mat(self, mid, md):
        mat = bpy.data.materials.new(name=md.get("name", mid))
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        out  = nodes.new("ShaderNodeOutputMaterial"); out.location  = (400,0)
        bsdf = nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (0,0)
        links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        bsdf.inputs["Roughness"].default_value = md.get("roughness",0.5)
        bsdf.inputs["Metallic"].default_value  = md.get("metallic", 0.0)
        em = md.get("emission",(0,0,0))
        if any(v>0.001 for v in em):
            bsdf.inputs["Emission Color"].default_value    = (*em,1.0)
            bsdf.inputs["Emission Strength"].default_value = 1.0
        tp = md.get("texture_path")
        loaded = False
        if tp:
            ap = self._find_tex(tp)
            if ap:
                try:
                    img = bpy.data.images.load(ap, check_existing=True)
                    img.colorspace_settings.name = "sRGB"
                    uv  = nodes.new("ShaderNodeTexCoord"); uv.location  = (-600,200)
                    tex = nodes.new("ShaderNodeTexImage"); tex.location  = (-300,200)
                    tex.image = img
                    links.new(uv.outputs["UV"], tex.inputs["Vector"])
                    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
                    loaded = True
                except Exception as e:
                    _log("Texture load failed:", ap, e)
        if not loaded:
            bsdf.inputs["Base Color"].default_value = md.get("color",(0.8,0.8,0.8,1.0))
        return mat

    def _build_node(self, node, parent_col, parent_world):
        world = parent_world @ node["mat"]
        name  = node["name"]
        has_ch = bool(node["children"])
        if has_ch:
            sub = bpy.data.collections.new(name)
            parent_col.children.link(sub)
            cur = sub
        else:
            cur = parent_col

        for inst in node["ginst"]:
            gdata = self.p.geometries.get(inst["gid"])
            if gdata is None:
                _log("WARNING: geometry '%s' not found" % inst["gid"])
                continue
            obj = self._make_mesh(gdata, name, inst["mmap"], world)
            if obj:
                cur.objects.link(obj)

        for ch in node["children"]:
            self._build_node(ch, cur, world)

    def _make_mesh(self, gdata, obj_name, mmap, world):
        sources  = gdata["sources"]
        pos_sid  = gdata["pos_sid"]
        verts_id = gdata["verts_id"]
        prims    = gdata["prims"]
        t        = self.p._t

        _log("Building '%s': pos_sid=%r sources=%s prims=%s" % (
            obj_name, pos_sid, list(sources.keys()), [p for p,_ in prims]))

        # ── locate position source ──────────────────────────
        if pos_sid and pos_sid not in sources:
            _log("  pos_sid not in sources; searching primitives")
            pos_sid = None

        if pos_sid is None:
            # Try POSITION semantic directly in primitive inputs
            for _pt, pel in prims:
                for inp in pel.findall(t("input")):
                    sem = inp.get("semantic","")
                    sid = _strip(inp.get("source",""))
                    if sem == "POSITION" and sid in sources:
                        pos_sid = sid
                        _log("  Found POSITION source in primitive: %r" % pos_sid)
                        break
                if pos_sid: break

        if pos_sid is None:
            # Last resort: first stride-3 source
            for sid, data in sources.items():
                if data and len(data[0]) == 3:
                    pos_sid = sid
                    _log("  Stride-3 fallback: %r" % pos_sid)
                    break

        if not pos_sid or pos_sid not in sources:
            msg = "'%s': no position source (sources: %s)" % (obj_name, list(sources.keys()))
            _log("SKIP:", msg)
            self.report(msg)
            return None

        raw_pos = sources[pos_sid]
        if not raw_pos:
            _log("SKIP: '%s': position source empty" % obj_name)
            return None

        bverts = [tuple(world @ mathutils.Vector(p[:3])) for p in raw_pos]
        n_pos  = len(bverts)
        _log("  Positions: %d" % n_pos)

        # ── decode faces ────────────────────────────────────
        all_faces     = []
        all_uvs       = []
        all_mat_idx   = []
        sym_to_slot   = {}
        slot_to_mid   = {}
        has_uvs       = False

        for prim_type, pel in prims:
            sym = pel.get("material","")
            if sym not in sym_to_slot:
                si = len(sym_to_slot)
                sym_to_slot[sym] = si
                slot_to_mid[si]  = mmap.get(sym,"")
            si = sym_to_slot[sym]

            pos_off = 0
            uv_off  = None
            uv_src  = None
            max_off = 0
            found_pos = False

            for inp in pel.findall(t("input")):
                sem = inp.get("semantic","")
                sid = _strip(inp.get("source",""))
                try: off = int(inp.get("offset","0").strip())
                except ValueError: off = 0
                max_off = max(max_off, off)

                if sem in ("VERTEX","POSITION"):
                    pos_off   = off
                    found_pos = True
                    if sem == "POSITION" and sid and sid != pos_sid and sid in sources:
                        _log("  Overriding pos source to %r" % sid)
                        pos_sid = sid
                        bverts  = [tuple(world @ mathutils.Vector(p[:3])) for p in sources[sid]]
                        n_pos   = len(bverts)
                elif sem == "TEXCOORD" and uv_off is None and sid in sources:
                    uv_off = off
                    uv_src = sources[sid]
                    has_uvs = True

            stride = max_off + 1

            if not found_pos:
                _log("  No VERTEX/POSITION input in %s; skipping" % prim_type)
                continue

            p_el = pel.find(t("p"))
            # For "polygons" type, faces may live inside <ph> elements (not a top-level <p>),
            # so don't skip early — the polygons branch handles <ph> itself.
            if (p_el is None or not (p_el.text or "").strip()) and prim_type != "polygons":
                _log("  No <p> data in %s; skipping" % prim_type)
                continue
            raw = list(map(int, p_el.text.split())) if (p_el is not None and (p_el.text or "").strip()) else []

            # vertex counts
            if prim_type == "triangles":
                cnt    = int(pel.get("count","0"))
                vcnts  = [3] * cnt
            elif prim_type == "polylist":
                ve = pel.find(t("vcount"))
                if ve is not None and (ve.text or "").strip():
                    vcnts = list(map(int, ve.text.split()))
                else:
                    cnt = int(pel.get("count","0"))
                    if cnt and len(raw) == cnt*3*stride:
                        vcnts = [3]*cnt
                        _log("  polylist: inferred triangles")
                    else:
                        _log("  polylist: missing vcount; skipping")
                        continue
            elif prim_type == "polygons":
                sub_ps = pel.findall(t("p"))
                ph_els = pel.findall(t("ph"))
                if ph_els:
                    # Polygon-with-holes: outer contour is <ph><p>, holes are <ph><h>
                    # For rendering, use the exterior face from each <ph>; ignore holes
                    n_ph_before = len(all_faces)
                    for ph in ph_els:
                        sp = ph.find(t("p"))
                        if sp is None or not (sp.text or "").strip(): continue
                        sr = list(map(int, sp.text.split()))
                        nv = len(sr) // stride
                        f,u = self._decode(sr, nv, stride, pos_off, uv_off, uv_src, bverts)
                        if f:
                            all_faces.append(f); all_uvs.append(u); all_mat_idx.append(si)
                    _log("  polygons(<ph>): %d faces" % (len(all_faces)-n_ph_before))
                    # Also handle any direct <p> children that sit alongside <ph> elements
                    # (plain faces with no holes, e.g. the bottom face of a panel)
                    for sp in sub_ps:
                        if not (sp.text or "").strip(): continue
                        sr = list(map(int, sp.text.split()))
                        nv = len(sr) // stride
                        f,u = self._decode(sr, nv, stride, pos_off, uv_off, uv_src, bverts)
                        if f:
                            all_faces.append(f); all_uvs.append(u); all_mat_idx.append(si)
                    continue
                elif len(sub_ps) > 1:
                    for sp in sub_ps:
                        if not (sp.text or "").strip(): continue
                        sr = list(map(int, sp.text.split()))
                        nv = len(sr) // stride
                        f,u = self._decode(sr, nv, stride, pos_off, uv_off, uv_src, bverts)
                        if f:
                            all_faces.append(f); all_uvs.append(u); all_mat_idx.append(si)
                    continue
                else:
                    tv = len(raw)//stride
                    for g in (3,4):
                        if tv % g == 0:
                            vcnts = [g]*(tv//g); break
                    else:
                        vcnts = [tv]
            else:
                continue

            n_before = len(all_faces)
            cur = 0
            for vc in vcnts:
                bs = vc*stride
                sub = raw[cur:cur+bs]; cur += bs
                if len(sub) < bs: break
                f,u = self._decode(sub, vc, stride, pos_off, uv_off, uv_src, bverts)
                if f:
                    all_faces.append(f); all_uvs.append(u); all_mat_idx.append(si)
            _log("  %s: %d faces" % (prim_type, len(all_faces)-n_before))

        _log("  Total faces: %d" % len(all_faces))

        if not all_faces:
            msg = "'%s': 0 faces built" % obj_name
            _log("SKIP:", msg); self.report(msg)
            return None

        mesh = bpy.data.meshes.new(name=obj_name)
        mesh.from_pydata(bverts, [], all_faces)
        mesh.update()

        if has_uvs and any(u is not None for u in all_uvs):
            layer = mesh.uv_layers.new(name="UVMap")
            for fi, poly in enumerate(mesh.polygons):
                fuv = all_uvs[fi] if fi < len(all_uvs) else None
                for li, li_idx in enumerate(poly.loop_indices):
                    if fuv and li < len(fuv):
                        layer.data[li_idx].uv = fuv[li]
                    else:
                        layer.data[li_idx].uv = (0.0, 0.0)

        for si in sorted(slot_to_mid):
            bl_mat = self.bl_mats.get(slot_to_mid[si])
            if bl_mat is None:
                bl_mat = bpy.data.materials.new(name="CV_Unknown_%d" % si)
                bl_mat.use_nodes = True
            mesh.materials.append(bl_mat)

        for fi, poly in enumerate(mesh.polygons):
            if fi < len(all_mat_idx):
                poly.material_index = all_mat_idx[fi]

        obj = bpy.data.objects.new(name=obj_name, object_data=mesh)
        obj.matrix_world = mathutils.Matrix.Identity(4)
        return obj

    @staticmethod
    def _decode(raw, n_verts, stride, pos_off, uv_off, uv_src, bverts):
        face = []
        uvs  = [] if uv_src is not None else None
        nv   = len(bverts)
        for vi in range(n_verts):
            blk = raw[vi*stride:(vi+1)*stride]
            if len(blk) < stride: return [],None
            pi = blk[pos_off]
            if pi >= nv: pi = nv-1
            face.append(pi)
            if uv_src is not None and uv_off is not None and uv_off < len(blk):
                ui = blk[uv_off]
                uv = uv_src[ui] if ui < len(uv_src) else (0.0,0.0)
                uvs.append((uv[0], uv[1]))
        return (face,uvs) if len(face)>=3 else ([],None)

# ──────────────────────────────────────────────────────────────
#  Operator
# ──────────────────────────────────────────────────────────────

class IMPORT_OT_cabinet_vision_dae(Operator, ImportHelper):
    """Import a Cabinet Vision Collada (.dae) file"""
    bl_idname  = "import_scene.cabinet_vision_dae"
    bl_label   = "Import Cabinet Vision DAE"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".dae"
    filter_glob: StringProperty(default="*.dae", options={"HIDDEN"})
    flip_uv_v:   BoolProperty(
        name="Flip UV (V axis)",
        description="Enable if textures appear upside-down",
        default=False)

    def execute(self, context):
        _log("="*60)
        _log("Importing:", self.filepath)
        warnings = []
        try:
            p = DAEParser(self.filepath)
            p.parse()
            b = BlenderBuilder(p, report_fn=warnings.append)
            b.build(context)
            if self.flip_uv_v:
                for obj in context.scene.objects:
                    if obj.type=="MESH" and obj.data.uv_layers:
                        for ud in obj.data.uv_layers[0].data:
                            ud.uv[1] = 1.0 - ud.uv[1]
            for w in warnings:
                self.report({"WARNING"}, w)
            msg = "Cabinet Vision import: %d geometries, %d materials" % (
                len(p.geometries), len(p.materials))
            _log(msg); _log("="*60)
            self.report({"INFO"}, msg)
        except Exception as exc:
            import traceback
            self.report({"ERROR"}, "Import failed: %s" % exc)
            return {"CANCELLED"}
        return {"FINISHED"}

    def draw(self, context):
        self.layout.prop(self, "flip_uv_v")

# ──────────────────────────────────────────────────────────────
#  Register
# ──────────────────────────────────────────────────────────────

def _menu(self, context):
    self.layout.operator(IMPORT_OT_cabinet_vision_dae.bl_idname,
                         text="Cabinet Vision (.dae)")

def register():
    bpy.utils.register_class(IMPORT_OT_cabinet_vision_dae)
    bpy.types.TOPBAR_MT_file_import.append(_menu)

def unregister():
    bpy.utils.unregister_class(IMPORT_OT_cabinet_vision_dae)
    bpy.types.TOPBAR_MT_file_import.remove(_menu)

if __name__ == "__main__":
    register()
