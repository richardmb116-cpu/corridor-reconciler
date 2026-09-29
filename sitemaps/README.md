# Site maps

Extracted feeder drawings (`*.sitemap.json`) are loaded into the tool from your disk and are
deliberately git-ignored: they embed a render of the customer's distribution drawing.

Generate one with:

    pip install -r ../tools/requirements.txt
    python ../tools/extract_site_map.py "distribution-drawing.pdf" --name "Example site" \
        --label "0,0,255=Feeder A" --label "0,255,0=Feeder B" --label "0,191,255=Feeder C" --label "255,0,255=Feeder D"

Then open the tool, expand **Site map**, choose the JSON, place control points and apply.
Use **Save georeferenced site map** to keep the control points, names and exclusions with the file.
