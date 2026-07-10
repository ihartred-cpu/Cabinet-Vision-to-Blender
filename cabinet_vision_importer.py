# ============================================================
#  Cabinet Vision DAE Importer for Blender 4.0+ / 5.x
#  File > Import > Cabinet Vision (.dae)
#
#  Diagnostic output: Window > Toggle System Console (Windows)
#
#  CHANGELOG
#  1.14.0 - New opt-in "Mark Hard Edges as Seams" post-process (on by
#           default): marks every edge where the two adjacent faces meet
#           at more than ~40 degrees as a UV seam, on every mesh object
#           created by the import. Cabinet Vision panels are almost
#           entirely rectilinear, so this lands seams right where a face
#           actually turns a corner -- panel face to edgeband, panel face
#           to a merged bore's cylinder wall -- giving a later UV unwrap
#           sensible cut lines without hand-marking every part. Boundary
#           edges (only one adjacent face) are left alone. Only sets edge
#           seam flags; doesn't move geometry or touch existing UVs.
#  1.13.0 - Two collection-grouping fixes so parts consolidate the way a
#           person expects to browse them in the outliner:
#           * Assembly collections (e.g. "Tall Cabinet Assembly") are now
#             reused instead of always creating a new one. Cabinet Vision
#             stacks multiple anonymous PA_ wrapper levels for what's
#             conceptually one assembly; previously each level created
#             its own collection, fragmenting one assembly's parts across
#             "Tall Cabinet Assembly", "Tall Cabinet Assembly.001", ".002",
#             etc. Now every part belonging to that assembly -- across
#             however many stacked PA_ levels CV emitted, and regardless
#             of which of the two build paths (physical-part merge vs.
#             clean-collapse) picked it up -- lands in one shared
#             collection, so e.g. every "AS" (adjustable shelf) in an
#             assembly ends up in one "AS" collection instead of several.
#           * Bore sub-types (LFVBORE, LRVBORE, _HGCVBORE, _HGAVBORE, and
#             CV's dozens of other bore type codes) that don't get
#             absorbed into a panel now share one common "Bores"
#             collection per assembly instead of each getting its own
#             collection named after its literal sub-type code.
#  1.12.0 - Fixed mangled/mismatched UVs on panels with shelf-pin or
#           hinge bores (commonly visible on End/Top/Bottom panels): CV
#           exports each bore as its own separately-tessellated cylinder
#           with a UV parameterization that doesn't match the flat panel
#           it's drilled into. A 90-degree UV rotation to correct this
#           already existed, but it only checked the *merged mesh
#           object's* own name for a "BORE" suffix -- which worked back
#           when a bore stayed its own standalone object, but silently
#           stopped firing once 1.9.0-1.11.0 started joining bore
#           instances directly into the panel's merged mesh (named after
#           the panel, e.g. "TO"/"SL"/"BT", not the bore). The bore's raw,
#           misaligned UV then flowed straight into the panel mesh
#           untouched. Now applied per contributing instance instead of
#           per merged object, so it fires regardless of what the merged
#           object ends up named. Verified directly against a live
#           "hall out.dae" import (decoded geometry names/counts).
#  1.11.0 - 1.10.0's bore-absorption only covered bores exported as flat
#           siblings under a bare (non-PA_) grouping node. In practice
#           Cabinet Vision often wraps a bore in its own PA_+VN_ pair --
#           e.g. hinge bores ("_HGAVBORE"/"_HGCVBORE") showing up under
#           their own "Molding_Door_NN" wrapper, sibling to the door's
#           real "Door_NN" slab wrapper and to separate hinge-hardware
#           ("Widget_Arm"/"Widget_Base_Plate") wrappers, all as direct
#           children of one door assembly -- which the 1.10.0 fix didn't
#           reach at all. Extended the same "exactly one structural
#           target absorbs every bore-only sibling" logic to this PA_
#           assembly level too, additionally excluding any "Widget"-
#           labeled sibling (hinge arm/base hardware) from ever being a
#           valid absorption target. Verified directly against the
#           user's own "salvia out.dae" door structure.
#  1.10.0 - Bore operations (e.g. "_HGAVBORE" hinge-cup/screw bores) that
#           Cabinet Vision exports as flat siblings of the part they're
#           drilled into -- rather than nested inside it the way panel
#           cuts normally are -- previously stayed unmerged, floating as
#           their own separate objects instead of becoming part of the
#           door/drawer-front they belong to. Common on hardware-widget
#           groupings (hinge plates, etc.) where the door slab and its
#           bores sit as siblings alongside separate hinge hardware
#           (arm/base) sub-assemblies. When exactly one non-feature leaf
#           part exists among such a group of siblings, every bore-type
#           object in that group is now joined into it; hinge hardware
#           and any ambiguous (multiple-candidate) groupings are left
#           untouched to avoid an incorrect merge.
#  1.9.1 - "Hide Dado/Notch Feature Geometry" (1.9.0) was also catching
#          BORE-named nodes, hiding boring/drilling geometry along with
#          the dado/notch pockets. Split the keyword set so hiding only
#          ever applies to DADO/NOTCH; BORE geometry always stays merged
#          and visible, in the panel mesh, same as before 1.9.0.
#  1.9.0 - Fixed a real bug (present since 1.4.0's part-joining, not
#          something 1.8.0's rewrite introduced): BORE/DADO/NOTCH feature
#          geometry nested inside the panel it cuts into (the normal,
#          documented case -- e.g. "UBDADO", "_HGAVBORE") was being
#          silently fused into that panel's merged mesh instead of ever
#          reaching the "hide standalone feature objects" logic added in
#          1.7.0, which only ever fired for the rarer case of a feature
#          exported as an un-nestable orphan sibling. New "Hide Bore/
#          Dado/Notch Feature Geometry" checkbox (on by default) now
#          catches the nested case too, routing that geometry straight
#          to the hidden "CV Hidden Features" collection instead of
#          merging it in. Turn off if a panel's dado/notch pocket only
#          exists as geometry under one of these feature nodes and you
#          rely on "Fix Hidden Dado Faces" to expose it.
#  1.8.0 - Performance / organization rewrite. Import is much faster on
#          large files:
#          * Each geometry is decoded from XML exactly ONCE and cached,
#            instead of being fully re-parsed for every instance that
#            references it (CV instances the same panel/bore geometry
#            many times across a job).
#          * Physical parts are assembled directly into a single mesh at
#            build time, instead of creating dozens of temporary objects
#            per part and running the slow, selection-based Join
#            operator on each group. (The operator join is kept only for
#            the rarer clean-named collapse path.)
#          * UVs and material indices are written with foreach_set
#            instead of per-loop Python assignment; vertex transforms go
#            through numpy.
#          * The recursive fallback texture search walks the export
#            directory once and caches a filename index, instead of
#            re-walking the tree for every missing texture.
#          Behavior fixes:
#          * "Flip UV (V axis)" now only affects objects created by this
#            import -- it used to flip every mesh already in the scene.
#          * Unknown-material slots share one "CV_Unknown" material
#            instead of creating a new datablock per object.
#          * Import errors now print a full traceback to the console.
#  1.7.0 - Opt-in "Fix Hidden Dado/Notch Faces": cuts away the uncut
#          covering face CV sometimes exports over an interior dado
#          pocket, exposing the pocket geometry already in the file.
#          Standalone DADO/NOTCH/BORE sibling reference objects now move
#          into the hidden features collection.
#  1.6.0 - Collections preserve each part's association with its
#          assembly (per-assembly collections named from CV's own
#          label). Fixed "Merge Vertices by Distance" toggle visibility.
#  1.5.0 - Optional "Clean Topology" post-process (Limited Dissolve +
#          Tris to Quads), off by default.
#  1.4.1 - Automatic "Merge Vertices by Distance" after joining.
#  1.4.0 - Physical parts joined into one object per panel instance.
#  1.3.0 - (prior baseline)
# ============================================================

bl_info = {
    "name": "Cabinet Vision DAE Importer",
    "author": "Custom",
    "version": (1, 14, 0),
    "blender": (4, 0, 0),
    "location": "File > Import > Cabinet Vision (.dae)",
    "description": "Import Cabinet Vision Collada exports with correct geometry, materials, UVs, hierarchy, and joined physical parts",
    "category": "Import-Export",
}

import os
import re
import math
import xml.etree.ElementTree as ET

import bpy
import bmesh
import mathutils
import numpy as np
from bpy.props import StringProperty, BoolProperty, FloatProperty
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


# CV bore/hardware objects whose holes are tessellated into the panel faces.
# Part-type names listed here are moved to a hidden "CV Hidden Features"
# collection instead of importing as visible objects. Currently empty (all
# bore objects import normally); kept as a configuration point.
_BORE_PART_TYPES = frozenset()

# Sub-part name fragments that mark a leaf as a *feature* cut into a panel
# (a drilled hole, a dado groove, a notch) rather than an independent
# physical part in its own right. Cabinet Vision wraps every one of these
# features in its own nested "PA_" node, even a single boring, so they
# can't be told apart from a genuinely separate part by nesting depth
# alone -- only by name. Used to decide physical-part membership/naming
# (see _is_physical_part_root / _pick_primary_name) -- BORE stays in this
# set so boring operations are still recognized as belonging to the panel
# they're cut into rather than being treated as their own separate part.
_FEATURE_KEYWORDS = ("BORE", "DADO", "NOTCH")

# Subset of _FEATURE_KEYWORDS that gets routed to the hidden "CV Hidden
# Features" collection (see _gather_instances / _build_node) rather than
# staying merged and visible in the panel's mesh. BORE is deliberately
# excluded: boring/drilling operations should stay visible, unlike DADO/
# NOTCH pockets which are typically redundant duplicate geometry (e.g.
# "UBDADO").
_HIDDEN_FEATURE_KEYWORDS = ("DADO", "NOTCH")


def _is_feature_name(name):
    n = name.upper()
    return any(k in n for k in _FEATURE_KEYWORDS)


def _is_hidden_feature_name(name):
    n = name.upper()
    return any(k in n for k in _HIDDEN_FEATURE_KEYWORDS)


# Cabinet Vision's VN_ wrapper ids encode a human-readable assembly label
# ("Base_Cabinet_Assembly", "Molding_Molding_Assembly", ...) sandwiched
# between the hash and a trailing "<instance number>[_<letter>]", e.g.
# "VN_Sh41fd5fc0_Base_Cabinet_Assembly_44_a". Used to name each assembly's
# collection so it reads like "Base Cabinet Assembly" instead of a hash.
_ASSEMBLY_LABEL_RE = re.compile(r"^VN_Sh[0-9a-fA-F]+_(.+?)_\d+(?:_[a-zA-Z])?$")


# ──────────────────────────────────────────────────────────────
#  Parser
# ──────────────────────────────────────────────────────────────

class DAEParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.directory = os.path.dirname(os.path.abspath(filepath))
        self.up_axis = "Y_UP"
        self.unit_meter = 1.0
        self.images = {}
        self.effects = {}
        self.materials = {}
        self.geometries = {}
        self.lights = {}       # id -> light dict
        self.lib_nodes = {}    # id -> raw element (from library_nodes)
        self.scene_nodes = []
        tree = ET.parse(filepath)
        self._root = tree.getroot()
        tag = self._root.tag
        self._ns = tag[1:tag.index("}")] if tag.startswith("{") else ""

    def _t(self, n):
        return "{%s}%s" % (self._ns, n) if self._ns else n

    def _find(self, el, *path):
        for n in path:
            if el is None:
                return None
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
        self._lights()
        self._parse_library_nodes()
        self._scene()
        _log("up=%s unit=%s images=%d effects=%d mats=%d geoms=%d lights=%d nodes=%d" % (
            self.up_axis, self.unit_meter,
            len(self.images), len(self.effects),
            len(self.materials), len(self.geometries),
            len(self.lights), len(self.scene_nodes)))

    def _asset(self):
        a = self._find(self._root, "asset")
        if a is None:
            return
        u = self._find(a, "up_axis")
        if u is not None and u.text:
            self.up_axis = u.text.strip().upper()
        un = self._find(a, "unit")
        if un is not None:
            try:
                self.unit_meter = float(un.get("meter", "1.0"))
            except ValueError:
                pass

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
        d = {"color": (0.8, 0.8, 0.8, 1.0), "texture_path": None,
             "roughness": 0.5, "metallic": 0.0, "emission": (0, 0, 0)}
        prof = self._find(eff_el, "profile_COMMON")
        if prof is None:
            return d
        surf_map = {}
        samp_map = {}
        for np_el in self._all(prof, "newparam"):
            sid = np_el.get("sid", "")
            sf = self._find(np_el, "surface")
            if sf is not None:
                i = self._find(sf, "init_from")
                if i is not None and i.text:
                    surf_map[sid] = i.text.strip()
            sm = self._find(np_el, "sampler2D")
            if sm is not None:
                s = self._find(sm, "source")
                if s is not None and s.text:
                    samp_map[sid] = s.text.strip()

        def rtex(ref):
            s = samp_map.get(ref, ref)
            i = surf_map.get(s, s)
            return self.images.get(i) or self.images.get(ref)

        tech = self._find(prof, "technique")
        if tech is None:
            return d
        shader = None
        for st in ("phong", "lambert", "blinn", "constant"):
            shader = self._find(tech, st)
            if shader is not None:
                break
        if shader is None:
            return d
        diff = self._find(shader, "diffuse")
        if diff is not None:
            ce = self._find(diff, "color")
            te = self._find(diff, "texture")
            if ce is not None and ce.text:
                v = list(map(float, ce.text.split()))
                d["color"] = tuple(v[:4]) if len(v) >= 4 else (*v[:3], 1.0)
            elif te is not None:
                p = rtex(te.get("texture", ""))
                if p:
                    d["texture_path"] = p
        se = self._find(shader, "shininess")
        if se is not None:
            fe = self._find(se, "float")
            if fe is not None and fe.text:
                try:
                    d["roughness"] = max(0.0, min(1.0, 1.0 - float(fe.text) / 128.0))
                except ValueError:
                    pass
        return d

    def _materials(self):
        lib = self._find(self._root, "library_materials")
        for mat in self._all(lib, "material"):
            mid = mat.get("id", "")
            name = mat.get("name", mid)
            inst = self._find(mat, "instance_effect")
            if inst is not None:
                eid = _strip(inst.get("url", ""))
                self.materials[mid] = {"name": name, **self.effects.get(eid, {})}
            else:
                self.materials[mid] = {"name": name, "color": (0.8, 0.8, 0.8, 1.0),
                                       "texture_path": None, "roughness": 0.5, "metallic": 0.0}

    def _float_source(self, src_el):
        fa = self._find(src_el, "float_array")
        if fa is None or not fa.text:
            return []
        vals = list(map(float, fa.text.split()))
        stride = 1
        tc = self._find(src_el, "technique_common")
        if tc is not None:
            acc = self._find(tc, "accessor")
            if acc is not None:
                try:
                    stride = max(1, int(acc.get("stride", "1")))
                except ValueError:
                    pass
        return [tuple(vals[i:i + stride]) for i in range(0, len(vals), stride)]

    def _geometries(self):
        lib = self._find(self._root, "library_geometries")
        for geom in self._all(lib, "geometry"):
            gid = geom.get("id", "")
            gname = geom.get("name", gid)
            mesh = self._find(geom, "mesh")
            if mesh is None:
                continue

            sources = {}
            for src in self._all(mesh, "source"):
                sid = src.get("id", "").strip()
                data = self._float_source(src)
                if data:
                    sources[sid] = data

            verts_el = self._find(mesh, "vertices")
            verts_id = verts_el.get("id", "").strip() if verts_el is not None else ""
            pos_sid = None
            if verts_el is not None:
                for inp in self._all(verts_el, "input"):
                    if inp.get("semantic") == "POSITION":
                        pos_sid = _strip(inp.get("source", ""))
                        break

            prims = []
            for pt in ("polylist", "triangles", "polygons"):
                for p in self._all(mesh, pt):
                    prims.append((pt, p))

            self.geometries[gid] = {
                "name": gname, "sources": sources,
                "verts_id": verts_id, "pos_sid": pos_sid, "prims": prims
            }
        _log("geometries indexed: %d" % len(self.geometries))

    def _lights(self):
        lib = self._find(self._root, "library_lights")
        for light in self._all(lib, "light"):
            lid = light.get("id", "")
            lname = light.get("name", lid)
            tc = self._find(light, "technique_common")
            if tc is None:
                continue
            d = {"name": lname, "type": "POINT", "color": (1.0, 1.0, 1.0), "energy": 10.0}
            for ltype in ("point", "directional", "spot", "ambient"):
                el = self._find(tc, ltype)
                if el is None:
                    continue
                d["type"] = {"point": "POINT", "directional": "SUN",
                             "spot": "SPOT", "ambient": "SUN"}[ltype]
                c = self._find(el, "color")
                if c is not None and c.text:
                    try:
                        v = list(map(float, c.text.split()))
                        d["color"] = tuple(v[:3]) if len(v) >= 3 else (1.0, 1.0, 1.0)
                    except ValueError:
                        pass
                if ltype == "spot":
                    fa = self._find(el, "falloff_angle")
                    if fa is not None and fa.text:
                        try:
                            d["spot_size"] = math.radians(float(fa.text))
                        except ValueError:
                            pass
                if ltype == "point":
                    qa = self._find(el, "quadratic_attenuation")
                    if qa is not None and qa.text:
                        try:
                            q = float(qa.text)
                            if q > 1e-8:
                                d["energy"] = min(1000.0, 1.0 / q)
                        except ValueError:
                            pass
                break
            self.lights[lid] = d
            _log("  light '%s': type=%s color=%s" % (lid, d["type"], d["color"]))

    def _node_matrix(self, node_el):
        m = mathutils.Matrix.Identity(4)
        for ch in node_el:
            tag = ch.tag.split("}")[-1] if "}" in ch.tag else ch.tag
            if not ch.text or not ch.text.strip():
                continue
            try:
                if tag == "matrix":
                    v = list(map(float, ch.text.split()))
                    if len(v) == 16:
                        m = m @ mathutils.Matrix([v[0:4], v[4:8], v[8:12], v[12:16]])
                elif tag == "translate":
                    x, y, z = map(float, ch.text.split())
                    m = m @ mathutils.Matrix.Translation((x, y, z))
                elif tag == "rotate":
                    ax, ay, az, ang = map(float, ch.text.split())
                    axis = mathutils.Vector((ax, ay, az))
                    if axis.length > 1e-8:
                        m = m @ mathutils.Matrix.Rotation(math.radians(ang), 4, axis.normalized())
                elif tag == "scale":
                    sx, sy, sz = map(float, ch.text.split())
                    m = m @ mathutils.Matrix.Diagonal((sx, sy, sz, 1.0)).to_4x4()
            except (ValueError, ZeroDivisionError):
                continue
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
        nid = node_el.get("id", "")
        name = _cv_part_name(node_el.get("name", nid) or nid or "Node")
        mat = self._node_matrix(node_el)
        ginst = []
        for ig in self._all(node_el, "instance_geometry"):
            gid = _strip(ig.get("url", ""))
            mm = {}
            bm = self._find(ig, "bind_material")
            if bm is not None:
                tc = self._find(bm, "technique_common")
                for im in self._all(tc, "instance_material"):
                    mm[im.get("symbol", "")] = _strip(im.get("target", ""))
            ginst.append({"gid": gid, "mmap": mm})
        linst = [_strip(il.get("url", "")) for il in self._all(node_el, "instance_light")
                 if _strip(il.get("url", ""))]
        children = [self._parse_node(c) for c in self._all(node_el, "node")]
        # Cabinet Vision stores geometry in <library_nodes> and references it
        # from visual scene nodes via <instance_node>. Resolve those here.
        for inst in self._all(node_el, "instance_node"):
            ref_id = _strip(inst.get("url", ""))
            lib_node_el = self.lib_nodes.get(ref_id)
            if lib_node_el is not None:
                children.append(self._parse_node(lib_node_el))
            else:
                _log("WARNING: instance_node %r not in library_nodes" % ref_id)
        return {"name": name, "mat": mat, "ginst": ginst, "linst": linst, "children": children}

    def _scene(self):
        sc = self._find(self._root, "scene")
        if sc is None:
            return
        ivs = self._find(sc, "instance_visual_scene")
        if ivs is None:
            return
        sid = _strip(ivs.get("url", ""))
        lib = self._find(self._root, "library_visual_scenes")
        for vs in self._all(lib, "visual_scene"):
            if vs.get("id") == sid:
                self.scene_nodes = [self._parse_node(n) for n in self._all(vs, "node")]
                break


# ──────────────────────────────────────────────────────────────
#  Builder
# ──────────────────────────────────────────────────────────────

class BlenderBuilder:
    def __init__(self, parser, report_fn=None, join_parts=True, merge_distance=0.0001,
                 hide_feature_parts=True):
        self.p = parser
        self.report = report_fn or (lambda m: None)
        self.bl_mats = {}
        # gid -> decoded geometry dict (or None if unusable). Each geometry
        # is decoded from XML exactly once, no matter how many instances
        # reference it.
        self._geom_cache = {}
        self._tex_index = None      # lowercase filename -> path, built lazily
        self._unknown_mat = None    # shared fallback material
        self._created_objects = []  # every mesh object created by this import
        self._join_groups = []      # legacy per-type groups joined via operator
        self._joined_objects = []   # merged/joined objects for post-processing
        # When True, each physical part's faces, edgebanding, dados and
        # boring are merged into a single mesh object (see
        # _is_physical_part_root / _build_physical_part below).
        self._join_parts = join_parts
        # Distance (in Blender units, i.e. meters after CV's unit scale is
        # applied) within which coincident vertices left over from merging
        # independently-tessellated faces/edgebanding/boring are welded
        # together. 0 (or None) disables the weld pass.
        self._merge_distance = merge_distance
        # When True (default), BORE/DADO/NOTCH feature geometry (e.g.
        # "UBDADO", "_HGAVBORE") is always routed to the hidden "CV Hidden
        # Features" collection instead of being fused into its parent
        # panel's merged mesh -- see _gather_instances. Off restores the
        # legacy behavior of merging nested feature geometry into the
        # panel it cuts into.
        self._hide_feature_parts = hide_feature_parts

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

    # ── materials & textures ───────────────────────────────────────────

    def _find_tex(self, path):
        if os.path.exists(path):
            return path
        base = os.path.basename(path)
        for sub in ("", "textures", "Textures", "images", "Images", "materials", "Maps"):
            c = os.path.join(self.p.directory, sub, base)
            if os.path.exists(c):
                return c
        # Fallback: recursive, case-insensitive search under the .dae's own
        # directory. The walk runs once and is cached as a filename index,
        # instead of re-walking the tree for every missing texture.
        if self._tex_index is None:
            self._tex_index = {}
            for root, _dirs, files in os.walk(self.p.directory):
                for f in files:
                    self._tex_index.setdefault(f.lower(), os.path.join(root, f))
        return self._tex_index.get(base.lower())

    def _make_mat(self, mid, md):
        # Prefer the image filename stem (e.g. "BCW_MAPLE_cee3ec") as the
        # material name; fall back to the DAE material name or id.
        tp = md.get("texture_path")
        if tp:
            mat_name = os.path.splitext(os.path.basename(tp))[0]
        else:
            mat_name = md.get("name") or mid
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        out = nodes.new("ShaderNodeOutputMaterial"); out.location = (400, 0)
        bsdf = nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (0, 0)
        links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        bsdf.inputs["Roughness"].default_value = md.get("roughness", 0.5)
        bsdf.inputs["Metallic"].default_value = md.get("metallic", 0.0)
        em = md.get("emission", (0, 0, 0))
        if any(v > 0.001 for v in em):
            bsdf.inputs["Emission Color"].default_value = (*em, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 1.0
        loaded = False
        if tp:
            ap = self._find_tex(tp)
            if ap:
                try:
                    img = bpy.data.images.load(ap, check_existing=True)
                    img.colorspace_settings.name = "sRGB"
                    uv = nodes.new("ShaderNodeTexCoord"); uv.location = (-600, 200)
                    tex = nodes.new("ShaderNodeTexImage"); tex.location = (-300, 200)
                    tex.image = img
                    links.new(uv.outputs["UV"], tex.inputs["Vector"])
                    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
                    loaded = True
                except Exception as e:
                    _log("Texture load failed:", ap, e)
            else:
                _log("Texture NOT FOUND for material '%s': %r (looked under %s)" % (
                    mat_name, tp, self.p.directory))
        if not loaded:
            bsdf.inputs["Base Color"].default_value = md.get("color", (0.8, 0.8, 0.8, 1.0))
        return mat

    def _material_for(self, mid):
        """Blender material for a DAE material id, sharing one fallback
        material for unknown/missing ids instead of creating a new
        datablock per object."""
        m = self.bl_mats.get(mid)
        if m is None:
            if self._unknown_mat is None:
                self._unknown_mat = bpy.data.materials.new(name="CV_Unknown")
                self._unknown_mat.use_nodes = True
            m = self._unknown_mat
        return m

    # ── collections ────────────────────────────────────────────────────

    def _get_hidden_features_col(self, scene_col):
        """Return (creating if needed) a hidden collection for reference/
        helper geometry that isn't a real visible part on its own: bore
        hardware, and standalone dado/notch marker objects that Cabinet
        Vision didn't nest inside the one panel they cut into (so they
        never get absorbed into that panel's merge -- see
        _is_physical_part_root)."""
        col = bpy.data.collections.get("CV Hidden Features")
        if col is None:
            col = bpy.data.collections.new("CV Hidden Features")
            scene_col.children.link(col)
            col.hide_viewport = True
            col.hide_render = True
        return col

    def _get_or_create_col(self, parent_col, name):
        """Return existing child collection named `name`, or create and link one."""
        for child in parent_col.children:
            if child.name == name:
                return child
        col = bpy.data.collections.new(name)
        parent_col.children.link(col)
        return col

    @staticmethod
    def _collection_key(part_name):
        """Collection-grouping key for a part-type name. Every *BORE
        sub-type (LFVBORE, LRVBORE, _HGCVBORE, _HGAVBORE, ...) shares one
        common "Bores" collection per assembly instead of each fragmenting
        into its own separately-named collection -- Cabinet Vision has
        dozens of distinct bore type codes, and grouping them by their
        literal name scatters what a person thinks of as one thing (the
        shelf-pin/hinge boring for this assembly) across many collections.
        Non-bore part types (e.g. "AS") are grouped by their own name, one
        shared collection per assembly, unchanged."""
        return "Bores" if "BORE" in part_name.upper() else part_name

    # ── physical-part detection ─────────────────────────────────────────

    def _gather_leaf_names(self, node, out):
        """Depth-first collect the resolved CV name of every geometry-bearing
        leaf under `node` (including itself)."""
        if node["ginst"]:
            out.append(node["name"])
        for ch in node["children"]:
            self._gather_leaf_names(ch, out)

    def _is_physical_part_root(self, node):
        """True when `node` (a PA_ wrapper) represents exactly one physical
        part: it has at least one direct, non-PA_ child carrying real panel
        geometry (a face or edgeband), and every nested PA_ child beneath it
        contributes only boring/dado/notch features of that same panel --
        never an unrelated separate part. Cabinet Vision wraps individual
        bores/dados in their own PA_ node too, so nesting depth alone can't
        distinguish "one panel with holes" from "an assembly of parts";
        this checks the actual leaf names instead."""
        direct_structural = any(
            not ch["name"].startswith("PA_") and not _is_feature_name(ch["name"])
            for ch in node["children"]
        )
        if not direct_structural:
            return False
        for ch in node["children"]:
            if ch["name"].startswith("PA_"):
                names = []
                self._gather_leaf_names(ch, names)
                if any(not _is_feature_name(n) for n in names):
                    return False
        return True

    def _pick_primary_name(self, node):
        """Name a merged physical part after its most common non-feature
        leaf (e.g. 'RU'), falling back to the most common leaf overall if
        every leaf happens to be a feature."""
        names = []
        self._gather_leaf_names(node, names)
        pool = [n for n in names if not _is_feature_name(n)] or names
        if not pool:
            return node["name"]
        counts = {}
        for n in pool:
            counts[n] = counts.get(n, 0) + 1
        return max(counts.items(), key=lambda kv: kv[1])[0]

    # ── assembly grouping (keep each part associated with its assembly) ──

    def _first_vn_name(self, node):
        """Depth-first search for the first VN_-wrapper id under `node`,
        used to recover a human-readable assembly label (see
        _ASSEMBLY_LABEL_RE)."""
        if node["name"].startswith("VN_"):
            return node["name"]
        for ch in node["children"]:
            found = self._first_vn_name(ch)
            if found:
                return found
        return None

    def _pick_assembly_name(self, node):
        vn = self._first_vn_name(node)
        if vn:
            m = _ASSEMBLY_LABEL_RE.match(vn)
            if m:
                label = m.group(1).replace("_", " ").strip()
                if label:
                    return label
        return "Assembly (%s)" % node["name"]

    # ── geometry decoding (once per gid, cached) ─────────────────────────

    def _decode_geometry(self, gid):
        """Decode a <geometry> into local-space arrays, once per gid.
        Returns {"pos": (N,3) float array, "faces": [vert-index tuples],
        "uvs": [per-face uv list or None], "syms": [per-face material
        symbol], "has_uvs": bool} or None if the geometry is unusable."""
        if gid in self._geom_cache:
            return self._geom_cache[gid]
        gdata = self.p.geometries.get(gid)
        dec = self._decode_geometry_impl(gdata) if gdata is not None else None
        if gdata is None:
            _log("WARNING: geometry '%s' not found" % gid)
        self._geom_cache[gid] = dec
        return dec

    def _decode_geometry_impl(self, gdata):
        sources = gdata["sources"]
        pos_sid = gdata["pos_sid"]
        prims = gdata["prims"]
        gname = gdata["name"]
        t = self.p._t

        # ── locate position source ──────────────────────────
        if pos_sid and pos_sid not in sources:
            _log("  '%s': pos_sid not in sources; searching primitives" % gname)
            pos_sid = None

        if pos_sid is None:
            # Try POSITION semantic directly in primitive inputs
            for _pt, pel in prims:
                for inp in pel.findall(t("input")):
                    if inp.get("semantic", "") == "POSITION":
                        sid = _strip(inp.get("source", ""))
                        if sid in sources:
                            pos_sid = sid
                            break
                if pos_sid:
                    break

        if pos_sid is None:
            # Last resort: first stride-3 source
            for sid, data in sources.items():
                if data and len(data[0]) == 3:
                    pos_sid = sid
                    break

        if not pos_sid or pos_sid not in sources:
            msg = "'%s': no position source (sources: %s)" % (gname, list(sources.keys()))
            _log("SKIP:", msg)
            self.report(msg)
            return None

        pos = [p[:3] for p in sources[pos_sid]]
        if not pos:
            _log("SKIP: '%s': position source empty" % gname)
            return None
        n_pos = len(pos)

        # ── decode faces ────────────────────────────────────
        faces = []
        uvs = []
        syms = []
        has_uvs = False

        for prim_type, pel in prims:
            sym = pel.get("material", "")

            pos_off = 0
            uv_off = None
            uv_src = None
            max_off = 0
            found_pos = False

            for inp in pel.findall(t("input")):
                sem = inp.get("semantic", "")
                sid = _strip(inp.get("source", ""))
                try:
                    off = int(inp.get("offset", "0").strip())
                except ValueError:
                    off = 0
                max_off = max(max_off, off)

                if sem in ("VERTEX", "POSITION"):
                    pos_off = off
                    found_pos = True
                    if sem == "POSITION" and sid and sid != pos_sid and sid in sources:
                        _log("  '%s': overriding pos source to %r" % (gname, sid))
                        pos_sid = sid
                        pos = [p[:3] for p in sources[sid]]
                        n_pos = len(pos)
                elif sem == "TEXCOORD" and uv_off is None and sid in sources:
                    uv_off = off
                    uv_src = sources[sid]
                    has_uvs = True

            stride = max_off + 1

            if not found_pos:
                _log("  '%s': no VERTEX/POSITION input in %s; skipping" % (gname, prim_type))
                continue

            p_el = pel.find(t("p"))
            # For "polygons" type, faces may live inside <ph> elements (not a
            # top-level <p>), so don't skip early -- the polygons branch
            # handles <ph> itself.
            if (p_el is None or not (p_el.text or "").strip()) and prim_type != "polygons":
                _log("  '%s': no <p> data in %s; skipping" % (gname, prim_type))
                continue
            raw = (list(map(int, p_el.text.split()))
                   if (p_el is not None and (p_el.text or "").strip()) else [])

            # vertex counts
            if prim_type == "triangles":
                cnt = int(pel.get("count", "0"))
                vcnts = [3] * cnt
            elif prim_type == "polylist":
                ve = pel.find(t("vcount"))
                if ve is not None and (ve.text or "").strip():
                    vcnts = list(map(int, ve.text.split()))
                else:
                    cnt = int(pel.get("count", "0"))
                    if cnt and len(raw) == cnt * 3 * stride:
                        vcnts = [3] * cnt
                    else:
                        _log("  '%s': polylist missing vcount; skipping" % gname)
                        continue
            elif prim_type == "polygons":
                sub_ps = pel.findall(t("p"))
                ph_els = pel.findall(t("ph"))
                if ph_els:
                    from mathutils.geometry import tessellate_polygon as _tess
                    for ph in ph_els:
                        sp = ph.find(t("p"))
                        if sp is None or not (sp.text or "").strip():
                            continue
                        sr = list(map(int, sp.text.split()))
                        nv_ext = len(sr) // stride
                        ext_vids, ext_uvs = self._decode(sr, nv_ext, stride, pos_off,
                                                         uv_off, uv_src, n_pos)

                        # Collect hole contours from <ph><h> children
                        h_data = []
                        for h_el in ph.findall(t("h")):
                            if not (h_el.text or "").strip():
                                continue
                            hr = list(map(int, h_el.text.split()))
                            nv_h = len(hr) // stride
                            h_vids, h_uvs = self._decode(hr, nv_h, stride, pos_off,
                                                         uv_off, uv_src, n_pos)
                            if h_vids:
                                h_data.append((h_vids, h_uvs))

                        if not h_data:
                            # No holes -- emit simple polygon
                            if ext_vids:
                                faces.append(ext_vids); uvs.append(ext_uvs); syms.append(sym)
                        else:
                            # Build vid->UV lookup for outer ring and all holes
                            vid_uv = {}
                            if ext_uvs:
                                vid_uv.update(zip(ext_vids, ext_uvs))
                            for h_vids, h_uvs in h_data:
                                if h_uvs:
                                    for vid, uv in zip(h_vids, h_uvs):
                                        vid_uv.setdefault(vid, uv)

                            # Concatenated vid list (outer first, then holes)
                            # -- matches tessellate_polygon's index space
                            all_ring_vids = list(ext_vids)
                            for h_vids, _ in h_data:
                                all_ring_vids.extend(h_vids)

                            outer_vecs = [mathutils.Vector(pos[vid]) for vid in ext_vids]
                            hole_vecs = [[mathutils.Vector(pos[vid]) for vid in h_vids]
                                         for h_vids, _ in h_data]
                            try:
                                tris = _tess([outer_vecs] + hole_vecs)
                                for tri in tris:
                                    f = [all_ring_vids[tri[j]] for j in range(3)]
                                    u = [vid_uv.get(all_ring_vids[tri[j]], (0.0, 0.0))
                                         for j in range(3)]
                                    faces.append(f); uvs.append(u); syms.append(sym)
                            except Exception as _te:
                                _log("  tessellate_polygon failed (%s); simple face fallback" % _te)
                                if ext_vids:
                                    faces.append(ext_vids); uvs.append(ext_uvs); syms.append(sym)

                    # Also handle plain <p> children alongside <ph> elements
                    for sp in sub_ps:
                        if not (sp.text or "").strip():
                            continue
                        sr = list(map(int, sp.text.split()))
                        nv = len(sr) // stride
                        f, u = self._decode(sr, nv, stride, pos_off, uv_off, uv_src, n_pos)
                        if f:
                            faces.append(f); uvs.append(u); syms.append(sym)
                    continue
                elif len(sub_ps) > 1:
                    for sp in sub_ps:
                        if not (sp.text or "").strip():
                            continue
                        sr = list(map(int, sp.text.split()))
                        nv = len(sr) // stride
                        f, u = self._decode(sr, nv, stride, pos_off, uv_off, uv_src, n_pos)
                        if f:
                            faces.append(f); uvs.append(u); syms.append(sym)
                    continue
                else:
                    tv = len(raw) // stride
                    for g in (3, 4):
                        if tv % g == 0:
                            vcnts = [g] * (tv // g)
                            break
                    else:
                        vcnts = [tv]
            else:
                continue

            cur = 0
            for vc in vcnts:
                bs = vc * stride
                sub = raw[cur:cur + bs]; cur += bs
                if len(sub) < bs:
                    break
                f, u = self._decode(sub, vc, stride, pos_off, uv_off, uv_src, n_pos)
                if f:
                    faces.append(f); uvs.append(u); syms.append(sym)

        if not faces:
            msg = "'%s': 0 faces built" % gname
            _log("SKIP:", msg)
            self.report(msg)
            return None

        _log("  decoded '%s': %d verts, %d faces%s" % (
            gname, n_pos, len(faces), " (uv)" if has_uvs else ""))
        return {"pos": np.array(pos, dtype=np.float64), "faces": faces,
                "uvs": uvs, "syms": syms, "has_uvs": has_uvs, "name": gname}

    @staticmethod
    def _decode(raw, n_verts, stride, pos_off, uv_off, uv_src, n_pos):
        face = []
        uvs = [] if uv_src is not None else None
        for vi in range(n_verts):
            blk = raw[vi * stride:(vi + 1) * stride]
            if len(blk) < stride:
                return [], None
            pi = blk[pos_off]
            if pi >= n_pos:
                pi = n_pos - 1
            face.append(pi)
            if uv_src is not None and uv_off is not None and uv_off < len(blk):
                ui = blk[uv_off]
                uv = uv_src[ui] if ui < len(uv_src) else (0.0, 0.0)
                uvs.append((uv[0], uv[1]))
        return (face, uvs) if len(face) >= 3 else ([], None)

    # ── mesh object construction ─────────────────────────────────────────

    @staticmethod
    def _xform(pos, world):
        """Transform an (N,3) position array by a mathutils 4x4 matrix."""
        m = np.array(world, dtype=np.float64)
        return pos @ m[:3, :3].T + m[:3, 3]

    def _build_mesh_object(self, name, instances):
        """Build ONE mesh object from a list of (decoded, world, mmap)
        instances -- a single geometry instance, or a whole physical
        part's faces + edgebanding + boring merged directly (replacing
        the old create-many-objects-then-operator-join flow). World
        transforms are baked into the vertices (object matrix stays
        identity), matching previous behavior. Returns (object or None,
        number of instances that contributed faces)."""
        vert_parts = []
        faces = []
        uv_pairs = []
        mids = []
        has_uvs = False
        offset = 0
        used = 0
        bore_uv_ranges = []

        for entry in instances:
            if len(entry) == 4:
                dec, world, mmap, inst_name = entry
            else:
                dec, world, mmap = entry
                inst_name = name
            if dec is None or not dec["faces"]:
                continue
            v = self._xform(dec["pos"], world)
            vert_parts.append(v)
            if offset:
                faces.extend(tuple(i + offset for i in f) for f in dec["faces"])
            else:
                faces.extend(dec["faces"])
            uv_start = len(uv_pairs)
            for f, fuv in zip(dec["faces"], dec["uvs"]):
                if fuv:
                    uv_pairs.extend(fuv)
                else:
                    uv_pairs.extend((0.0, 0.0) for _ in f)
            if inst_name.upper().endswith("BORE"):
                bore_uv_ranges.append((uv_start, len(uv_pairs)))
            for s in dec["syms"]:
                mids.append(mmap.get(s, ""))
            has_uvs = has_uvs or dec["has_uvs"]
            offset += len(v)
            used += 1

        if not faces:
            return None, 0

        mesh = bpy.data.meshes.new(name=name)
        allv = np.vstack(vert_parts)
        mesh.from_pydata(allv.tolist(), [], faces)
        mesh.update()

        if has_uvs:
            layer = mesh.uv_layers.new(name="UVMap")
            uv = np.asarray(uv_pairs, dtype=np.float32)
            # Bore geometry's own UV parameterization needs a 90-degree
            # rotation to align with the surrounding panel/material. This
            # used to be gated on the whole merged object's name ending in
            # "BORE", which only ever fired when a bore stayed its own
            # standalone object. Since v1.9.0+ joins bore instances into
            # the panel's own merged mesh (named after the panel, e.g.
            # "TO"/"SL"/"BT"), that check silently stopped firing for the
            # far more common merged case, leaving bore UVs unrotated and
            # visibly mismatched ("mangled") against the panel's grain.
            # Apply the rotation per contributing instance instead, so it
            # fires regardless of what the merged object ends up named.
            for lo, hi in bore_uv_ranges:
                uv[lo:hi] = np.column_stack((1.0 - uv[lo:hi, 1], uv[lo:hi, 0]))  # 90 deg CCW
            layer.data.foreach_set("uv", uv.ravel())

        # Material slots: one per distinct material id actually used.
        slot_of = {}
        for mid in mids:
            if mid not in slot_of:
                slot_of[mid] = len(mesh.materials)
                mesh.materials.append(self._material_for(mid))
        if len(slot_of) > 1:
            mesh.polygons.foreach_set(
                "material_index",
                np.fromiter((slot_of[m] for m in mids), dtype=np.int32, count=len(mids)))

        obj = bpy.data.objects.new(name=name, object_data=mesh)
        obj.matrix_world = mathutils.Matrix.Identity(4)
        self._created_objects.append(obj)
        return obj, used

    def _make_light(self, ldict, name, world):
        """Create a Blender light object from a parsed Collada light dict."""
        ltype = ldict.get("type", "POINT")
        ldata = bpy.data.lights.new(name=name, type=ltype)
        ldata.color = ldict.get("color", (1.0, 1.0, 1.0))
        ldata.energy = ldict.get("energy", 10.0)
        if ltype == "SPOT" and "spot_size" in ldict:
            ldata.spot_size = ldict["spot_size"]
        obj = bpy.data.objects.new(name=name, object_data=ldata)
        obj.matrix_world = world
        _log("  light created: '%s' type=%s energy=%.2f" % (name, ltype, ldata.energy))
        return obj

    # ── scene walking ────────────────────────────────────────────────────

    def _gather_instances(self, node, world, meshes, lights):
        """Recursively collect every geometry/light instance under `node`
        (regardless of further PA_/VN_ nesting) with resolved world
        matrices, so a whole physical part can be built as one mesh.

        DADO/NOTCH feature leaves (not BORE -- boring/drilling operations
        stay visible, see _HIDDEN_FEATURE_KEYWORDS) are diverted straight
        to the hidden "CV Hidden Features" collection instead of being
        folded into the merge (when self._hide_feature_parts is on, the
        default). Cabinet Vision nests these inside the very panel they
        cut into -- normally via their own nested PA_ wrapper, sitting
        alongside the panel's bare structural geometry as a direct
        sibling -- which previously meant _build_physical_part's
        all-or-nothing gather here fused their geometry straight into
        the panel mesh with no way to hide it afterward: the "move
        standalone features to the hidden collection" branch in
        _build_node only ever fired for features CV exports as
        un-nestable orphan siblings, never for the far more common
        nested case. Turn this off if a part's dado/notch pocket only
        exists as separate geometry under one of these feature nodes
        and you rely on "Fix Hidden Dado Faces" to expose it -- with
        this on, that geometry is hidden away rather than merged in, so
        there's nothing left in the merged mesh for that fix to find."""
        if (self._hide_feature_parts and _is_hidden_feature_name(node["name"])
                and node["ginst"]):
            hidden_col = self._get_hidden_features_col(bpy.context.scene.collection)
            for inst in node["ginst"]:
                dec = self._decode_geometry(inst["gid"])
                obj, _ = self._build_mesh_object(node["name"], [(dec, world, inst["mmap"])])
                if obj:
                    hidden_col.objects.link(obj)
            for ch in node["children"]:
                self._gather_instances(ch, world @ ch["mat"], meshes, lights)
            return
        for inst in node["ginst"]:
            meshes.append((self._decode_geometry(inst["gid"]), world, inst["mmap"], node["name"]))
        for lid in node.get("linst", []):
            lights.append((lid, world))
        for ch in node["children"]:
            self._gather_instances(ch, world @ ch["mat"], meshes, lights)

    def _build_physical_part(self, node, parent_col, world):
        """Build an entire physical-part subtree (faces + edgebanding +
        boring/dado) directly as ONE mesh object in a shared part-type
        collection -- no temporary objects, no operator join."""
        primary = self._pick_primary_name(node)
        col = self._get_or_create_col(parent_col, self._collection_key(primary))
        meshes, lights = [], []
        self._gather_instances(node, world, meshes, lights)
        obj, used = self._build_mesh_object(primary, meshes)
        if obj:
            col.objects.link(obj)
            if used > 1:
                # Multiple independently-tessellated sub-meshes were merged:
                # queue for seam welding / optional post-processing.
                self._joined_objects.append(obj)
        for lid, lworld in lights:
            ldict = self.p.lights.get(lid)
            if ldict is None:
                _log("WARNING: light '%s' not found" % lid)
                continue
            col.objects.link(self._make_light(ldict, primary, lworld))

    def _build_node(self, node, parent_col, parent_world):
        world = parent_world @ node["mat"]
        name = node["name"]

        # Bore/hardware objects: move to hidden collection (holes are
        # already tessellated into panel faces via <ph><h> data).
        if name in _BORE_PART_TYPES:
            bore_col = self._get_hidden_features_col(bpy.context.scene.collection)
            for inst in node["ginst"]:
                dec = self._decode_geometry(inst["gid"])
                obj, _ = self._build_mesh_object(name, [(dec, world, inst["mmap"])])
                if obj:
                    bore_col.objects.link(obj)
            for ch in node["children"]:
                self._build_node(ch, bore_col, world)
            return

        # Standalone dado/notch reference objects (not BORE -- boring/
        # drilling operations stay visible, see _HIDDEN_FEATURE_KEYWORDS):
        # Cabinet Vision normally nests these inside the one panel they
        # cut into, where _is_physical_part_root/_build_physical_part
        # above absorbs them into that panel's merge. When a feature is
        # instead exported as its own sibling node (e.g. a groove shared
        # across more than one part, like a back-panel dado spanning both
        # uprights), it never gets nested that way and falls through to
        # here as an ordinary leaf. It's reference/helper geometry, not
        # an independent visible part, so it goes in the hidden
        # collection rather than cluttering the visible scene under its
        # own name.
        if _is_hidden_feature_name(name) and node["ginst"]:
            hidden_col = self._get_hidden_features_col(bpy.context.scene.collection)
            for inst in node["ginst"]:
                dec = self._decode_geometry(inst["gid"])
                obj, _ = self._build_mesh_object(name, [(dec, world, inst["mmap"])])
                if obj:
                    hidden_col.objects.link(obj)
            for ch in node["children"]:
                self._build_node(ch, hidden_col, world)
            return

        # PA_ assembly wrappers.
        #
        # If this wrapper's own direct children already include real panel
        # geometry (faces/edgebanding), and every nested PA_ child
        # underneath it contributes only boring/dado/notch features of
        # that same panel (never an unrelated separate part), then this
        # node is exactly "one physical part" -- build its whole subtree
        # directly as a single merged object.
        #
        # Otherwise this wrapper groups multiple distinct parts/sub-
        # assemblies (a cabinet, a countertop, a run of cabinets, a room,
        # ...) -- Cabinet Vision nests many of these anonymous PA_ levels
        # on top of each other. Each one gets its own collection so every
        # part stays associated with the assembly (and the assembly's own
        # parent grouping) it actually belongs to, instead of same-named
        # parts from every assembly in the file pooling together the
        # moment a PA_ wrapper is skipped as "just a pass-through."
        if name.startswith("PA_") and not node["ginst"]:
            if (self._join_parts and node["children"]
                    and self._is_physical_part_root(node)):
                self._build_physical_part(node, parent_col, world)
                return
            if self._join_parts and node["children"]:
                # Cabinet Vision stacks multiple anonymous PA_ wrapper
                # levels for what's conceptually one assembly, each
                # resolving to the same VN_-derived label (e.g. "Tall
                # Cabinet Assembly"). Reuse an existing same-named
                # collection under this parent instead of always creating
                # a new one, so every part belonging to that assembly --
                # across however many stacked PA_ levels CV emitted --
                # lands in one shared collection instead of fragmenting
                # into "Tall Cabinet Assembly", "Tall Cabinet
                # Assembly.001", ".002", etc.
                asm_col = self._get_or_create_col(parent_col, self._pick_assembly_name(node))

                # Cabinet Vision sometimes exports a bore as its own
                # PA_+VN_-wrapped sibling of the part it's actually
                # drilled into, rather than nesting it inside that part
                # the way panel cuts normally are -- e.g. hinge bores
                # ("_HGAVBORE"/"_HGCVBORE") showing up under their own
                # "Molding_Door_NN" wrapper alongside the door's real
                # "Door_NN" slab wrapper, both direct children of the
                # same door assembly. Classify each direct child up
                # front (before building) by its own leaf geometry: a
                # child whose ENTIRE subtree is bore-only is a donor to
                # be absorbed elsewhere, not a part in its own right.
                # Anything labeled "Widget" (hinge arm/base and similar
                # hardware) is never a valid absorption target even
                # though it isn't feature-named. If exactly one
                # structural, non-widget child remains as a candidate,
                # every bore-only child's object(s) get joined into it.
                target_candidates = []
                bore_only_children = []
                for ch in node["children"]:
                    leaves = []
                    self._gather_leaf_names(ch, leaves)
                    non_feature = [n for n in leaves if not _is_feature_name(n)]
                    bore_leaves = [n for n in leaves
                                  if _is_feature_name(n) and not _is_hidden_feature_name(n)]
                    if leaves and not non_feature and bore_leaves:
                        bore_only_children.append(ch)
                        continue
                    vn = self._first_vn_name(ch)
                    if not (vn and "widget" in vn.lower()):
                        target_candidates.append(ch)

                # Track objects via self._created_objects (populated by
                # _build_mesh_object regardless of collection nesting
                # depth), not asm_col.objects -- a child that isn't
                # itself "one physical part" recurses into its own
                # nested sub-collection (e.g. "Assembly (PA_hinge_h1)"),
                # so its objects never land directly in asm_col and a
                # diff against asm_col.objects would miss them entirely.
                per_child_objs = {}
                for ch in node["children"]:
                    before = len(self._created_objects)
                    self._build_node(ch, asm_col, world)
                    new_objs = self._created_objects[before:]
                    if new_objs:
                        per_child_objs[id(ch)] = new_objs

                if (self._hide_feature_parts and bore_only_children
                        and len(target_candidates) == 1):
                    target_objs = per_child_objs.get(id(target_candidates[0]), [])
                    bore_objs = [o for ch in bore_only_children
                                for o in per_child_objs.get(id(ch), [])]
                    if len(target_objs) == 1 and bore_objs:
                        self._join_groups.append([target_objs[0]] + bore_objs)
                return
            for ch in node["children"]:
                self._build_node(ch, parent_col, world)
            return

        # If this wrapper node has no direct geometry and all children have
        # clean CV part names, collapse: group each part type into one shared
        # collection inside this node's OWN collection (not parent_col --
        # otherwise same-named parts from sibling nodes elsewhere in the
        # file would pool together and lose their association with `node`).
        # Children here still go through _build_node individually (so
        # feature/bore dispatch above applies to them); same-type objects
        # are then joined with the operator afterward.
        if (not node["ginst"] and node["children"] and
                all(not ch["name"].startswith(("VN_", "PA_"))
                    for ch in node["children"])):
            own_col = self._get_or_create_col(parent_col, name)
            per_type = {}
            for ch in node["children"]:
                # Grouped by _collection_key (bore sub-types share one
                # "Bores" collection) for where the object actually lands;
                # per_type below stays keyed by the real ch["name"] so the
                # bore-absorption classification just below is unaffected.
                part_col = self._get_or_create_col(own_col, self._collection_key(ch["name"]))
                before = {o.name for o in part_col.objects}
                self._build_node(ch, part_col, world)
                new_objs = [o for o in part_col.objects if o.name not in before]
                if new_objs:
                    per_type.setdefault(ch["name"], []).extend(new_objs)

            # BORE operations (e.g. "_HGAVBORE" hinge-cup/screw bores) that
            # land here as flat siblings -- not nested inside a PA_-wrapped
            # panel the way "Fix Hidden Dado"-style features normally are
            # -- belong to whichever structural part they're drilled into
            # (typically a door/drawer-front slab like "S_DSLAB"), not to
            # any hardware siblings also grouped here (e.g. "_HGARM"/
            # "_HGBASE" hinge arm/base, which are physical hinge parts, not
            # cuts). If exactly one non-feature, childless (leaf-type)
            # sibling exists at this level with exactly one object, absorb
            # every bore-type object here into it via an operator join --
            # DADO/NOTCH never reach this dict at all when hidden (they're
            # diverted to "CV Hidden Features" inside the _build_node call
            # above before part_col is ever populated).
            wrapper_type_names = {ch["name"] for ch in node["children"] if ch["children"]}
            bore_types = [t for t in per_type
                          if _is_feature_name(t) and not _is_hidden_feature_name(t)]
            target_types = [t for t in per_type
                            if t not in bore_types and t not in wrapper_type_names]
            absorbed = set()
            if bore_types and len(target_types) == 1 and len(per_type[target_types[0]]) == 1:
                target_obj = per_type[target_types[0]][0]
                bore_objs = [o for t in bore_types for o in per_type[t]]
                self._join_groups.append([target_obj] + bore_objs)
                absorbed = set(bore_types) | {target_types[0]}

            for tname, objs in per_type.items():
                if tname in absorbed:
                    continue
                if len(objs) > 1:
                    self._join_groups.append(objs)
            return

        has_ch = bool(node["children"])
        if has_ch:
            sub = bpy.data.collections.new(name)
            parent_col.children.link(sub)
            cur = sub
        else:
            cur = parent_col

        for inst in node["ginst"]:
            dec = self._decode_geometry(inst["gid"])
            obj, _ = self._build_mesh_object(name, [(dec, world, inst["mmap"])])
            if obj:
                cur.objects.link(obj)

        for ch in node["children"]:
            self._build_node(ch, cur, world)

        for lid in node.get("linst", []):
            ldict = self.p.lights.get(lid)
            if ldict is None:
                _log("WARNING: light '%s' not found" % lid)
                continue
            cur.objects.link(self._make_light(ldict, name, world))

    # ── post-processing ──────────────────────────────────────────────────

    def join_part_groups(self, context):
        """Operator-join the (rare) per-type groups queued by the clean-
        named collapse path in _build_node. Physical parts no longer come
        through here -- they're built merged from the start."""
        if not self._join_groups:
            return
        vl = context.view_layer
        prev = vl.objects.active
        for o in list(context.selected_objects):
            o.select_set(False)
        for group in self._join_groups:
            valid = [o for o in group if o.name in vl.objects]
            if len(valid) < 2:
                continue
            vl.objects.active = valid[0]
            for o in valid:
                o.select_set(True)
            try:
                bpy.ops.object.join()
                self._joined_objects.append(valid[0])
            except Exception as exc:
                _log("join failed: %s" % exc)
            valid[0].select_set(False)
        vl.objects.active = prev

    def weld_seams(self):
        """Weld the duplicate seam vertices merging leaves behind (each
        face/edgeband/bore was built from its own separate vertex list, so
        coincident points aren't shared until welded)."""
        if self._merge_distance and self._joined_objects:
            self._merge_by_distance(self._joined_objects)

    def _merge_by_distance(self, objs):
        """Weld vertices within self._merge_distance of each other on each
        object, via bmesh (no edit-mode/context override needed). This is
        the automated equivalent of Mesh > Clean Up > Merge by Distance,
        run only on the objects that were merged/joined."""
        dist = self._merge_distance
        total_removed = 0
        for obj in objs:
            if obj.type != "MESH":
                continue
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            before = len(bm.verts)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
            removed = before - len(bm.verts)
            if removed:
                bm.to_mesh(obj.data)
                obj.data.update()
                total_removed += removed
            bm.free()
        if total_removed:
            _log("Merge by distance: welded %d duplicate vertices across %d objects" % (
                total_removed, len(objs)))

    def clean_topology(self, angle_limit=math.radians(5.0)):
        """Optional post-process, off by default: on each merged object,
        dissolve edges between near-coplanar faces (Limited Dissolve) and
        merge the remaining triangles into quads (Tris to Quads). Bore
        holes are tessellated by CV as fans of small triangles; on the
        flat panel area around them this collapses a lot of redundant
        triangulation into far fewer faces.

        This only removes/merges edges -- it does not move any vertex
        position -- but it DOES change how many faces bound a hole (e.g. a
        16-gon bore wall may become fewer, larger faces), so it's opt-in
        rather than automatic: leave it off if something downstream
        depends on the exact triangulation Cabinet Vision exported."""
        objs = self._joined_objects
        if not objs:
            return
        n_faces_before = n_faces_after = 0
        for obj in objs:
            if obj.type != "MESH":
                continue
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            n_faces_before += len(bm.faces)
            bmesh.ops.dissolve_limit(
                bm, angle_limit=angle_limit, use_dissolve_boundaries=False,
                verts=bm.verts, edges=bm.edges)
            bmesh.ops.join_triangles(
                bm, faces=bm.faces,
                angle_face_threshold=math.radians(40),
                angle_shape_threshold=math.radians(40))
            n_faces_after += len(bm.faces)
            bm.to_mesh(obj.data)
            bm.free()
            obj.data.update()
        _log("Clean topology: %d -> %d faces across %d merged objects" % (
            n_faces_before, n_faces_after, len(objs)))

    def flip_uvs(self):
        """Flip the V axis of the first UV layer on every mesh object
        created by THIS import (previously this flipped every mesh already
        in the scene too)."""
        for obj in self._created_objects:
            if obj.type != "MESH" or not obj.data.uv_layers:
                continue
            layer = obj.data.uv_layers[0].data
            arr = np.empty(len(layer) * 2, dtype=np.float32)
            layer.foreach_get("uv", arr)
            arr[1::2] = 1.0 - arr[1::2]
            layer.foreach_set("uv", arr)

    def mark_hard_edge_seams(self, angle_limit=math.radians(40.0)):
        """On by default: mark every edge whose two adjacent faces meet at
        more than `angle_limit` as a UV seam, on every mesh object created
        by this import. Cabinet Vision panels are almost entirely
        rectilinear, so this lands seams right where a face genuinely
        turns a corner -- panel face to edgeband, panel face to a merged
        bore's cylinder wall, and so on -- exactly where a later UV
        unwrap (Smart UV Project or otherwise) should be cutting anyway,
        without needing to hand-mark seams on every part.

        Boundary edges (only one adjacent face -- an open edge where
        nothing else was merged in, e.g. a lone unmerged panel) are left
        alone: there's no second face to compare an angle against, and
        marking every open boundary as a seam would over-segment simple
        parts into far more islands than needed."""
        n_seams = n_edges = 0
        for obj in self._created_objects:
            if obj.type != "MESH":
                continue
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            n_edges += len(bm.edges)
            for e in bm.edges:
                if len(e.link_faces) == 2 and e.calc_face_angle() > angle_limit:
                    e.seam = True
                    n_seams += 1
            bm.to_mesh(obj.data)
            bm.free()
            obj.data.update()
        _log("Mark hard edges as seams: %d/%d edges marked across %d objects" % (
            n_seams, n_edges, len(self._created_objects)))

    # ── hidden dado/notch cutting ───────────────────────────────────────
    #
    # Some panels (typically uprights, with a dado/groove cut into their
    # *interior* face rather than a rabbet cut from an edge) import with
    # the cut invisible. Cabinet Vision correctly builds the recessed
    # floor and side walls of the pocket -- that geometry genuinely exists
    # in the file -- but exports the panel's own large flat face without a
    # hole for it, so the real pocket sits, unseen, directly behind a
    # solid, unbroken face. The signature is distinctive: a large flat
    # face and a much smaller, near-coincident, *parallel* face (the
    # pocket's floor) whose footprint is fully contained inside the big
    # face's footprint. Where that pattern is found, this cuts away just
    # the covering portion of the big face so the pocket already modeled
    # behind it becomes visible -- it does not invent any new geometry.

    def _planar_face_groups(self, bm, normal_round=2, offset_round=4):
        """Cluster bmesh faces into coplanar, co-facing groups keyed by
        (rounded unit normal, rounded plane offset)."""
        groups = {}
        for f in bm.faces:
            n = f.normal
            if n.length < 1e-6:
                continue
            n = n.normalized()
            nkey = (round(n.x, normal_round), round(n.y, normal_round), round(n.z, normal_round))
            offset = round(n.dot(f.verts[0].co), offset_round)
            g = groups.setdefault((nkey, offset), {"normal": n, "faces": [], "area": 0.0})
            g["faces"].append(f)
            g["area"] += f.calc_area()
        return groups

    @staticmethod
    def _perp_basis(normal):
        """Return two unit vectors spanning the plane perpendicular to `normal`."""
        n = normal.normalized()
        ref = mathutils.Vector((1.0, 0.0, 0.0))
        if abs(n.dot(ref)) > 0.9:
            ref = mathutils.Vector((0.0, 1.0, 0.0))
        u = n.cross(ref).normalized()
        v = n.cross(u).normalized()
        return u, v

    def _find_hidden_dado(self, bm, max_depth=0.05, max_area_ratio=0.25, containment_margin=0.01):
        """Find one (bridging face, recessed floor) pair matching the hidden-
        dado signature described above, or None. `max_depth` bounds how far
        behind the big face the recessed floor can sit (a dado/notch is
        shallow relative to the panel it's cut into); `max_area_ratio`
        bounds how small the floor must be relative to the face covering
        it; `containment_margin` allows a hair of slack when checking that
        the floor's footprint sits inside the big face's footprint."""
        groups = self._planar_face_groups(bm)
        by_normal = {}
        for (nkey, offset), g in groups.items():
            by_normal.setdefault(nkey, []).append((offset, g))

        for entries in by_normal.values():
            if len(entries) < 2:
                continue
            entries.sort(key=lambda e: -e[1]["area"])
            bridge_offset, bridge = entries[0]
            if bridge["area"] < 1e-6:
                continue
            u_axis, v_axis = self._perp_basis(bridge["normal"])
            origin = bridge["faces"][0].verts[0].co.copy()
            b_us = [(v.co - origin).dot(u_axis) for f in bridge["faces"] for v in f.verts]
            b_vs = [(v.co - origin).dot(v_axis) for f in bridge["faces"] for v in f.verts]
            b_bounds = (min(b_us), max(b_us), min(b_vs), max(b_vs))

            for floor_offset, floor in entries[1:]:
                depth = abs(floor_offset - bridge_offset)
                if depth < 1e-5 or depth > max_depth:
                    continue
                if floor["area"] > bridge["area"] * max_area_ratio:
                    continue
                f_us = [(v.co - origin).dot(u_axis) for f in floor["faces"] for v in f.verts]
                f_vs = [(v.co - origin).dot(v_axis) for f in floor["faces"] for v in f.verts]
                f_bounds = (min(f_us), max(f_us), min(f_vs), max(f_vs))
                if (f_bounds[0] < b_bounds[0] - containment_margin or
                        f_bounds[1] > b_bounds[1] + containment_margin or
                        f_bounds[2] < b_bounds[2] - containment_margin or
                        f_bounds[3] > b_bounds[3] + containment_margin):
                    continue  # floor isn't inside the big face's footprint -- not a match
                return {
                    "normal": bridge["normal"], "offset": bridge_offset,
                    "u_axis": u_axis, "v_axis": v_axis, "origin": origin,
                    "bridge_bounds": b_bounds,
                    "u_lo": f_bounds[0], "u_hi": f_bounds[1],
                    "v_lo": f_bounds[2], "v_hi": f_bounds[3],
                }
        return None

    def _cut_one_hidden_dado(self, bm, match, edge_margin=1e-4):
        """Bisect the bridging face group along the recessed floor's
        footprint boundary (skipping any side that already coincides with
        the panel's own edge) and delete the portion directly over the
        floor, exposing it."""
        normal, offset = match["normal"], match["offset"]
        u_axis, v_axis, origin = match["u_axis"], match["v_axis"], match["origin"]
        nkey = (round(normal.x, 2), round(normal.y, 2), round(normal.z, 2))

        def bridge_faces_now():
            return [f for f in bm.faces
                    if f.normal.length > 1e-6
                    and (round(f.normal.normalized().x, 2), round(f.normal.normalized().y, 2),
                         round(f.normal.normalized().z, 2)) == nkey
                    and abs(normal.dot(f.verts[0].co) - offset) < 1e-4]

        bb = match["bridge_bounds"]
        cuts = (
            (u_axis, match["u_lo"], bb[0]), (u_axis, match["u_hi"], bb[1]),
            (v_axis, match["v_lo"], bb[2]), (v_axis, match["v_hi"], bb[3]),
        )
        for axis, bound, edge in cuts:
            if abs(bound - edge) < edge_margin:
                continue  # the notch already reaches the panel's own edge here
            plane_co = origin + axis * bound
            geom = list(bm.verts) + list(bm.edges) + bridge_faces_now()
            bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6,
                                   plane_co=plane_co, plane_no=axis,
                                   clear_inner=False, clear_outer=False)
            bm.faces.ensure_lookup_table()

        to_delete = []
        for f in bridge_faces_now():
            verts = [v.co for v in f.verts]
            cu = sum((v - origin).dot(u_axis) for v in verts) / len(verts)
            cv = sum((v - origin).dot(v_axis) for v in verts) / len(verts)
            if (match["u_lo"] - edge_margin < cu < match["u_hi"] + edge_margin and
                    match["v_lo"] - edge_margin < cv < match["v_hi"] + edge_margin):
                to_delete.append(f)
        n = len(to_delete)
        bmesh.ops.delete(bm, geom=to_delete, context="FACES")
        return n

    def fix_hidden_dado_faces(self, max_per_object=8):
        """Run on each merged physical part: repeatedly find and open up
        hidden dado/notch pockets (see _find_hidden_dado) until none are
        left or `max_per_object` cuts have been made, whichever comes
        first -- a panel can have more than one such pocket."""
        total_cuts = total_objs = 0
        for obj in self._joined_objects:
            if obj.type != "MESH":
                continue
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            cuts_here = 0
            for _ in range(max_per_object):
                match = self._find_hidden_dado(bm)
                if not match:
                    break
                cuts_here += self._cut_one_hidden_dado(bm, match)
            if cuts_here:
                bm.to_mesh(obj.data)
                obj.data.update()
                total_cuts += cuts_here
                total_objs += 1
            bm.free()
        if total_cuts:
            _log("Fix hidden dado/notch faces: opened %d face(s) across %d object(s)" % (
                total_cuts, total_objs))


# ──────────────────────────────────────────────────────────────
#  Operator
# ──────────────────────────────────────────────────────────────

class IMPORT_OT_cabinet_vision_dae(Operator, ImportHelper):
    """Import a Cabinet Vision Collada (.dae) file"""
    bl_idname = "import_scene.cabinet_vision_dae"
    bl_label = "Import Cabinet Vision DAE"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".dae"
    filter_glob: StringProperty(default="*.dae", options={"HIDDEN"})
    flip_uv_v: BoolProperty(
        name="Flip UV (V axis)",
        description="Enable if textures appear upside-down",
        default=False)
    join_parts: BoolProperty(
        name="Join Panel Parts",
        description=("Merge each physical part's faces, edgebanding, and "
                     "boring/dado into a single selectable object"),
        default=True)
    merge_by_distance: BoolProperty(
        name="Merge Vertices by Distance",
        description=("After joining, weld duplicate seam vertices left "
                     "over from joining independently-tessellated faces, "
                     "edgebanding and boring (equivalent to Mesh > Clean "
                     "Up > Merge by Distance, run automatically)"),
        default=True)
    merge_distance: FloatProperty(
        name="Distance",
        description="Vertices closer than this are welded together",
        default=0.0001, min=0.0, precision=5, unit="LENGTH")
    clean_topology: BoolProperty(
        name="Clean Topology (Limited Dissolve + Tris to Quads)",
        description=("On each joined object, dissolve edges between near-"
                     "coplanar triangulated faces and merge remaining "
                     "triangles into quads. Off by default: this changes "
                     "how many faces bound a bore hole (though it never "
                     "moves a vertex), which matters if anything "
                     "downstream depends on CV's exact triangulation"),
        default=False)
    fix_hidden_dados: BoolProperty(
        name="Fix Hidden Dado/Notch Faces",
        description=("Cabinet Vision sometimes exports a panel's dado/"
                     "notch pocket correctly, but leaves the panel's own "
                     "flat face uncut over it, hiding the pocket behind "
                     "solid material. Find that pattern (a big flat face "
                     "fully covering a much smaller, near-coincident, "
                     "parallel face) and cut the covering portion away. "
                     "Off by default since it deletes geometry -- turn "
                     "on if a part looks like it's missing a dado/notch "
                     "cut that should be visible"),
        default=False)
    hide_feature_parts: BoolProperty(
        name="Hide Dado/Notch Feature Geometry",
        description=("Cabinet Vision nests DADO/NOTCH feature geometry "
                     "(e.g. 'UBDADO') inside the panel it cuts into. On, "
                     "that geometry is always routed to the hidden 'CV "
                     "Hidden Features' collection instead of being fused "
                     "into the panel's merged mesh, since it's typically "
                     "redundant duplicate geometry. BORE (boring/"
                     "drilling) geometry is never affected by this and "
                     "always stays merged and visible. Turn off if a "
                     "panel's dado/notch pocket only exists as separate "
                     "geometry under one of these feature nodes and you "
                     "rely on 'Fix Hidden Dado Faces' to expose it -- with "
                     "this on, there's nothing left in the merged mesh "
                     "for that fix to find"),
        default=True)
    mark_hard_edges: BoolProperty(
        name="Mark Hard Edges as Seams",
        description=("Mark every edge where two adjacent faces meet at "
                     "more than ~40 degrees as a UV seam (panel face to "
                     "edgeband, panel face to a merged bore's cylinder "
                     "wall, etc.), so a later UV unwrap has sensible cut "
                     "lines to work from without hand-marking every part. "
                     "Only sets edge seam flags -- doesn't move any "
                     "geometry or touch existing UVs by itself"),
        default=True)

    def execute(self, context):
        import time
        _log("=" * 60)
        _log("Importing:", self.filepath)
        t0 = time.perf_counter()
        warnings = []
        try:
            p = DAEParser(self.filepath)
            p.parse()
            dist = self.merge_distance if self.merge_by_distance else 0.0
            b = BlenderBuilder(p, report_fn=warnings.append,
                               join_parts=self.join_parts, merge_distance=dist,
                               hide_feature_parts=self.hide_feature_parts)
            b.build(context)
            b.join_part_groups(context)
            b.weld_seams()
            if self.clean_topology:
                b.clean_topology()
            if self.fix_hidden_dados:
                b.fix_hidden_dado_faces()
            if self.flip_uv_v:
                b.flip_uvs()
            if self.mark_hard_edges:
                b.mark_hard_edge_seams()
            for w in warnings:
                self.report({"WARNING"}, w)
            msg = "Cabinet Vision import: %d geometries, %d materials in %.2fs" % (
                len(p.geometries), len(p.materials), time.perf_counter() - t0)
            _log(msg)
            _log("=" * 60)
            self.report({"INFO"}, msg)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            self.report({"ERROR"}, "Import failed: %s" % exc)
            return {"CANCELLED"}
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "join_parts")
        layout.prop(self, "merge_by_distance")
        dist_row = layout.row()
        dist_row.enabled = self.merge_by_distance
        dist_row.prop(self, "merge_distance")
        layout.prop(self, "clean_topology")
        layout.prop(self, "fix_hidden_dados")
        layout.prop(self, "hide_feature_parts")
        layout.prop(self, "flip_uv_v")
        layout.prop(self, "mark_hard_edges")


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
