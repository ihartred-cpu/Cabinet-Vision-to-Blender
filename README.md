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
- Extended 1.10.0's bore-absorption to bores wrapped in their own `PA_`+`VN_` pair (e.g. hinge bores sibling to a door's real slab wrapper), excluding hinge hardware ("Widget_*") as a valid target.

### 1.10.0
- Bores exported as flat siblings of the part they're drilled into (e.g. hinge-cup/screw bores) now join into that part automatically, when exactly one unambiguous target exists.

### 1.9.1
- Fixed 1.9.0's hide logic also catching BORE nodes. Hiding now only applies to DADO/NOTCH; BORE geometry stays merged and visible.

### 1.9.0
- Fixed a long-standing bug: BORE/DADO/NOTCH geometry nested inside its panel was silently merged in instead of reaching the "hide standalone features" logic. New "Hide Bore/Dado/Notch Feature Geometry" option (on by default) routes it to the hidden collection instead.

### 1.8.0
- Performance/organization rewrite: geometry decoded and cached once per unique instance, parts built directly instead of via temp-object-then-join, UVs/material indices/transforms written in bulk via numpy, texture search cached.
- Fixes: UV flip now scoped to this import's own objects, unknown materials share one fallback datablock, import errors log a full traceback.

### 1.7.0
- Added opt-in "Fix Hidden Dado/Notch Faces": exposes dado/notch pockets CV builds correctly but leaves covered by an uncut face.
- Standalone dado/notch/bore reference objects now move to the hidden collection instead of importing as visible clutter.

### 1.6.0
- Collections now preserve each part's assembly association instead of pooling same-named parts across the whole file.
- Fixed "Merge Vertices by Distance" toggle being squeezed out of the import panel.

### 1.5.0
- Added optional "Clean Topology" post-process (Limited Dissolve + Tris to Quads), off by default since it changes bore-hole triangulation.

### 1.4.1
- Added automatic "Merge Vertices by Distance" after joining, to weld duplicate seam vertices left over from merging.

### 1.4.0
- Physical parts (faces + edgebanding + boring/dado) now join into one selectable object per panel instance.

### 1.3.0
- Baseline release: correct geometry, materials, UVs, and hierarchy on import.
