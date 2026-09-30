# Matching logic

- Images are projected to local metres (equirectangular about each corridor's first vertex).
- Each image is assigned to the nearest corridor segment whose buffer it falls inside; bridged
  segments (long gaps between known waypoints) use the wider bridge buffer. Ties prefer the closest line.
- Status per image: **Correct** (on corridor, in that corridor's folder), **Misfiled** (on corridor,
  elsewhere), **Stray** (in a corridor folder but off every corridor), **On corridor, no folder set**,
  **Time-only** (no GPS, inside the time window), **No GPS**, **Other**.
- Coverage: the corridor is cut into bins along chainage; bins with no correctly filed image are merged
  into gaps, and the number of misfiled photos that fall in each gap is reported.
- Site maps: control points (drawing x,y in PDF points; lat/lng) solve a similarity (2 points) or
  least-squares affine (3 or more) transform. Residuals are reported per point. Vertices inside excluded
  rectangles (detail insets, legend, title block) are dropped before the transform.

# Neighbour review

- The unit that moves is either the image's own folder (a pole folder, moved whole into a feeder) or
  a single image. Votes are about where a unit sits: the pole's parent (feeder), or the image's folder.
- Neighbours of an image: up to K images from other units within R metres (defaults 8 and 40 m), plus,
  with *Use shot order*, the nearest two shots either side from other units of the same `deviceId`
  within 5 minutes. Shot time comes from a capture-time metadata field or the timestamp in a DJI file
  name (`DJI_YYYYMMDDhhmmss_nnnn`); upload time (`createdAt`) is never used, because an upload batch
  shares one folder whether or not it is right.
- Each neighbour votes for the group its unit is in, and votes are pooled over the unit's images. A
  unit is flagged when it has at least 3 votes, the winner is not its current group, and the winner
  has at least the agreement share (default 60%). A pole is *mixed* when under 70% of its own images
  agree with the winner.
- Flags are committed most-confident first, recounting after each with that unit in its new group, so
  a misfiled pole does not drag a correctly filed neighbour (for example at the end of a line) with it.
- Moves are sent as `move` mutations in batches of 50 per destination. Undo sends each unit back to
  the folder it was in before the run.
- Corridor analysis counts an image as in a corridor's target folder when the target is any ancestor
  of the image (so a feeder target covers its pole folders).

# Split captures

- Shots are grouped per `deviceId` (or all together with *Same drone only* off) and sorted by shot
  time. A shot joins the current burst when it is at most the gap (default 60 s) after the previous
  shot and, when it has GPS, within the distance (default 20 m) of the burst's first GPS shot; the
  distance check stops a mission's poles chaining into one burst.
- A burst with shots in two or more folders is a split. The suggested destination is the folder with
  most of the burst's shots (ties go to the folder with more images overall).

# Folder check

- Asset folder: not an Archive (name matches the Archive pattern) or inside one, not a top folder,
  and no sub-folders other than Archives. RGB = images whose name does not match the "not RGB"
  pattern (default `_T\.|_T_`, DJI thermal).
- Spare shots: RGB images in an Archive, loose in a folder with sub-folders, or in an over-full
  asset folder. For a short folder, its own Archive's shots always qualify (score -1 + time gap);
  other spare shots qualify within the time window of the folder's shots (same `deviceId`) and the
  distance of the nearest one, scored time/window + distance/limit.
- Pairs are assigned greedily, best score first: each shot at most once, a folder at most what it is
  short, an over-full folder only down to the expected count. Up to three unassigned alternatives
  are listed per folder, unticked.

# Media Drive API

GraphQL endpoint `https://mediadrive-api.unleashlive.com/graphql`, `Authorization: Bearer <PAT>`.
Queries used: `get(item:{id})`, `list(location, limit, nextToken)`; items carry `parentId`, `location`,
`createdAt`, `metadata { gpslat gpslng gpsalt ... }`. Move mutation: `move(moveItems:[{id}], to:{id})`.
