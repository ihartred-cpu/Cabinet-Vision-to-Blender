CV .dae export needs to be in UTF-8 output and not ANSI or unicode

I've only tested in Blender 4.5.7 & 5.1+ but it should work fine back to 4.0

Supports all materials, as well a lighting. 




![Cabinet Vision](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-06-30%20123044.png)

![Blender](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-06-30%20123128.png)

![Blender](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-06-30%20124303.png)

![CV](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-07-01%20094204.png)

![Blender](https://github.com/ihartred-cpu/Cabinet-Vision-to-Blender/blob/main/Screenshot%202026-07-06%20095110.png)

## Changelog

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
