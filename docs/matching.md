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

# Media Drive API

GraphQL endpoint `https://mediadrive-api.unleashlive.com/graphql`, `Authorization: Bearer <PAT>`.
Queries used: `get(item:{id})`, `list(location, limit, nextToken)`; items carry `parentId`, `location`,
`createdAt`, `metadata { gpslat gpslng gpsalt ... }`. Move mutation: `move(moveItems:[{id}], to:{id})`.
