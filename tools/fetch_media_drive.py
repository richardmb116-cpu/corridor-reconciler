#!/usr/bin/env python3
"""
Export an Unleash Live Media Drive folder tree to JSON for kml_media_reconciler.html.

Only needed if the browser page cannot call the API directly (CORS). Uses the
Python standard library only.

Usage:
    set UNLEASH_PAT=ul_pat_xxxxxxxx        (Windows)   |   export UNLEASH_PAT=ul_pat_xxx  (Mac/Linux)
    python fetch_media_drive.py <FOLDER_ID> [<FOLDER_ID> ...] [output.json] [--extra dateTimeOriginal,takenAt]

Several folder IDs are exported into one file (duplicates are skipped).

Then load the JSON file in the page under "Advanced / offline options".
"""
import json, os, sys, urllib.request, urllib.error

ENDPOINT = os.environ.get("UNLEASH_MEDIADRIVE_API", "https://mediadrive-api.unleashlive.com/graphql")
FIELDS = "id teamId location type tags createdAt updatedAt deviceId name parentId s3Path mimeType"
META = ["size", "childItemsNumber", "make", "model", "width", "height", "gpslat", "gpslng", "gpsalt", "isPanoramic", "duration"]
TOKEN = "pk sk locationCreatedAt teamId teamIdType createdAt searchNameCreatedAt searchName deviceId type"


def gql(query, pat):
    req = urllib.request.Request(ENDPOINT, data=json.dumps({"query": query}).encode(),
                                 headers={"content-type": "application/json", "authorization": f"Bearer {pat}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode(errors='replace')[:500]}")
    if body.get("errors"):
        raise SystemExit("GraphQL error: " + "; ".join(e.get("message", "?") for e in body["errors"]))
    return body["data"]


def lit(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return json.dumps(str(v))


def token_literal(tok):
    if not tok:
        return ""
    parts = [f"{k}: {lit(v)}" for k, v in tok.items() if lit(v) is not None]
    return f", nextToken: {{{', '.join(parts)}}}" if parts else ""


def is_folder(it):
    t = str(it.get("type") or "").upper()
    if t in ("F", "D", "FOLDER", "DIR", "DIRECTORY"):
        return True
    if t in ("I", "V", "IMAGE", "VIDEO"):
        return False
    md = it.get("metadata") or {}
    if md.get("childItemsNumber") is not None:
        return True
    return not it.get("mimeType") and not it.get("s3Path")


def list_all(location, pat, meta):
    items, tok = [], None
    while True:
        q = f"""query list {{ list(sort: desc, location: {json.dumps(location)}, limit: 200{token_literal(tok)}) {{
            items {{ {FIELDS} metadata {{ {' '.join(meta)} }} }}
            nextToken {{ {TOKEN} }} }} }}"""
        d = gql(q, pat)["list"] or {}
        items.extend(d.get("items") or [])
        tok = d.get("nextToken")
        if not tok or all(v is None for v in tok.values()):
            return items
        print(f"    … {len(items)} items", file=sys.stderr)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    extra = []
    if "--extra" in sys.argv:
        extra = [s.strip() for s in sys.argv[sys.argv.index("--extra") + 1].split(",") if s.strip()]
        args = [a for a in args if a not in extra and a != sys.argv[sys.argv.index("--extra") + 1]]
    if not args:
        raise SystemExit(__doc__)
    outs = [a for a in args if a.lower().endswith(".json")]
    root_ids = list(dict.fromkeys(a for a in args if a not in outs))
    if not root_ids:
        raise SystemExit(__doc__)
    out = outs[0] if outs else f"media-drive-items_{root_ids[0]}{'_and_more' if len(root_ids) > 1 else ''}.json"
    pat = os.environ.get("UNLEASH_PAT") or input("Personal Access Token: ").strip()
    meta = list(dict.fromkeys(META + extra))

    items, queue, seen, nf, nfile = [], [], set(), 0, 0
    for root_id in root_ids:
        root = gql(f'query GetLibraryItem {{ get(item:{{id:{json.dumps(root_id)}}}) {{ {FIELDS} metadata {{ {" ".join(meta)} }} }} }}', pat)["get"]
        if not root:
            raise SystemExit(f"Folder {root_id} not found")
        if root["id"] not in seen:
            seen.add(root["id"]); items.append(root); queue.append(root); nf += 1
    while queue:
        f = queue.pop(0)
        # Archive and Results folders keep a prefixed location ("archive#team/..."): list with the location
        # as stored, and only try the "#"-to-"/" form when that finds nothing.
        raw = f"{f.get('location') or ''}/{f['id']}" if f.get("location") else f["id"]
        loc = (f.get("location") or "").replace("#", "/")
        alt = f"{loc}/{f['id']}" if loc else f["id"]
        print(f"Listing {f.get('name') or f['id']}", file=sys.stderr)
        try:
            kids = list_all(raw, pat, meta)
            if not kids and alt != raw:
                kids = list_all(alt, pat, meta)
        except SystemExit:
            kids = list_all(alt, pat, meta)
        # sub-folders a location listing does not return (Archive, Results): ask for them by parent
        try:
            have = {k["id"] for k in kids}
            sub = gql(f'query sub {{ listSubfolders(parentId: {json.dumps(f["id"])}) {{ items {{ id }} }} }}', pat)["listSubfolders"] or {}
            for si in sub.get("items") or []:
                if si["id"] in have or si["id"] in seen:
                    continue
                it = gql(f'query GetLibraryItem {{ get(item:{{id:{json.dumps(si["id"])}}}) {{ {FIELDS} metadata {{ {" ".join(meta)} }} }} }}', pat)["get"]
                if it:
                    kids.append(it)
        except SystemExit:
            pass
        for k in kids:
            if k["id"] in seen:
                continue
            seen.add(k["id"])
            items.append(k)
            if is_folder(k):
                nf += 1
                queue.append(k)
            else:
                nfile += 1
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(items, fh)
    print(f"Done: {nf} folders, {nfile} files → {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
