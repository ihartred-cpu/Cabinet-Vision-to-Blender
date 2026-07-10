# Cabinet Vision to Blender

A Blender add-on that imports Cabinet Vision's Collada (`.dae`) exports as a clean, organized scene — correct geometry, materials, UVs, and lighting, with cabinets rebuilt as sensible, editable objects instead of a pile of disconnected meshes.

Most Collada importers, including Blender's built-in one, just dump the raw scene graph: every face, edgeband, and bore/dado fragment lands as its own disconnected object. This add-on understands Cabinet Vision's specific export structure, so it reconstructs what CV actually meant:

- **Joined, welded parts** — each panel's faces, edgebanding, and boring/dado merge into one selectable object, with seams welded automatically.
- **Assembly-aware collections** — parts are grouped and named after their actual CV assembly (e.g. "Base Cabinet Assembly"), instead of pooling same-named parts from across the whole file.
- **Hardware-aware bore handling** — bores exported as loose siblings (e.g. hinge bores) are matched to the correct part rather than hinge hardware; an opt-in fix can also expose dado/notch pockets CV leaves hidden behind an uncut face.
- **Fast on real jobs** — geometry is decoded and cached once per instance instead of re-parsed, parts build directly into their final mesh instead of via temp-object-then-join, and heavy lifting runs through numpy.
- **Optional cleanup pass** — an off-by-default topology cleanup for over-triangulated faces; left off because it changes bore-hole triangulation.

Tested in Blender 4.5.7 and 5.1+ (should work back to 4.0). CV's `.dae` export must be UTF-8, not ANSI/Unicode.

![Cabinet Vision](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-06-30%20123044.png)

![Blender](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-06-30%20123128.png)

![Blender](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-06-30%20124303.png)

![CV](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-07-01%20094204.png)

![Blender](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-07-06%20095110.png)

## Changelog

### 1.11.0
- 1.10.0's bore-absorption only covered bores exported as flat siblings under a bare (non-`PA_`) grouping node. Cabinet Vision often instead wraps a bore in its own `PA_`+`VN_` pair -- e.g. hinge bores ("_HGAVBORE"/"_HGCVBORE") showing up under their own "Molding_Door_NN" wrapper, sibling to the door's real "Door_NN" slab wrapper and to separate hinge-hardware ("Widget_Arm"/"Widget_Base_Plate") wrappers -- which 1.10.0 didn't reach. Extended the same "exactly one structural target absorbs every bore-only sibling" logic to this assembly level too, additionally excluding any "Widget"-labeled sibling (hinge arm/base hardware) from ever being a valid absorption target.

### 1.10.0
- Bore operations (e.g. "_HGAVBORE" hinge-cup/screw bores) that Cabinet Vision exports as flat siblings of the part they're drilled into -- rather than nested inside it the way panel cuts normally are -- previously stayed unmerged, floating as their own separate objects instead of becoming part of the door/drawer-front they belong to. When exactly one non-feature leaf part exists among such a group of siblings, every bore-type object in that group is now joined into it; hinge hardware and any ambiguous (multiple-candidate) groupings are left untouched to avoid an incorrect merge.

### 1.9.1
- "Hide Dado/Notch Feature Geometry" (1.9.0) was also catching BORE-named nodes, hiding boring/drilling geometry along with the dado/notch pockets. Split the keyword set so hiding only ever applies to DADO/NOTCH; BORE geometry always stays merged and visible in the panel mesh, same as before 1.9.0.

### 1.9.0
- Fixed a real bug (present since 1.4.0's part-joining, not something 1.8.0's rewrite introduced): BORE/DADO/NOTCH feature geometry nested inside the panel it cuts into (the normal, documented case -- e.g. "UBDADO", "_HGAVBORE") was being silently fused into that panel's merged mesh instead of ever reaching the "hide standalone feature objects" logic added in 1.7.0, which only ever fired for the rarer case of a feature exported as an un-nestable orphan sibling. New "Hide Bore/Dado/Notch Feature Geometry" checkbox (on by default) now catches the nested case too, routing that geometry straight to the hidden "CV Hidden Features" collection instead of merging it in.

### 1.8.0
- Performance/organization rewrite. Import is much faster on large files: each geometry is decoded from XML exactly once and cached, instead of being fully re-parsed for every instance that references it (Cabinet Vision instances the same panel/bore geometry many times across a job). Physical parts are assembled directly into a single mesh at build time, instead of creating dozens of temporary objects per part and running the slow, selection-based Join operator on each group (the operator join is now kept only for the rarer clean-named collapse path). UVs and material indices are written with `foreach_set` instead of per-loop Python assignment, and vertex transforms go through numpy. The recursive fallback texture search walks the export directory once and caches a filename index, instead of re-walking the tree for every missing texture.
- Behavior fixes: "Flip UV (V axis)" now only affects objects created by this import -- it used to flip every mesh already in the scene. Unknown-material slots share one "CV_Unknown" material instead of creating a new datablock per object. Import errors now print a full traceback to the console.

### 1.7.0
- Some panels (typically uprights with a dado/groove cut into their interior face, as opposed to a rabbet cut from an edge) import with the cut invisible: Cabinet Vision correctly builds the recessed floor and side walls of the pocket, but exports the panel's own large flat face without a hole for it, so the real pocket geometry sits, unseen, directly behind a solid unbroken face. New opt-in "Fix Hidden Dado/Notch Faces" checkbox scans each joined part for exactly this signature (a large flat face fully covering a much smaller, near-coincident, parallel face) and cuts away just the covering portion, exposing the pocket that was already there. Off by default since it deletes geometry -- turn it on when a part looks like it's missing a dado/notch that should be visible.
- Standalone DADO/NOTCH/BORE reference objects that Cabinet Vision emits as their own siblings (rather than nested inside the one panel they cut into, so they can't be joined into it) previously imported as ordinary visible parts cluttering the scene; they now move into the same hidden collection as bore hardware.

### 1.6.0
- Collections now preserve each part's association with its assembly. Previously, once part names were "clean" (no `VN_`/`PA_` prefix), same-named parts from every assembly in the whole file (every "RU", every "LU", ...) were pooled into one shared collection, losing which cabinet/countertop/molding run each part belonged to. Each physical assembly (identified as the shallowest point where distinct parts appear as direct children) now gets its own collection — named from Cabinet Vision's own label where available (e.g. "Base Cabinet Assembly") — with its part collections nested inside it.
- Fixed the "Merge Vertices by Distance" toggle not being visible/reachable in the import options panel: it shared a row with the distance field, which could get squeezed out of a narrow panel. Each option now gets its own full-width row.

### 1.5.0
- Added an optional "Clean Topology" post-process (Limited Dissolve + Tris to Quads) on joined objects, off by default. Removes redundant edges on flat, near-coplanar triangulated faces without moving vertex positions. Left off by default because it changes face/edge topology near bore holes, which matters if anything downstream depends on the exact triangulation CV exported.

### 1.4.1
- Added automatic "Merge Vertices by Distance" after joining, to weld the duplicate seam vertices that joining leaves behind (each face/edgeband/bore was built from its own separate vertex list, so coincident points aren't shared until merged).

### 1.4.0
- Physical parts (faces + edgebanding + boring/dado) are now recognized as a single unit and joined into one selectable object per panel instance, instead of staying as many separate un-joined objects.

### 1.3.0
- Baseline release: correct geometry, materials, UVs, and hierarchy on import.
