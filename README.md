# Cabinet Vision to Blender

A Blender add-on that imports Cabinet Vision's Collada (`.dae`) exports directly into a clean, organized Blender scene — correct geometry, materials, UVs, and lighting, with cabinets rebuilt as sensible, editable objects instead of a pile of disconnected meshes.

Most Collada importers (including Blender's built-in one) just dump the raw scene graph: every face, edgeband strip, and boring/dado/notch fragment comes in as its own separate object, with no regard for which panel or cabinet it belongs to, and re-decode the same geometry from scratch every time it's instanced. This add-on is built specifically around how Cabinet Vision structures its Collada exports, so it can reconstruct what CV actually meant, and do it fast:

- **Joined parts** — each physical panel's faces, edgebanding, and boring/dado are recognized as one unit and built directly into a single, selectable object, with duplicate seam vertices automatically welded.
- **Assembly-aware collections** — parts stay grouped under their own cabinet/countertop/molding run, in a collection named from Cabinet Vision's own label (e.g. "Base Cabinet Assembly"), instead of every same-named part across the whole file getting pooled together.
- **Hidden-feature repair** — an opt-in "Fix Hidden Dado/Notch Faces" pass catches panels where CV builds a correct recessed pocket but exports an unbroken face covering it, and cuts away just the covering portion so the pocket is actually visible. Standalone dado/notch/bore reference objects that CV emits as loose siblings (rather than nested where they'd get joined) are swept into a hidden collection instead of cluttering the scene.
- **Built for CV's real export sizes** — each geometry is decoded from the XML once and cached, instead of being re-parsed every time CV instances the same panel or bore across a job; parts are assembled directly into their final mesh instead of spawning dozens of temporary objects per part and running Blender's Join operator on each group; and UVs, material indices, and vertex transforms are written in bulk (numpy / `foreach_set`) instead of per-vertex Python loops. Large jobs that would grind a generic importer to a crawl import quickly.
- **Optional clean topology pass** — an off-by-default Limited Dissolve + Tris to Quads step to tidy up flat, over-triangulated faces without moving any vertices.

Tested in Blender 4.5.7 and 5.1+, and should work back to 4.0. Note: the CV `.dae` export must be saved as UTF-8, not ANSI/Unicode.

![Cabinet Vision](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-06-30%20123044.png)

![Blender](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-06-30%20123128.png)

![Blender](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-06-30%20124303.png)

![CV](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-07-01%20094204.png)

![Blender](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-07-06%20095110.png)

## Changelog

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
