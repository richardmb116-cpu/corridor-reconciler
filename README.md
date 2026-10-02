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

### Organise a dump into captures

The **Organise** tab takes a folder of loose images (pick it as the source; sub-folders optional)
and splits it into **captures**: runs of consecutive shots from one drone with no gap over 120 s,
staying within 50 m of where the run started, and, when camera pitch is available, starting at a
nadir shot (pitch at or below -80°; the metadata field is found automatically or can be named).
Captures whose centres are within 25 m are the same **structure**, so a structure shot on three
missions shows as one structure with three visits. Visits are labelled to help decide whether they
were really one capture: *probably the same capture (paused n min)*, *re-shot (new nadir start)*,
*later the same day* or *separate mission*, and captures that do not begin with a nadir are marked.
**Combine** a structure's visits, or **Merge selected** captures, where they were one capture, and
leave any out with –.

**Create folders and move** builds, inside a chosen folder, either a folder per structure with a
sub-folder per visit, a folder per capture, or a folder per structure. Names come from editable
templates (`{sid}`, `{date}`, `{time}`, `{n}`, `{visit}`, `{visits}`) and can be changed per row;
existing folders with the same name are reused. Folder creation is not in the published Media Drive
API notes, so the page tries the likely `createFolder` forms (as unleash-mover does) and stops with
a clear message if none works. Moves can be undone; created folders are left in place.

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

### Merge loose and split shots

The **Merge splits** tab groups each drone's shots into bursts (consecutive shots at most 60 s apart,
within 20 m of the burst's first shot; both adjustable) and lists what needs putting back together:

- **Loose shots**: shots sitting in a feeder folder (a folder that also holds sub-folders) instead of
  a pole folder. They go into the pole folder of their own burst, or, when the whole burst is loose,
  the nearest pole folder on the ground.
- **Same-name folders**: bursts split between folders with the same name (ignoring `(2)` or `copy`).
- **Other splits**: any other burst spread over more than one folder.

Change the destination per row, tick what to fix and press **Merge selected**. Shots move as single
images, folders emptied by a merge are left in place (and reported), and the run can be undone.
With **Skip duplicate copies** (on by default), a file with the same name and capture second in two
or more folders, such as an archived original, is treated as a copy and left out.

### Check folders

The **Check folders** tab counts the RGB shots in every asset folder (a folder with no sub-folders
other than Archive folders) and flags any with more or fewer than the expected number (5 by
default). Thermal files (`_T` in the name) are not counted; the pattern is editable under **Rules**.
For each short folder it suggests the closest spare shots to refolder, and ticks them:

1. shots in the folder's own **Archive** sub-folder,
2. loose shots in the feeder, and
3. extra shots from over-full folders nearby,

taken within 120 s (same drone) and 30 m of the folder's own shots. Each spare shot goes to at most
one folder, no folder is given more than it needs, and an over-full folder is never taken below the
expected number. Folders that already have the right count are never touched. Over-full folders
list which of their shots have a home to go to. Review, then **Move ticked shots** (undoable).

Archive folders are also left out of Re-file and Merge: a pole folder holding an Archive is still a
pole folder, and a folder that holds sub-folders (a feeder) is never moved as a pole.

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
