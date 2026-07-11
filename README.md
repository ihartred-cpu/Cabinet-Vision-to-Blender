# Cabinet Vision to Blender

Cabinet Vision, in its wisdom, exports to Collada (`.dae`) — a fine, uh, *time-honored* choice — and the results are about what you'd expect: every face, edgeband strip, and dado fragment arrives as its own disconnected object, with zero regard for which panel or cabinet it belongs to. This add-on makes the best of it: CV's `.dae` exports come in as a proper Blender scene — correct geometry, materials, UVs, lighting — with cabinets rebuilt as sensible, editable objects instead of a debris field of meshes.

## Features

- **Joined parts** — each panel's faces, edgebanding, and boring/dado become one selectable object, seams welded.
- **Assembly-aware collections** — parts grouped under their cabinet/countertop/molding run, named from CV's own label (e.g. "Base Cabinet Assembly"); CV's redundant wrapper levels get collapsed instead of fragmenting one assembly across duplicates.
- **Hardware-aware bore handling** — bores exported as flat siblings get absorbed into the correct structural panel (never into hinge hardware), with UVs corrected to match. Unabsorbed bores share one "Bores" collection per assembly; dado/notch pockets route to a hidden collection by default; boring/drilling geometry always stays merged and visible.
- **Hidden-feature repair** — opt-in pass that cuts open dado/notch pockets CV built correctly but covered with a solid face.
- **Built for CV's real export sizes** — geometry decoded from XML once and cached, parts assembled directly instead of spawning temp objects for Join, UVs/materials/transforms written in bulk (numpy/`foreach_set`). Large jobs stay fast.
- **Optional clean topology pass** — Limited Dissolve + Tris to Quads, off by default (it changes bore-hole triangulation).
- **Hard edges marked as UV seams** — on by default; seams at >~40° face angles give a later unwrap sensible cut lines without hand-marking every part.

Tested in Blender 4.5.7 and 5.1+, should work back to 4.0. CV `.dae` export must be saved as UTF-8, not ANSI/Unicode.

![Cabinet Vision](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-06-30%20123044.png)

![Blender](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-06-30%20123128.png)

![Blender](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-06-30%20124303.png)

![CV](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-07-01%20094204.png)

![Blender](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-07-06%20095110.png)

## Changelog

### 1.14.0
New opt-in "Mark Hard Edges as Seams" post-process (on by default): marks every edge where adjacent faces meet at >~40° as a UV seam, on every mesh the import creates. Gives a later UV unwrap sensible cut lines without hand-marking parts. Boundary edges are left alone; only sets seam flags.

### 1.13.0
Assembly collections (e.g. "Tall Cabinet Assembly") are now reused instead of fragmenting across ".001", ".002", etc. when CV stacks anonymous wrapper levels. Unabsorbed bore sub-types now share one "Bores" collection per assembly instead of each sub-type code getting its own.

### 1.12.0
Fixed mangled UVs on panels with shelf-pin/hinge bores: the existing 90° UV correction only checked the merged object's own name for a "BORE" suffix, which stopped firing once bores started joining directly into panel meshes (named "TO"/"SL"/"BT", not the bore). Now applied per contributing instance instead.

### 1.11.0
Extended bore-absorption to bores wrapped in their own `PA_`+`VN_` pair (e.g. hinge bores under a "Molding_Door_NN" wrapper sibling to the door's real slab wrapper), not just bare-sibling bores. "Widget"-labeled hinge hardware is explicitly excluded as an absorption target.

### 1.10.0
Bore operations exported as flat siblings of the part they're drilled into (rather than nested, the normal case) now get joined into that part when exactly one non-feature leaf part exists among the siblings. Hinge hardware and ambiguous groupings are left untouched.

### 1.9.1
"Hide Dado/Notch Feature Geometry" was also catching BORE nodes. Split the keyword set so hiding only applies to DADO/NOTCH; BORE geometry always stays merged and visible.

### 1.9.0
Fixed a bug present since 1.4.0: nested BORE/DADO/NOTCH feature geometry was being silently fused into the panel mesh instead of reaching the "hide standalone feature objects" logic. New "Hide Bore/Dado/Notch Feature Geometry" checkbox (on by default) now catches the nested case, routing it to a hidden "CV Hidden Features" collection.

### 1.8.0
Performance/organization rewrite: geometry decoded from XML once and cached instead of re-parsed per instance; parts assembled directly into a single mesh instead of temp objects + Join operator; UVs/material indices via `foreach_set`, transforms via numpy; texture search caches a filename index instead of re-walking the tree. Also: "Flip UV (V axis)" now only affects objects from this import; unknown materials share one "CV_Unknown" slot; import errors print a full traceback.

### 1.7.0
New opt-in "Fix Hidden Dado/Notch Faces" checkbox: cuts away a covering face left over a pocket CV built correctly but didn't expose. Off by default since it deletes geometry. Standalone DADO/NOTCH/BORE sibling objects that can't be joined now move into the hidden collection instead of cluttering the scene.

### 1.6.0
Collections now preserve each part's assembly association instead of pooling every same-named part file-wide. Each assembly gets its own collection, named from CV's label where available. Fixed "Merge Vertices by Distance" toggle being squeezed out of the import options panel.

### 1.5.0
Added optional "Clean Topology" post-process (Limited Dissolve + Tris to Quads), off by default — changes topology near bore holes.

### 1.4.1
Added automatic "Merge Vertices by Distance" after joining, to weld duplicate seam vertices.

### 1.4.0
Physical parts (faces + edgebanding + boring/dado) now join into one selectable object per panel instance.

### 1.3.0
Baseline release: correct geometry, materials, UVs, and hierarchy on import.
