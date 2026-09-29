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

- Neighbours of an image: up to K images within R metres (defaults 8 and 40 m), plus, with *Use shot
  order*, the two shots either side from the same `deviceId` taken within 2 minutes. Shot time comes
  from a capture-time metadata field or the timestamp in a DJI file name
  (`DJI_YYYYMMDDhhmmss_nnnn`); upload time (`createdAt`) is never used, because an upload batch shares
  one folder whether or not it is right.
- Each neighbour votes for its current folder. An image is flagged when at least 3 neighbours voted,
  the winning folder is not its own, and the winner has at least the agreement share (default 60%).
  Images without GPS can still be flagged through shot order.
- Moves are sent as `move` mutations in batches of 50 per target folder. Undo sends each image back
  to the folder it was in before the run.

# Media Drive API

GraphQL endpoint `https://mediadrive-api.unleashlive.com/graphql`, `Authorization: Bearer <PAT>`.
Queries used: `get(item:{id})`, `list(location, limit, nextToken)`; items carry `parentId`, `location`,
`createdAt`, `metadata { gpslat gpslng gpsalt ... }`. Move mutation: `move(moveItems:[{id}], to:{id})`.
