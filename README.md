# Media Drive corridor reconciler

A single-page tool for Unleash Live Media Drive that finds images belonging to a corridor
(KML, KMZ, GeoJSON, or a georeferenced 12kV distribution drawing) that were foldered elsewhere,
shows coverage gaps along the line, and exports a move list. Everything runs in the browser;
the Personal Access Token is only sent to `mediadrive-api.unleashlive.com`, and is kept between visits
only if you use **Saved views**: it is then stored in this browser encrypted with AES-GCM under a
password you choose (PBKDF2-SHA256, 310,000 rounds). The password is never stored or sent.

## Use it

Open the hosted page (GitHub Pages, see below) or `index.html` locally, then:

1. **Connect**: paste a `ul_pat_...` token (Profile > Developers) and one or more folder IDs or links (one per line) from the
   cloud.unleashlive.com URL. The scan walks every sub-folder and reads GPS and timestamps.
2. **Add corridors**: KML/KMZ/GeoJSON lines, or waypoint files (Points are connected in sequence,
   file or nearest-neighbour order; over-long segments are flagged as bridges across missing waypoints
   and get a wider buffer). Site-map feeders are added from the **Site map** panel.
3. **Time window** (optional): catches images without GPS.
4. **Target folders**: one per corridor. Run the analysis.

### Fix misfiled images from their neighbours (no corridor needed)

When shots were uploaded under the wrong mission, the images around them are usually right. After
the scan, panel **A** puts every image on a satellite map and rings the ones whose neighbours (nearby
on the ground, plus the shots taken just before and after by the same drone) are filed elsewhere.

For a `Parent > Site > Feeder > Pole` tree, keep **Move: Whole pole folders** (the default): the pole
folder is what moves, with all its images, into the feeder its neighbouring poles are under. Dots are
coloured by feeder, and a pole whose own images disagree is marked *mixed* so you can check it first.
**Single images** mode moves images instead. Select with **Box** or **Lasso** (draw freehand round a run of poles; tick *Remove*, or hold Alt, to
take them out again), **Select all in view**, or click dots one by one. Keys: B box, L lasso, P pan.
Then pick the destination,
review the move list, then **Apply moves in Media Drive**. Each run can be undone, and saved as JSON.

### Merge split captures

The **Merge splits** tab finds bursts of shots taken together (same drone, consecutive shots at most
60 s apart, within 20 m of the burst's first shot; both adjustable) that ended up in more than one
folder. Each burst is suggested to merge into the folder holding most of its shots; change the
destination per row, tick the bursts to merge and press **Merge selected**. Shots are moved as
single images, folders emptied by a merge are left in place (and reported), and the run can be undone.
With **Skip duplicate copies** (on by default), a file with the same name and capture second in two
or more folders, such as an archived original, is treated as a copy and left out.

### Scan cache

Each scanned folder's tree is kept in this browser (IndexedDB), so pressing **Scan** again loads it
instantly, even without a token. **Rescan fresh** ignores the cache (to pick up new uploads), and
↻ next to a cached folder rescans just that one. Ticking or unticking a cached folder loads exactly the ticked set straight away. Moves made here update the cache. The cache holds file names, folder names, GPS and
times (not images) and is not encrypted; **Clear cache** removes it.

### Corridor analysis

Outputs: misfiled list, strays, per-corridor and per-folder summaries, coverage gaps, a move-list CSV,
a full report CSV, GeoJSON, and a ready-to-paste GraphQL `move` mutation. The corridor analysis itself moves nothing.

## Repository layout

    index.html                 the tool (deployed as the GitHub Pages site)
    tools/extract_site_map.py  pulls feeder linework out of a vector PDF by colour -> *.sitemap.json
    tools/fetch_media_drive.py exports a Media Drive folder tree to JSON when the browser is blocked by CORS
    tools/requirements.txt     Python dependencies (PyMuPDF)
    sitemaps/                  extracted drawings live here locally; git-ignored (customer data)
    docs/                      notes on the API, matching logic and design standards
    .github/workflows/         Pages deployment

## Deploy

Pushing to `main` runs the Pages workflow. In the repository settings, under **Pages**, set
**Source** to **GitHub Actions** once (the first workflow run prompts for it if not set).

## CORS note

If the hosted page cannot reach the Media Drive API from the browser, export with
`tools/fetch_media_drive.py <FOLDER_ID> [<FOLDER_ID> ...]` (token in `UNLEASH_PAT`) and load the JSON under
**Advanced / offline options**.

## Design

Styled to the Unleash Live Design.md master (Brand Identity Guidelines v1.4): Chalk ground, white
hairline-ruled cards, Onyx ink, Geist Mono caps labels, red confined to interaction and the critical
state, secondary palette for status. STK Bureau Sans falls back to Inter until the licensed files are added.
