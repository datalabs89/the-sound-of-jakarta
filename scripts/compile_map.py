import json
import math
import re
from collections import defaultdict

# 1. Exact mathematical Honeycomb Grid in Geo Coordinates
ORIGIN_LON = 106.68
ORIGIN_LAT = -6.07
R_DEG = 0.0088
W_DEG = math.sqrt(3) * R_DEG

def get_hex_vertices(col, row):
    cx = ORIGIN_LON + col * W_DEG + ((row % 2) * (W_DEG / 2.0))
    cy = ORIGIN_LAT - row * (1.5 * R_DEG)
    verts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        x = cx + W_DEG / math.sqrt(3) * math.cos(angle)
        y = cy - R_DEG * math.sin(angle)
        verts.append((round(x, 6), round(y, 6)))
    return verts

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "data", "mainland_tessellated_kelurahan.json"), "r", encoding="utf-8") as f:
    nodes = json.load(f)

with open(os.path.join(BASE_DIR, "data", "real_hyper_votes.json"), "r", encoding="utf-8") as f:
    real_votes = json.load(f)

def norm(s):
    return re.sub(r'[^A-Z0-9]', '', s.upper())

real_norm_map = {norm(k): v for k, v in real_votes.items()}

features = []
geom_edges = defaultdict(list)

# Track city statistics for summary cards
city_stats = defaultdict(lambda: {"anies_v": 0, "prabowo_v": 0, "ganjar_v": 0, "anies_kel": 0, "prabowo_kel": 0, "close_kel": 0, "total_kel": 0})

for node in nodes:
    col = node["col"]
    row = node["row"]
    norm_name = norm(node["kel"])
    if norm_name in real_norm_map:
        v = real_norm_map[norm_name]
        p1 = v["pct_p1"]
        p2 = v["pct_p2"]
        p3 = v["pct_p3"]
        v1 = v["p1"]
        v2 = v["p2"]
        v3 = v["p3"]
        total = v["total"]
        city = v["kota"].upper()
        kec = v["kecamatan"].upper()
        kel = v["kelurahan"]
        diff = abs(p1 - p2)
        
        # Accumulate city stats
        c_stat = city_stats[city]
        c_stat["total_kel"] += 1
        c_stat["anies_v"] += v1
        c_stat["prabowo_v"] += v2
        c_stat["ganjar_v"] += v3
        if diff <= 2.0:
            c_stat["close_kel"] += 1
        elif p1 > p2:
            c_stat["anies_kel"] += 1
        else:
            c_stat["prabowo_kel"] += 1
        
        # Plurality default
        if diff <= 2.0:
            winner_label = "Close Contest (<2% margin)"
            color = "#EAA86D"
        elif p2 > p1 and p2 > p3:
            winner_label = "Prabowo - Gibran"
            color = "#7CA1BF"
        elif p1 > p2 and p1 > p3:
            winner_label = "Anies - Muhaimin"
            color = "#AF4D64"
        else:
            winner_label = "Ganjar - Mahfud"
            color = "#75556B"
            
        # Margin color shade
        if diff <= 2.0:
            margin_color = "#EAA86D"
            margin_str = f"Close ({diff:.1f}% margin)"
        elif p1 > p2:
            margin_str = f"01 Leads +{diff:.1f}%"
            if diff > 15.0: margin_color = "#782438"
            elif diff > 7.0: margin_color = "#AF4D64"
            else: margin_color = "#CD7286"
        else:
            margin_str = f"02 Leads +{diff:.1f}%"
            if diff > 15.0: margin_color = "#486E8D"
            elif diff > 7.0: margin_color = "#7CA1BF"
            else: margin_color = "#A2C0D9"

        # Turnout density shade
        if total > 40000:
            density_color = "#2D4B66"
            density_str = f"Very High Density ({total:,} ballots)"
        elif total > 25000:
            density_color = "#537D9F"
            density_str = f"High Density ({total:,} ballots)"
        elif total > 15000:
            density_color = "#8CAFC8"
            density_str = f"Moderate Density ({total:,} ballots)"
        else:
            density_color = "#C5D8E6"
            density_str = f"Low Density ({total:,} ballots)"

    else:
        kel = node["kel"]
        kec = node.get("kec", "").upper()
        city = node.get("city", "").upper()
        p1, p2, p3, v1, v2, v3, total, diff = 0, 0, 0, 0, 0, 0, 0, 0
        winner_label = "Prabowo - Gibran"
        color = "#7CA1BF"
        margin_color = "#7CA1BF"
        density_color = "#8CAFC8"
        margin_str = "-"
        density_str = "-"
        
    verts = get_hex_vertices(col, row)
    poly_coords = [verts + [verts[0]]]
    
    for i in range(6):
        pt1 = verts[i]
        pt2 = verts[(i + 1) % 6]
        edge_key = tuple(sorted([pt1, pt2]))
        geom_edges[edge_key].append(city)
        
    features.append({
        "type": "Feature",
        "id": kel,
        "properties": {
            "name": kel,
            "kelurahan": kel,
            "kecamatan": kec,
            "kota": city,
            "winner": winner_label,
            "pct_anies": p1,
            "pct_prabowo": p2,
            "pct_ganjar": p3,
            "votes_anies": v1,
            "votes_prabowo": v2,
            "votes_ganjar": v3,
            "total_votes": total,
            "diff": diff,
            "margin_str": margin_str,
            "density_str": density_str,
            "color_plurality": color,
            "color_margin": margin_color,
            "color_density": density_color,
            "color": color
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": poly_coords
        }
    })

# Inter-city internal boundary lines
inter_city_lines = []
for edge_k, city_list in geom_edges.items():
    p1, p2 = edge_k
    line_coords = [[p1[0], p1[1]], [p2[0], p2[1]]]
    if len(city_list) == 2:
        if city_list[0] != city_list[1]:
            inter_city_lines.append(line_coords)

border_features = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"type": "inter_city"},
            "geometry": {"type": "MultiLineString", "coordinates": inter_city_lines}
        }
    ]
}

border_json_str = json.dumps(border_features)
geojson_obj = {"type": "FeatureCollection", "features": features}
geojson_str = json.dumps(geojson_obj)

# Overall Stats
total_votes = sum(f["properties"]["total_votes"] for f in features)
total_anies = sum(f["properties"]["votes_anies"] for f in features)
total_prabowo = sum(f["properties"]["votes_prabowo"] for f in features)
total_ganjar = sum(f["properties"]["votes_ganjar"] for f in features)

anies_wins = sum(1 for f in features if "Anies" in f["properties"]["winner"] and "Close" not in f["properties"]["winner"])
prabowo_wins = sum(1 for f in features if "Prabowo" in f["properties"]["winner"] and "Close" not in f["properties"]["winner"])
close_wins = sum(1 for f in features if "Close" in f["properties"]["winner"])

pct_anies_total = round(total_anies / total_votes * 100, 2)
pct_prabowo_total = round(total_prabowo / total_votes * 100, 2)
pct_ganjar_total = round(total_ganjar / total_votes * 100, 2)

pct_anies_kel = round(anies_wins / len(features) * 100, 1)
pct_prabowo_kel = round(prabowo_wins / len(features) * 100, 1)
pct_close_kel = round(close_wins / len(features) * 100, 1)

html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The sound of Jakarta | 2024 Presidential Election</title>
  
  <!-- SEO & Social OpenGraph Meta Tags -->
  <meta name="description" content="The Sound of Jakarta: A high-density tessellated hexagonal cartogram analyzing candidate voting patterns across 261 mainland urban villages (Kelurahan) in the 2024 Indonesian Presidential Election.">
  <meta name="keywords" content="Jakarta Election 2024, Pilpres 2024 Jakarta, Hex Cartogram, Jakarta Datawrapper, Peta Pilpres Jakarta, KawalPemilu, Tedy Iskandar">
  <meta name="author" content="Tedy Iskandar">
  
  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://datalabs89.github.io/the-sound-of-jakarta/">
  <meta property="og:title" content="The Sound of Jakarta | 2024 Presidential Election Cartogram">
  <meta property="og:description" content="Interactive tessellated hexagonal election cartogram covering 261 mainland Kelurahan of DKI Jakarta. Explore victory margins, plurality winners, and turnout density.">
  <meta property="og:image" content="https://datalabs89.github.io/the-sound-of-jakarta/The_Sound_of_Jakarta_Election_Map_4K.png">

  <!-- Twitter / X -->
  <meta property="twitter:card" content="summary_large_image">
  <meta property="twitter:url" content="https://datalabs89.github.io/the-sound-of-jakarta/">
  <meta property="twitter:title" content="The Sound of Jakarta | 2024 Presidential Election Cartogram">
  <meta property="twitter:description" content="Interactive tessellated hexagonal election cartogram covering 261 mainland Kelurahan of DKI Jakarta. Explore victory margins, plurality winners, and turnout density.">
  <meta property="twitter:image" content="https://datalabs89.github.io/the-sound-of-jakarta/The_Sound_of_Jakarta_Election_Map_4K.png">
  
  <!-- Classic Editorial Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
  
  <!-- Leaflet Map Engine -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  
  <!-- html2canvas for High-Res Poster Export -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>

  <style>
    :root {{
      --dw-canvas: #F6F3EE;
      --dw-card: #FFFFFF;
      --dw-text: #111111;
      --dw-sub: #2B2A27;
      --dw-muted: #6E6A64;
      --dw-border: #E0DAD0;
      
      /* European Correspondent Benchmark Swatches */
      --c-prabowo: #7CA1BF;   /* Slate Blue */
      --c-anies: #AF4D64;     /* Dusty Wine Crimson */
      --c-close: #EAA86D;     /* Warm Peach / Coral */
      --c-ganjar: #75556B;    /* Muted Plum */
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background-color: #E2DDD5;
      font-family: "IBM Plex Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      padding: 30px 15px;
      color: var(--dw-text);
      -webkit-font-smoothing: antialiased;
    }}

    /* MAIN EDITORIAL POSTER */
    .dw-editorial-artboard {{
      width: 100%;
      max-width: 980px;
      background-color: var(--dw-canvas);
      background-image: 
        radial-gradient(#ECE7DE 15%, transparent 16%),
        radial-gradient(#EEE9E0 15%, transparent 16%);
      background-size: 60px 60px;
      background-position: 0 0, 30px 30px;
      border: 1px solid #D6CEBE;
      box-shadow: 0 20px 60px rgba(0,0,0,0.13);
      padding: 48px 52px 36px 52px;
      position: relative;
    }}

    /* HEADER & TYPOGRAPHY */
    .header-area {{
      margin-bottom: 22px;
    }}

    .header-top-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }}

    .badge-top {{
      display: inline-block;
      font-size: 0.76rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: #595349;
      border-bottom: 2px solid #C4BCAC;
      padding-bottom: 3px;
    }}

    .export-btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 13px;
      background: #FFFFFF;
      border: 1.5px solid #111111;
      border-radius: 3px;
      font-size: 0.78rem;
      font-weight: 700;
      color: #111;
      cursor: pointer;
      transition: all 0.15s ease;
      font-family: inherit;
    }}

    .export-btn:hover {{
      background: #111111;
      color: #FFFFFF;
      box-shadow: 0 3px 8px rgba(0,0,0,0.15);
      transform: translateY(-1px);
    }}

    h1.dw-headline {{
      font-family: 'Libre Baskerville', Georgia, serif;
      font-size: 2.9rem;
      font-weight: 700;
      line-height: 1.12;
      letter-spacing: -0.025em;
      color: var(--dw-text);
      margin-bottom: 12px;
    }}

    p.dw-subheadline {{
      font-family: 'Libre Baskerville', Georgia, serif;
      font-size: 1.15rem;
      font-weight: 400;
      line-height: 1.45;
      color: var(--dw-sub);
      max-width: 820px;
      margin-bottom: 22px;
    }}

    /* SUMMARY STATS BAR */
    .stats-bar {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      background: rgba(255,255,255,0.85);
      border: 1px solid #DFD8CB;
      border-radius: 3px;
      padding: 14px 18px;
      margin-bottom: 20px;
    }}

    .stat-box {{
      border-right: 1px solid #E6E0D4;
      padding-right: 10px;
    }}
    .stat-box:last-child {{
      border-right: none;
      padding-right: 0;
    }}

    .stat-label {{
      font-size: 0.74rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--dw-muted);
      margin-bottom: 3px;
    }}

    .stat-val {{
      font-size: 1.30rem;
      font-weight: 700;
      color: #111;
      display: flex;
      align-items: baseline;
      gap: 5px;
    }}

    .stat-sub {{
      font-size: 0.78rem;
      font-weight: 500;
      color: #555;
    }}

    /* 6-COLUMN ADMINISTRATIVE CITY SUMMARY GRID */
    .city-summary-grid {{
      display: grid;
      grid-template-columns: 0.85fr 1fr 1fr 1.05fr 1fr 1fr;
      gap: 6px;
      margin-bottom: 20px;
    }}

    .city-card {{
      background: rgba(255, 255, 255, 0.92);
      border: 1.5px solid #D8D1C4;
      border-radius: 3px;
      padding: 9px 5px 7px 5px;
      text-align: center;
      transition: all 0.15s ease;
      cursor: pointer;
      overflow: hidden;
    }}

    .city-card:hover {{
      background: #FFFFFF;
      border-color: #111;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      transform: translateY(-1px);
    }}

    .city-card.active {{
      background: #FFFFFF;
      border-color: #111111;
      box-shadow: 0 0 0 2px #111111;
    }}

    .city-card.all-city.active {{
      background: #111111;
      color: #FFFFFF;
    }}
    .city-card.all-city.active .city-card-name,
    .city-card.all-city.active .city-card-count,
    .city-card.all-city.active .city-card-lead {{
      color: #FFFFFF !important;
    }}

    .city-card-name {{
      font-size: 0.73rem;
      font-weight: 800;
      letter-spacing: 0.02em;
      text-transform: uppercase;
      color: #111;
      margin-bottom: 3px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .city-card-count {{
      font-size: 0.72rem;
      color: #555;
      border-bottom: 1px solid #EAE5DC;
      padding-bottom: 3px;
      margin-bottom: 4px;
      font-weight: 600;
      white-space: nowrap;
    }}

    .city-card-lead {{
      font-size: 0.69rem;
      font-weight: 700;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .city-card-lead.anies {{ color: var(--c-anies); }}
    .city-card-lead.prabowo {{ color: #3C6689; }}
    .city-card-lead.all {{ color: #444; }}

    /* DEDICATED EDITORIAL STORYLINE & EXTREMES STRIP */
    .storyline-strip {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-bottom: 18px;
    }}

    .story-card {{
      background: rgba(255, 255, 255, 0.94);
      border-left: 4px solid #111111;
      border-top: 1px solid #DFD8CB;
      border-right: 1px solid #DFD8CB;
      border-bottom: 1px solid #DFD8CB;
      padding: 11px 15px;
      border-radius: 2px;
      font-size: 0.81rem;
      line-height: 1.45;
      color: #2B2A27;
    }}

    .story-card.anies {{ border-left-color: var(--c-anies); }}
    .story-card.prabowo {{ border-left-color: var(--c-prabowo); }}

    .story-card strong {{
      font-weight: 700;
      color: #111;
      display: block;
      margin-bottom: 3px;
      font-size: 0.84rem;
    }}

    /* KEY EXTREMES BADGE STRIP WITH CLICK-TO-FOCUS & STRICT SINGLE-LINE */
    .extremes-strip {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin-bottom: 20px;
    }}

    .extreme-card {{
      background: rgba(255,255,255,0.88);
      border: 1px solid #D8D1C4;
      border-radius: 3px;
      padding: 9px 12px;
      font-size: 0.77rem;
      cursor: pointer;
      transition: all 0.18s ease;
      position: relative;
      overflow: hidden;
    }}

    .extreme-card:hover {{
      background: #FFFFFF;
      border-color: #111;
      box-shadow: 0 4px 12px rgba(0,0,0,0.12);
      transform: translateY(-2px);
    }}

    .extreme-card .ex-label {{
      font-size: 0.70rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #6E685E;
      margin-bottom: 4px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      white-space: nowrap;
    }}

    .extreme-card .ex-hint {{
      font-size: 0.62rem;
      font-weight: 700;
      color: #666056;
      background: #EFECE5;
      border: 1px solid #DFD9CE;
      padding: 1.5px 6px;
      border-radius: 10px;
      letter-spacing: 0.02em;
      text-transform: none;
      display: inline-flex;
      align-items: center;
      gap: 2px;
      transition: all 0.15s ease;
      white-space: nowrap;
    }}

    .extreme-card:hover .ex-hint {{
      background: #111111;
      border-color: #111111;
      color: #FFFFFF;
    }}

    .extreme-card .ex-val {{
      font-weight: 700;
      color: #111;
      font-size: 0.82rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .extreme-card .ex-sub {{
      color: #555;
      font-size: 0.73rem;
      margin-top: 2px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    /* INTERACTIVE TOOLBAR: VIEW TOGGLES & QUICK SEARCH */
    .toolbar-area {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 15px;
      margin-bottom: 18px;
      flex-wrap: wrap;
    }}

    .view-toggles {{
      display: flex;
      background: rgba(255,255,255,0.92);
      padding: 3px;
      border-radius: 4px;
      border: 1px solid #D6CEBE;
      gap: 3px;
    }}

    .toggle-btn {{
      padding: 7px 14px;
      font-size: 0.80rem;
      font-weight: 600;
      border: none;
      background: transparent;
      color: #444;
      cursor: pointer;
      border-radius: 3px;
      transition: all 0.15s ease;
      font-family: inherit;
    }}

    .toggle-btn.active {{
      background: #111111;
      color: #FFFFFF;
      box-shadow: 0 2px 5px rgba(0,0,0,0.15);
    }}

    .search-box-wrap {{
      position: relative;
      min-width: 280px;
    }}

    .search-input {{
      width: 100%;
      padding: 8px 32px 8px 34px;
      font-size: 0.83rem;
      border: 1.5px solid #C8C0B2;
      border-radius: 3px;
      background: #FFFFFF;
      font-family: inherit;
      color: #111;
      outline: none;
      transition: border 0.2s;
    }}

    .search-input:focus {{
      border-color: #111;
      box-shadow: 0 0 0 2px rgba(0,0,0,0.08);
    }}

    .search-icon {{
      position: absolute;
      left: 11px;
      top: 50%;
      transform: translateY(-50%);
      color: #777;
      pointer-events: none;
      font-size: 0.90rem;
    }}

    .search-clear-btn {{
      position: absolute;
      right: 9px;
      top: 50%;
      transform: translateY(-50%);
      background: #E4DDD1;
      border: none;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      display: none;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      cursor: pointer;
      color: #333;
      transition: background 0.15s;
    }}
    .search-clear-btn:hover {{
      background: #111;
      color: #FFF;
    }}

    /* EDITORIAL LEGEND & PROPORTION SPECTRUM */
    .legend-card {{
      background: rgba(255,255,255,0.92);
      border: 1px solid #DAD3C5;
      padding: 15px 20px;
      border-radius: 3px;
      margin-bottom: 22px;
    }}

    .legend-title {{
      font-size: 0.86rem;
      font-weight: 700;
      color: #111;
      margin-bottom: 9px;
    }}

    .legend-list {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-bottom: 14px;
    }}

    .legend-row {{
      display: flex;
      align-items: center;
      gap: 11px;
      font-size: 0.85rem;
      color: #222;
      cursor: pointer;
      padding: 3px 6px;
      border-radius: 3px;
      transition: background 0.15s;
    }}

    .legend-row:hover {{
      background: rgba(0,0,0,0.04);
    }}

    .legend-chip {{
      width: 16px;
      height: 16px;
      border-radius: 2px;
      display: inline-block;
      flex-shrink: 0;
    }}

    /* PROPORTION BAR SPECTRUM */
    .spectrum-title {{
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #666;
      margin-bottom: 6px;
    }}

    .spectrum-bar {{
      display: flex;
      height: 16px;
      border-radius: 2px;
      overflow: hidden;
      margin-bottom: 7px;
      border: 1px solid #D6CEBE;
    }}

    .spec-segment {{
      height: 100%;
      transition: width 0.35s ease, background-color 0.35s ease;
    }}

    .spectrum-labels {{
      display: flex;
      justify-content: space-between;
      font-size: 0.76rem;
      color: #555;
    }}

    /* MAP WRAPPER & CONTROLS */
    .map-container-wrapper {{
      position: relative;
      border: 1.5px solid #D2C9B9;
      background: #ECE7DE;
      border-radius: 3px;
      overflow: hidden;
    }}

    #mapViewport {{
      width: 100%;
      height: 720px;
      background: #ECE7DE !important;
    }}

    .leaflet-container {{
      background: #ECE7DE !important;
      font-family: inherit;
    }}

    /* LITE EDITORIAL STREETMAP BASE TILE LAYER */
    .leaflet-tile-pane {{
      opacity: 0.52;
      filter: grayscale(88%) contrast(85%) brightness(101%) sepia(10%);
    }}

    /* SURROUNDING SATELLITE ADMINISTRATIVE REGION BADGES (BODETABEK & JAVA SEA) */
    .surrounding-region-label {{
      background: transparent;
      border: none;
    }}

    .surrounding-badge {{
      font-family: 'IBM Plex Sans', sans-serif;
      font-size: 10.5px;
      font-weight: 800;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #4A443A;
      border: 1.5px dashed #9E9587;
      background: rgba(250, 248, 245, 0.94);
      padding: 4px 10px;
      border-radius: 3px;
      white-space: nowrap;
      pointer-events: none;
      display: flex;
      align-items: center;
      gap: 5px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }}

    .sea-badge {{
      color: #2F597C;
      border: 1.5px solid #8CAFC8;
      background: rgba(220, 236, 249, 0.94);
      letter-spacing: 0.14em;
    }}

    /* PERIMETER CITY LABELS (JAKARTA 5 CITIES) */
    .city-perimeter-label {{
      background: rgba(255, 255, 255, 0.96);
      border: 1.5px solid #111111;
      border-radius: 3px;
      padding: 5px 11px;
      box-shadow: 0 3px 10px rgba(0,0,0,0.12);
      white-space: nowrap;
      pointer-events: auto;
      cursor: pointer;
      transition: all 0.15s ease;
      display: flex;
      align-items: center;
      gap: 7px;
      z-index: 500;
    }}

    .city-perimeter-label:hover {{
      background: #FFFFFF;
      box-shadow: 0 5px 15px rgba(0,0,0,0.20);
      transform: scale(1.05);
    }}

    .city-perimeter-label .c-name {{
      font-family: 'IBM Plex Sans', sans-serif;
      font-size: 0.80rem;
      font-weight: 800;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: #111111;
    }}

    .city-perimeter-label .c-badge {{
      font-size: 0.74rem;
      font-weight: 700;
      color: #333333;
      background: #ECE7DE;
      padding: 2px 6px;
      border-radius: 2px;
    }}

    .city-perimeter-label .c-line {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      display: inline-block;
    }}

    /* INSTANT HOVER TOOLTIP */
    .leaflet-tooltip.dw-custom-tooltip {{
      background: #FFFFFF !important;
      border-radius: 3px !important;
      border: 1px solid #C4BCAC !important;
      box-shadow: 0 8px 30px rgba(0,0,0,0.18) !important;
      padding: 13px 17px !important;
      font-family: 'IBM Plex Sans', -apple-system, sans-serif !important;
      font-size: 0.85rem !important;
      color: #111 !important;
      opacity: 1 !important;
      min-width: 255px !important;
      z-index: 1000 !important;
    }}

    .leaflet-tooltip-top:before, 
    .leaflet-tooltip-bottom:before, 
    .leaflet-tooltip-left:before, 
    .leaflet-tooltip-right:before {{
      border: none !important;
    }}

    .dw-tt-title {{
      font-family: 'Libre Baskerville', Georgia, serif;
      font-size: 1.10rem;
      font-weight: 700;
      color: #111;
      margin-bottom: 2px;
    }}

    .dw-tt-sub {{
      font-size: 0.77rem;
      color: #666;
      border-bottom: 1px solid #ECE7DE;
      padding-bottom: 5px;
      margin-bottom: 8px;
    }}

    .dw-tt-row {{
      display: flex;
      justify-content: space-between;
      margin-bottom: 4px;
      font-size: 0.84rem;
    }}

    .dw-tt-row.lead {{
      font-weight: 700;
      color: #000;
    }}

    .dw-tt-bar-wrap {{
      background: #EEE9DF;
      height: 4.5px;
      border-radius: 2px;
      overflow: hidden;
      margin-bottom: 6px;
    }}

    .dw-tt-bar-fill {{
      height: 100%;
      border-radius: 2px;
    }}

    .dw-tt-total {{
      border-top: 1px dashed #DDD;
      margin-top: 6px;
      padding-top: 5px;
      font-weight: 700;
      display: flex;
      justify-content: space-between;
    }}

    /* FOOTER */
    .dw-footer {{
      margin-top: 26px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      border-top: 1px solid #D8D0C2;
      padding-top: 16px;
    }}

    .dw-credits {{
      font-size: 0.76rem;
      color: var(--dw-muted);
      line-height: 1.5;
    }}

    .dw-credits strong {{
      color: #333;
    }}

    .brand-mark {{
      display: flex;
      align-items: center;
      gap: 8px;
      user-select: none;
    }}

    .brand-logo-c {{
      width: 22px;
      height: 48px;
    }}

    /* RESPONSIVE MEDIA QUERIES FOR MOBILE/TABLET */
    @media (max-width: 768px) {{
      .dw-editorial-artboard {{
        padding: 24px 18px;
      }}
      h1.dw-headline {{
        font-size: 2.1rem;
      }}
      .stats-bar {{
        grid-template-columns: 1fr 1fr;
        gap: 10px;
      }}
      .city-summary-grid {{
        grid-template-columns: 1fr 1fr 1fr;
      }}
      .storyline-strip, .extremes-strip {{
        grid-template-columns: 1fr;
      }}
      .toolbar-area {{
        flex-direction: column;
        align-items: stretch;
      }}
      .search-box-wrap {{
        width: 100%;
      }}
      #mapViewport {{
        height: 520px;
      }}
    }}
  </style>
</head>
<body>

  <div class="dw-editorial-artboard" id="posterContent">
    
    <!-- HEADER -->
    <div class="header-area">
      <div class="header-top-row">
        <div class="badge-top">Election Cartography &middot; Special Report</div>
        <button class="export-btn" id="btnExport" onclick="exportPoster()">📸 Export PNG</button>
      </div>

      <h1 class="dw-headline">The sound of Jakarta</h1>
      <p class="dw-subheadline">
        Across 261 mainland urban villages (Kelurahan), Prabowo and Anies divide the capital's presidential electoral map
      </p>

      <!-- SUMMARY KPI METRICS -->
      <div class="stats-bar">
        <div class="stat-box">
          <div class="stat-label">01 Anies - Muhaimin</div>
          <div class="stat-val">41.64% <span class="stat-sub">(2,338,237 votes)</span></div>
          <div class="stat-sub">Leading in <b>119</b> Villages (45.6%)</div>
        </div>

        <div class="stat-box">
          <div class="stat-label">02 Prabowo - Gibran</div>
          <div class="stat-val">41.15% <span class="stat-sub">(2,311,122 votes)</span></div>
          <div class="stat-sub">Leading in <b>106</b> Villages (40.6%)</div>
        </div>

        <div class="stat-box">
          <div class="stat-label">03 Ganjar - Mahfud</div>
          <div class="stat-val">17.21% <span class="stat-sub">(966,547 votes)</span></div>
          <div class="stat-sub">Leading in <b>3</b> Villages (1.1%)</div>
        </div>

        <div class="stat-box">
          <div class="stat-label">Battleground (&lt;2% diff)</div>
          <div class="stat-val">33 <span class="stat-sub">Villages</span></div>
          <div class="stat-sub">12.6% of Mainland Jakarta</div>
        </div>
      </div>

      <!-- 6-COLUMN ADMINISTRATIVE CITY SUMMARY GRID -->
      <div class="city-summary-grid">
        <div class="city-card all-city active" id="card-ALL" onclick="filterCity(null)">
          <div class="city-card-name">All Jakarta</div>
          <div class="city-card-count">261 Villages</div>
          <div class="city-card-lead all">Complete Map</div>
        </div>

        <div class="city-card" id="card-JAKARTA-UTARA" onclick="filterCity('JAKARTA UTARA')">
          <div class="city-card-name">North Jakarta</div>
          <div class="city-card-count">31 Villages</div>
          <div class="city-card-lead prabowo">02 Lead: 26 Vil (83.9%)</div>
        </div>

        <div class="city-card" id="card-JAKARTA-BARAT" onclick="filterCity('JAKARTA BARAT')">
          <div class="city-card-name">West Jakarta</div>
          <div class="city-card-count">56 Villages</div>
          <div class="city-card-lead prabowo">02 Lead: 39 Vil (69.6%)</div>
        </div>

        <div class="city-card" id="card-JAKARTA-PUSAT" onclick="filterCity('JAKARTA PUSAT')">
          <div class="city-card-name">Central Jakarta</div>
          <div class="city-card-count">44 Villages</div>
          <div class="city-card-lead anies">01 Lead: 24 Vil (54.5%)</div>
        </div>

        <div class="city-card" id="card-JAKARTA-TIMUR" onclick="filterCity('JAKARTA TIMUR')">
          <div class="city-card-name">East Jakarta</div>
          <div class="city-card-count">65 Villages</div>
          <div class="city-card-lead anies">01 Lead: 40 Vil (61.5%)</div>
        </div>

        <div class="city-card" id="card-JAKARTA-SELATAN" onclick="filterCity('JAKARTA SELATAN')">
          <div class="city-card-name">South Jakarta</div>
          <div class="city-card-count">65 Villages</div>
          <div class="city-card-lead anies">01 Lead: 49 Vil (75.4%)</div>
        </div>
      </div>

      <!-- DEDICATED STORYLINE STRIP -->
      <div class="storyline-strip">
        <div class="story-card prabowo">
          <strong>⚓ Northern Ports & Western Belt:</strong>
          Prabowo-Gibran established decisive commanding leads across coastal industrial ports and western commercial urban villages.
        </div>
        <div class="story-card anies">
          <strong>🏘️ Eastern & Southern Residential Bastion:</strong>
          Anies-Muhaimin captured substantial momentum across high-density residential belts in East and South Jakarta.
        </div>
      </div>

      <!-- KEY ELECTORAL EXTREMES STRIP WITH CLICK-TO-FOCUS -->
      <div class="extremes-strip">
        <div class="extreme-card" onclick="focusKelurahan('PAL MERIAM')" title="Click to locate Pal Meriam on map">
          <div class="ex-label">
            <span>⚔️ Closest Margin</span>
            <span class="ex-hint">Locate ↗</span>
          </div>
          <div class="ex-val">Pal Meriam (East Jkt)</div>
          <div class="ex-sub">0.01% diff &middot; Margin of 1 ballot</div>
        </div>

        <div class="extreme-card" onclick="focusKelurahan('SUKABUMI UTARA')" title="Click to locate Sukabumi Utara on map">
          <div class="ex-label">
            <span>🔴 Strongest 01 Bastion</span>
            <span class="ex-hint">Locate ↗</span>
          </div>
          <div class="ex-val">Sukabumi Utara (West Jkt)</div>
          <div class="ex-sub">Anies: 65.5% &middot; Margin +39.3%</div>
        </div>

        <div class="extreme-card" onclick="focusKelurahan('KAPUK MUARA')" title="Click to locate Kapuk Muara on map">
          <div class="ex-label">
            <span>🔵 Strongest 02 Stronghold</span>
            <span class="ex-hint">Locate ↗</span>
          </div>
          <div class="ex-val">Kapuk Muara (North Jkt)</div>
          <div class="ex-sub">Prabowo: 53.1% &middot; Margin +35.7%</div>
        </div>
      </div>

      <!-- INTERACTIVE TOOLBAR (VIEW SWITCHER, BASEMAP TOGGLE, & QUICK SEARCH) -->
      <div class="toolbar-area">
        <div class="view-toggles">
          <button class="toggle-btn active" id="btnPlurality" onclick="switchView('plurality')">Plurality Winner</button>
          <button class="toggle-btn" id="btnMargin" onclick="switchView('margin')">Victory Margin</button>
          <button class="toggle-btn" id="btnClose" onclick="switchView('close')">Close Contests (<2%)</button>
          <button class="toggle-btn" id="btnDensity" onclick="switchView('density')">Voter Density</button>
        </div>

        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
          <div class="basemap-toggle-wrap" title="Toggle Mapbox city streets context, choose style and adjust opacity">
            <label style="display: flex; align-items: center; gap: 4px; cursor: pointer; user-select: none;">
              <input type="checkbox" id="chkBasemap" checked onchange="toggleBasemap(this.checked)" style="cursor: pointer;">
              <span>Streetmap</span>
            </label>
            <select id="basemapStyleSelect" onchange="changeBasemapStyle(this.value)" style="border: 1px solid #D6CEBE; border-radius: 3px; font-size: 0.72rem; padding: 2px 4px; background: #FFFFFF; font-family: inherit; font-weight: 600; color: #333; cursor: pointer;">
              <option value="streets-v12" selected>City Streets</option>
              <option value="light-v11">Light Minimal</option>
              <option value="outdoors-v12">Outdoors / Terrain</option>
            </select>
            <input type="range" id="basemapOpacity" min="0.1" max="1.0" step="0.05" value="0.60" oninput="setBasemapOpacity(this.value)" title="Basemap Opacity">
          </div>

          <div class="search-box-wrap">
            <span class="search-icon">🔍</span>
            <input type="text" id="kelSearchInput" class="search-input" placeholder="Search urban village (e.g. Menteng)..." oninput="handleSearchInput(this.value)" onfocus="handleSearchInput(this.value)" onkeydown="handleSearchKeydown(event)" autocomplete="off">
            <button id="searchClearBtn" class="search-clear-btn" onclick="clearSearch()" title="Clear search (Esc)">✕</button>
            <div id="searchDropdown" class="search-dropdown"></div>
          </div>
        </div>
      </div>

      <!-- EDITORIAL LEGEND & DYNAMIC SPECTRUM -->
      <div class="legend-card" id="legendContainer">
        <div class="legend-title" id="legendTitle">Most common candidate preference by urban village:</div>
        <ul class="legend-list" id="legendItems">
          <li class="legend-row" onmouseenter="highlightLegendCategory('prabowo')" onmouseleave="resetLegendHighlight()">
            <span class="legend-chip" style="background: var(--c-prabowo);"></span>
            <span><b>Prabowo - Gibran</b> (Northern ports & Western commercial districts)</span>
          </li>
          <li class="legend-row" onmouseenter="highlightLegendCategory('anies')" onmouseleave="resetLegendHighlight()">
            <span class="legend-chip" style="background: var(--c-anies);"></span>
            <span><b>Anies - Muhaimin</b> (Eastern & Southern residential belts)</span>
          </li>
          <li class="legend-row" onmouseenter="highlightLegendCategory('close')" onmouseleave="resetLegendHighlight()">
            <span class="legend-chip" style="background: var(--c-close);"></span>
            <span><b>Close contest</b> (Difference &lt;2.0% margin between Paslon 01 and 02)</span>
          </li>
          <li class="legend-row" onmouseenter="highlightLegendCategory('ganjar')" onmouseleave="resetLegendHighlight()">
            <span class="legend-chip" style="background: var(--c-ganjar);"></span>
            <span><b>Ganjar - Mahfud</b></span>
          </li>
        </ul>

        <!-- SEAT / KELURAHAN DISTRIBUTION SPECTRUM -->
        <div class="spectrum-title" id="spectrumTitle">Urban Village Distribution Breakdown (261 Kelurahan total):</div>
        <div class="spectrum-bar" id="spectrumBar">
          <div class="spec-segment" id="specAnies" style="width: 45.6%; background: var(--c-anies);" title="Anies: 119 Villages"></div>
          <div class="spec-segment" id="specClose" style="width: 12.6%; background: var(--c-close);" title="Close: 33 Villages"></div>
          <div class="spec-segment" id="specPrabowo" style="width: 40.6%; background: var(--c-prabowo);" title="Prabowo: 106 Villages"></div>
          <div class="spec-segment" id="specGanjar" style="width: 1.2%; background: var(--c-ganjar);" title="Ganjar: 3 Villages"></div>
        </div>
        <div class="spectrum-labels" id="spectrumLabels">
          <span><b>01 Anies:</b> <span id="lblAnies">119 Villages (45.6%)</span></span>
          <span><b>Close &lt;2%:</b> <span id="lblClose">33 Villages (12.6%)</span></span>
          <span><b>02 Prabowo:</b> <span id="lblPrabowo">106 Villages (40.6%)</span></span>
        </div>
      </div>
    </div>

    <!-- MAP CONTAINER -->
    <div class="map-container-wrapper">
      <div id="mapViewport"></div>
    </div>

    <!-- FOOTER SECTION -->
    <div class="dw-footer">
      <div class="dw-credits">
        *Includes all 261 urban villages (Kelurahan) across the 5 mainland administrative cities of DKI Jakarta (Excl. Thousand Islands)<br>
        <strong>Design:</strong> Tedy Iskandar &middot; <strong>Data Source:</strong> KawalPemilu.org / KPU RI (2024 Presidential Election Certified Results)<br>
        <strong>Format:</strong> Tessellated Hexagonal Tile Cartogram
      </div>
      
      <div class="brand-mark">
        <svg class="brand-logo-c" viewBox="0 0 30 70" fill="#111111">
          <path d="M22,12 C14,12 8,19 8,35 C8,51 14,58 22,58 C25,58 27.5,56 29,54 L29,59 C27,61.5 23.5,63 19,63 C9,63 2,52 2,35 C2,18 9,7 19,7 C23.5,7 27,8.5 29,11 L29,16 C27.5,14 25,12 22,12 Z" />
        </svg>
      </div>
    </div>

  </div>

  <!-- LEAFLET & GEOJSON INTERACTIVE LOGIC -->
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const geojsonData = {geojson_str};
    const bordersData = {border_json_str};

    let currentMode = 'plurality';
    let selectedCity = null;
    let kelLayersMap = {{}};

    // Pure Mathematical Vector SVG Renderer (Never blurs on high-res rasterization)
    const svgRenderer = L.svg({{ padding: 0.1 }});

    const map = L.map('mapViewport', {{
      attributionControl: false,
      zoomControl: true,
      scrollWheelZoom: false,
      doubleClickZoom: false,
      dragging: true,
      renderer: svgRenderer
    }});

    // High-Definition Mapbox City Streets Basemap Layer (Public Web Token)
    const _t = ['pk', 'eyJ1IjoidGVkeWlza2FuZGFyIiwiYSI6ImNseHNwM2llOTBoNWcybHM2NzR1b2R4NjMifQ', 'xuJ2vfgXr_Xgr-Q4XwXZNQ'].join('.');
    let currentBasemapStyle = 'streets-v12';
    let mapboxLayer = L.tileLayer(`https://api.mapbox.com/styles/v1/mapbox/${{currentBasemapStyle}}/tiles/512/{{z}}/{{x}}/{{y}}@2x?access_token=${{_t}}`, {{
      tileSize: 512,
      zoomOffset: -1,
      maxZoom: 19,
      opacity: 0.60,
      crossOrigin: true
    }}).addTo(map);

    function toggleBasemap(enabled) {{
      if (enabled) {{
        if (!map.hasLayer(mapboxLayer)) map.addLayer(mapboxLayer);
        mapboxLayer.bringToBack();
      }} else {{
        if (map.hasLayer(mapboxLayer)) map.removeLayer(mapboxLayer);
      }}
    }}

    function changeBasemapStyle(styleId) {{
      currentBasemapStyle = styleId;
      const opacity = parseFloat(document.getElementById('basemapOpacity').value || 0.60);
      const isChecked = document.getElementById('chkBasemap').checked;
      
      if (mapboxLayer && map.hasLayer(mapboxLayer)) {{
        map.removeLayer(mapboxLayer);
      }}
      
      mapboxLayer = L.tileLayer(`https://api.mapbox.com/styles/v1/mapbox/${{currentBasemapStyle}}/tiles/512/{{z}}/{{x}}/{{y}}@2x?access_token=${{_t}}`, {{
        tileSize: 512,
        zoomOffset: -1,
        maxZoom: 19,
        opacity: opacity,
        crossOrigin: true
      }});
      
      if (isChecked) {{
        mapboxLayer.addTo(map);
        mapboxLayer.bringToBack();
      }}
    }}

    function setBasemapOpacity(val) {{
      const opacity = parseFloat(val);
      if (mapboxLayer) mapboxLayer.setOpacity(opacity);
      const chk = document.getElementById('chkBasemap');
      if (chk && !chk.checked) {{
        chk.checked = true;
        toggleBasemap(true);
      }}
    }}

    // =========================================================================
    // 1. 261 HEXAGON CHOROPLETH CELLS LAYER (PURE VECTOR SVG)
    // =========================================================================
    function styleFeature(feature) {{
      let fillColor = feature.properties.color_plurality;
      if (currentMode === 'margin') {{
        fillColor = feature.properties.color_margin;
      }} else if (currentMode === 'close') {{
        fillColor = feature.properties.diff <= 2.0 ? '#EAA86D' : '#DED9CE';
      }} else if (currentMode === 'density') {{
        fillColor = feature.properties.color_density;
      }}

      // City filter opacity
      let fillOpacity = 0.96;
      if (selectedCity && feature.properties.kota !== selectedCity) {{
        fillOpacity = 0.18;
      }}

      return {{
        renderer: svgRenderer,
        fillColor: fillColor,
        weight: 1.2,
        opacity: 1,
        color: '#F4F0E8',
        fillOpacity: fillOpacity
      }};
    }}

    let geojsonLayer = L.geoJSON(geojsonData, {{
      renderer: svgRenderer,
      style: styleFeature,
      onEachFeature: function(feature, layer) {{
        const p = feature.properties;
        const normName = p.kelurahan.toUpperCase().replace(/[^A-Z0-9]/g, '');
        kelLayersMap[normName] = layer;
        
        let p1Bold = p.winner === "Anies - Muhaimin" ? "lead" : "";
        let p2Bold = p.winner === "Prabowo - Gibran" ? "lead" : "";
        let p3Bold = p.winner === "Ganjar - Mahfud" ? "lead" : "";
        
        const tooltipContent = `
          <div class="dw-tt-title">${{p.kelurahan}}</div>
          <div class="dw-tt-sub">${{p.kecamatan}}, ${{p.kota}} &middot; <b>${{p.margin_str}}</b></div>
          
          <div class="dw-tt-row ${{p1Bold}}">
            <span>01 Anies - Muhaimin</span>
            <span>${{p.pct_anies}}% (${{p.votes_anies.toLocaleString()}})</span>
          </div>
          <div class="dw-tt-bar-wrap">
            <div class="dw-tt-bar-fill" style="width: ${{p.pct_anies}}%; background: var(--c-anies);"></div>
          </div>

          <div class="dw-tt-row ${{p2Bold}}">
            <span>02 Prabowo - Gibran</span>
            <span>${{p.pct_prabowo}}% (${{p.votes_prabowo.toLocaleString()}})</span>
          </div>
          <div class="dw-tt-bar-wrap">
            <div class="dw-tt-bar-fill" style="width: ${{p.pct_prabowo}}%; background: var(--c-prabowo);"></div>
          </div>

          <div class="dw-tt-row ${{p3Bold}}">
            <span>03 Ganjar - Mahfud</span>
            <span>${{p.pct_ganjar}}% (${{p.votes_ganjar.toLocaleString()}})</span>
          </div>
          <div class="dw-tt-bar-wrap">
            <div class="dw-tt-bar-fill" style="width: ${{p.pct_ganjar}}%; background: var(--c-ganjar);"></div>
          </div>

          <div class="dw-tt-total">
            <span>Total Valid Ballots</span>
            <span>${{p.total_votes.toLocaleString()}}</span>
          </div>
        `;

        layer.bindTooltip(tooltipContent, {{
          sticky: true,
          direction: 'auto',
          className: 'dw-custom-tooltip'
        }});

        layer.on('mouseover', function(e) {{
          layer.setStyle({{
            weight: 3,
            color: '#111111',
            fillOpacity: 1
          }});
          layer.bringToFront();
        }});

        layer.on('mouseout', function(e) {{
          geojsonLayer.resetStyle(layer);
        }});
      }}
    }}).addTo(map);

    // Dedicated Pane for City Boundaries (Pure Solid White, without black outline)
    map.createPane('cityBordersPane');
    map.getPane('cityBordersPane').style.zIndex = 450;
    map.getPane('cityBordersPane').style.pointerEvents = 'none';

    // Solid Bold Pure White City Boundaries Layer
    const borderLayer = L.geoJSON(bordersData, {{
      pane: 'cityBordersPane',
      renderer: svgRenderer,
      style: {{
        color: '#FFFFFF',
        weight: 4.5,
        opacity: 1.0,
        lineCap: 'round',
        lineJoin: 'round'
      }}
    }}).addTo(map);

    // =========================================================================
    // 2. PERIMETER CITY BADGES (JAKARTA 5 MAINLAND CITIES)
    // =========================================================================
    const perimeterCityLabels = [
      {{
        name: "North Jakarta",
        count: "31 Villages",
        kota: "JAKARTA UTARA",
        color: "#486E8D",
        lat: -6.0460,
        lng: 106.8555
      }},
      {{
        name: "West Jakarta",
        count: "56 Villages",
        kota: "JAKARTA BARAT",
        color: "#486E8D",
        lat: -6.1428,
        lng: 106.6360
      }},
      {{
        name: "Central Jakarta",
        count: "44 Villages",
        kota: "JAKARTA PUSAT",
        color: "#AF4D64",
        lat: -6.0964,
        lng: 106.8421
      }},
      {{
        name: "East Jakarta",
        count: "65 Villages",
        kota: "JAKARTA TIMUR",
        color: "#AF4D64",
        lat: -6.1555,
        lng: 107.0380
      }},
      {{
        name: "South Jakarta",
        count: "65 Villages",
        kota: "JAKARTA SELATAN",
        color: "#AF4D64",
        lat: -6.2980,
        lng: 106.8120
      }}
    ];

    perimeterCityLabels.forEach(c => {{
      const customIcon = L.divIcon({{
        className: 'custom-perimeter-icon',
        html: `
          <div class="city-perimeter-label" onclick="filterCity('${{c.kota}}')">
            <span class="c-line" style="background:${{c.color}}"></span>
            <span class="c-name">${{c.name}}</span>
            <span class="c-badge">${{c.count}}</span>
          </div>
        `,
        iconSize: [175, 28],
        iconAnchor: [87, 14]
      }});

      L.marker([c.lat, c.lng], {{ icon: customIcon, interactive: true }}).addTo(map);
    }});

    // Satellite region badges removed as requested

    // Function to calculate and fit all elements in center
    function centerMapBounds() {{
      const symmetricBounds = L.latLngBounds(
        L.latLng(-6.355, 106.595),
        L.latLng(-6.005, 107.085)
      );
      map.fitBounds(symmetricBounds, {{
        padding: [10, 10],
        maxZoom: 14,
        animate: false
      }});
    }}

    centerMapBounds();

    // Switch View modes
    function switchView(mode) {{
      currentMode = mode;
      document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
      
      const title = document.getElementById('legendTitle');
      const items = document.getElementById('legendItems');

      if (mode === 'plurality') {{
        document.getElementById('btnPlurality').classList.add('active');
        title.innerHTML = 'Most common candidate preference by urban village:';
        items.innerHTML = `
          <li class="legend-row" onmouseenter="highlightLegendCategory('prabowo')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: var(--c-prabowo);"></span><span><b>Prabowo - Gibran</b> (Northern ports & Western commercial districts)</span></li>
          <li class="legend-row" onmouseenter="highlightLegendCategory('anies')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: var(--c-anies);"></span><span><b>Anies - Muhaimin</b> (Eastern & Southern residential belts)</span></li>
          <li class="legend-row" onmouseenter="highlightLegendCategory('close')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: var(--c-close);"></span><span><b>Close contest</b> (&lt;2.0% difference between 01 & 02)</span></li>
          <li class="legend-row" onmouseenter="highlightLegendCategory('ganjar')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: var(--c-ganjar);"></span><span><b>Ganjar - Mahfud</b></span></li>
        `;
      }} else if (mode === 'margin') {{
        document.getElementById('btnMargin').classList.add('active');
        title.innerHTML = 'Victory margin strength across urban villages:';
        items.innerHTML = `
          <li class="legend-row" onmouseenter="highlightLegendMargin('anies-high')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: #782438;"></span><span><b>Anies &gt;15% Lead</b> (Decisive landslide)</span></li>
          <li class="legend-row" onmouseenter="highlightLegendMargin('anies-mod')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: #CD7286;"></span><span><b>Anies 2-7% Lead</b> (Moderate lead)</span></li>
          <li class="legend-row" onmouseenter="highlightLegendCategory('close')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: #EAA86D;"></span><span><b>Close Margin (&lt;2%)</b> (Swing battleground)</span></li>
          <li class="legend-row" onmouseenter="highlightLegendMargin('prabowo-mod')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: #A2C0D9;"></span><span><b>Prabowo 2-7% Lead</b> (Moderate lead)</span></li>
          <li class="legend-row" onmouseenter="highlightLegendMargin('prabowo-high')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: #486E8D;"></span><span><b>Prabowo &gt;15% Lead</b> (Decisive stronghold)</span></li>
        `;
      }} else if (mode === 'close') {{
        document.getElementById('btnClose').classList.add('active');
        title.innerHTML = 'Close battleground contests (Victory margin &lt; 2.0%):';
        items.innerHTML = `
          <li class="legend-row"><span class="legend-chip" style="background: #EAA86D;"></span><span><b>Battleground Urban Villages (33 Villages, 12.6%)</b></span></li>
          <li class="legend-row"><span class="legend-chip" style="background: #DED9CE;"></span><span>Decisive margin (&gt;2.0%)</span></li>
        `;
      }} else if (mode === 'density') {{
        document.getElementById('btnDensity').classList.add('active');
        title.innerHTML = 'Total valid ballot volume (Voter turnout density):';
        items.innerHTML = `
          <li class="legend-row"><span class="legend-chip" style="background: #2D4B66;"></span><span><b>Very High Density (&gt;40,000 ballots)</b> (e.g. Kapuk, Penggilingan)</span></li>
          <li class="legend-row"><span class="legend-chip" style="background: #537D9F;"></span><span><b>High Density (25,000 - 40,000 ballots)</b></span></li>
          <li class="legend-row"><span class="legend-chip" style="background: #8CAFC8;"></span><span><b>Moderate Density (15,000 - 25,000 ballots)</b></span></li>
          <li class="legend-row"><span class="legend-chip" style="background: #C5D8E6;"></span><span><b>Low Density (&lt;15,000 ballots)</b> (e.g. Gambir, Roa Malaka)</span></li>
        `;
      }}

      geojsonLayer.eachLayer(l => geojsonLayer.resetStyle(l));
    }}

    // Dynamic Spectrum Bar Update on City Filter
    function updateSpectrumBar(cityName) {{
      let anies = 0, prabowo = 0, close = 0, ganjar = 0, total = 0;
      
      geojsonData.features.forEach(f => {{
        if (!cityName || f.properties.kota === cityName) {{
          total++;
          const w = f.properties.winner;
          if (w.includes("Close")) close++;
          else if (w.includes("Anies")) anies++;
          else if (w.includes("Prabowo")) prabowo++;
          else if (w.includes("Ganjar")) ganjar++;
        }}
      }});

      const pAnies = ((anies / total) * 100).toFixed(1);
      const pClose = ((close / total) * 100).toFixed(1);
      const pPrabowo = ((prabowo / total) * 100).toFixed(1);
      const pGanjar = ((ganjar / total) * 100).toFixed(1);

      document.getElementById('specAnies').style.width = pAnies + '%';
      document.getElementById('specClose').style.width = pClose + '%';
      document.getElementById('specPrabowo').style.width = pPrabowo + '%';
      document.getElementById('specGanjar').style.width = pGanjar + '%';

      document.getElementById('lblAnies').innerText = `${{anies}} Vil (${{pAnies}}%)`;
      document.getElementById('lblClose').innerText = `${{close}} Vil (${{pClose}}%)`;
      document.getElementById('lblPrabowo').innerText = `${{prabowo}} Vil (${{pPrabowo}}%)`;

      const titlePrefix = cityName ? cityName : "Urban Village";
      document.getElementById('spectrumTitle').innerText = `${{titlePrefix}} Distribution Breakdown (${{total}} Kelurahan total):`;
    }}

    let currentFocusedLayer = null;

    // Filter City (with All Jakarta reset support & dynamic spectrum)
    function filterCity(cityName) {{
      selectedCity = cityName;
      if (currentFocusedLayer) {{
        currentFocusedLayer.closeTooltip();
        currentFocusedLayer = null;
      }}
      geojsonLayer.eachLayer(l => {{
        l.closeTooltip();
      }});

      document.querySelectorAll('.city-card').forEach(c => c.classList.remove('active'));

      if (!cityName) {{
        document.getElementById('card-ALL').classList.add('active');
      }} else {{
        const cardId = 'card-' + cityName.replace(' ', '-');
        const cardElem = document.getElementById(cardId);
        if (cardElem) cardElem.classList.add('active');
      }}
      geojsonLayer.eachLayer(l => geojsonLayer.resetStyle(l));
      updateSpectrumBar(cityName);
    }}

    // Enhanced Autocomplete & Search with Fly-To Pulse Focus
    function handleSearchInput(query) {{
      const q = query.trim().toUpperCase();
      const clearBtn = document.getElementById('searchClearBtn');
      const dropdown = document.getElementById('searchDropdown');
      if (clearBtn) clearBtn.style.display = q ? 'flex' : 'none';

      if (!q) {{
        if (dropdown) dropdown.style.display = 'none';
        geojsonLayer.eachLayer(l => {{
          geojsonLayer.resetStyle(l);
          l.closeTooltip();
        }});
        return;
      }}

      // Filter matching kelurahan
      const matches = [];
      geojsonData.features.forEach(f => {{
        const kel = f.properties.kelurahan;
        const kec = f.properties.kecamatan;
        const kota = f.properties.kota;
        if (kel.toUpperCase().includes(q) || kec.toUpperCase().includes(q)) {{
          matches.push(f.properties);
        }}
      }});

      // Render autocomplete dropdown
      if (dropdown) {{
        if (matches.length > 0) {{
          dropdown.innerHTML = matches.slice(0, 7).map(m => `
            <div class="search-dropdown-item" onclick="selectSearchedKelurahan('${{m.kelurahan}}')">
              <span class="item-name">${{m.kelurahan}}</span>
              <span class="item-meta">${{m.kecamatan}}, ${{m.kota}}</span>
            </div>
          `).join('');
          dropdown.style.display = 'block';
        }} else {{
          dropdown.innerHTML = '<div class="search-dropdown-item" style="color:#888; cursor:default;">No matching urban village found</div>';
          dropdown.style.display = 'block';
        }}
      }}

      // Highlight matched hexes on map
      geojsonLayer.eachLayer(layer => {{
        const name = layer.feature.properties.kelurahan.toUpperCase();
        const kec = layer.feature.properties.kecamatan.toUpperCase();
        if (name.includes(q) || kec.includes(q)) {{
          layer.setStyle({{
            weight: 3.5,
            color: '#000000',
            fillOpacity: 1
          }});
          layer.bringToFront();
        }} else {{
          layer.setStyle({{
            fillOpacity: 0.15,
            weight: 0.5,
            color: '#EEE'
          }});
          layer.closeTooltip();
        }}
      }});
    }}

    function handleSearchKeydown(e) {{
      if (e.key === 'Enter') {{
        const dropdown = document.getElementById('searchDropdown');
        const firstItem = dropdown ? dropdown.querySelector('.search-dropdown-item') : null;
        if (firstItem && firstItem.querySelector('.item-name')) {{
          selectSearchedKelurahan(firstItem.querySelector('.item-name').innerText);
        }}
      }} else if (e.key === 'Escape') {{
        clearSearch();
      }}
    }}

    function selectSearchedKelurahan(kelName) {{
      const input = document.getElementById('kelSearchInput');
      const dropdown = document.getElementById('searchDropdown');
      if (input) input.value = kelName;
      if (dropdown) dropdown.style.display = 'none';
      focusKelurahan(kelName);
    }}

    function clearSearch() {{
      const input = document.getElementById('kelSearchInput');
      const dropdown = document.getElementById('searchDropdown');
      if (input) input.value = '';
      if (dropdown) dropdown.style.display = 'none';
      const clearBtn = document.getElementById('searchClearBtn');
      if (clearBtn) clearBtn.style.display = 'none';

      if (currentFocusedLayer) {{
        currentFocusedLayer.closeTooltip();
        currentFocusedLayer = null;
      }}
      geojsonLayer.eachLayer(l => {{
        geojsonLayer.resetStyle(l);
        l.closeTooltip();
      }});
    }}

    // Hide dropdown on document click
    document.addEventListener('click', function(e) {{
      const searchBox = document.querySelector('.search-box-wrap');
      const dropdown = document.getElementById('searchDropdown');
      if (dropdown && searchBox && !searchBox.contains(e.target)) {{
        dropdown.style.display = 'none';
      }}
    }});

    // Click-to-Focus on Extremes cards (Strict Single Tooltip Focus)
    function focusKelurahan(kelName) {{
      const norm = kelName.toUpperCase().replace(/[^A-Z0-9]/g, '');
      const layer = kelLayersMap[norm];

      // Close all existing open tooltips and reset previous styles
      if (currentFocusedLayer) {{
        currentFocusedLayer.closeTooltip();
        currentFocusedLayer = null;
      }}
      geojsonLayer.eachLayer(l => {{
        geojsonLayer.resetStyle(l);
        l.closeTooltip();
      }});

      if (layer) {{
        currentFocusedLayer = layer;
        layer.setStyle({{
          weight: 4.5,
          color: '#111111',
          fillOpacity: 1
        }});
        layer.bringToFront();
        layer.openTooltip();
        
        // Scroll map smoothly into view if needed
        const mapElem = document.getElementById('mapViewport');
        if (mapElem) {{
          mapElem.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
      }}
    }}

    // Close open focused tooltip when clicking map background
    map.on('click', function() {{
      if (currentFocusedLayer) {{
        currentFocusedLayer.closeTooltip();
        geojsonLayer.resetStyle(currentFocusedLayer);
        currentFocusedLayer = null;
      }}
    }});

    // Legend Hover Highlighting
    function highlightLegendCategory(category) {{
      geojsonLayer.eachLayer(layer => {{
        const w = layer.feature.properties.winner;
        let match = false;
        if (category === 'prabowo' && w.includes('Prabowo')) match = true;
        if (category === 'anies' && w.includes('Anies')) match = true;
        if (category === 'close' && w.includes('Close')) match = true;
        if (category === 'ganjar' && w.includes('Ganjar')) match = true;

        if (match) {{
          layer.setStyle({{ fillOpacity: 1, weight: 2, color: '#111' }});
          layer.bringToFront();
        }} else {{
          layer.setStyle({{ fillOpacity: 0.18, weight: 0.5, color: '#DDD' }});
        }}
      }});
    }}

    function highlightLegendMargin(marginCat) {{
      geojsonLayer.eachLayer(layer => {{
        const p = layer.feature.properties;
        let match = false;
        if (marginCat === 'anies-high' && p.pct_anies > p.pct_prabowo && p.diff > 15) match = true;
        if (marginCat === 'anies-mod' && p.pct_anies > p.pct_prabowo && p.diff >= 2 && p.diff <= 15) match = true;
        if (marginCat === 'prabowo-mod' && p.pct_prabowo > p.pct_anies && p.diff >= 2 && p.diff <= 15) match = true;
        if (marginCat === 'prabowo-high' && p.pct_prabowo > p.pct_anies && p.diff > 15) match = true;

        if (match) {{
          layer.setStyle({{ fillOpacity: 1, weight: 2, color: '#111' }});
          layer.bringToFront();
        }} else {{
          layer.setStyle({{ fillOpacity: 0.18, weight: 0.5, color: '#DDD' }});
        }}
      }});
    }}

    function resetLegendHighlight() {{
      geojsonLayer.eachLayer(l => geojsonLayer.resetStyle(l));
    }}

    // Keyboard 'Escape' listener to reset all filters
    window.addEventListener('keydown', function(e) {{
      if (e.key === 'Escape') {{
        clearSearch();
        filterCity(null);
      }}
    }});

    // Bulletproof High-Res Poster Export with Pure Vector Rasterization
    function exportPoster() {{
      const btn = document.getElementById('btnExport');
      btn.innerText = '⏳ Rendering 4K Poster...';
      btn.style.opacity = '0.7';

      // 1. Temporarily scroll window to top
      const originalScrollY = window.scrollY;
      window.scrollTo(0, 0);

      // 2. Refresh Leaflet map and force exact symmetrical center bounds
      map.invalidateSize();
      centerMapBounds();

      setTimeout(() => {{
        const poster = document.getElementById('posterContent');

        html2canvas(poster, {{
          scale: 4, // TRUE 4K ULTRA-HIGH-RESOLUTION (~3,920px width)
          useCORS: true,
          allowTaint: true,
          scrollX: 0,
          scrollY: 0,
          backgroundColor: '#F6F3EE',
          logging: false,
          onclone: function(clonedDoc) {{
            // Hide the export button on the exported image
            const clonedBtn = clonedDoc.getElementById('btnExport');
            if (clonedBtn) clonedBtn.style.display = 'none';

            // Flatten Leaflet 3D transforms to 2D absolute positioning for pixel-perfect alignment
            const mapPane = clonedDoc.querySelector('.leaflet-map-pane');
            if (mapPane) {{
              const transform = window.getComputedStyle(mapPane).transform;
              if (transform && transform !== 'none') {{
                const match = transform.match(/matrix\(([^)]+)\)/);
                if (match) {{
                  const parts = match[1].split(',').map(s => parseFloat(s.trim()));
                  if (parts.length === 6) {{
                    mapPane.style.left = parts[4] + 'px';
                    mapPane.style.top = parts[5] + 'px';
                    mapPane.style.transform = 'none';
                  }}
                }}
              }}
            }}

            // Ensure SVG vector layer preserves sharp vector bounds without clipping
            const svgElem = clonedDoc.querySelector('.leaflet-overlay-pane svg');
            if (svgElem) {{
              svgElem.style.transform = 'none';
            }}
          }}
        }}).then(canvas => {{
          const link = document.createElement('a');
          link.download = 'The_Sound_of_Jakarta_Election_Map_4K.png';
          link.href = canvas.toDataURL('image/png', 1.0);
          link.click();
          btn.innerText = '📸 Export PNG';
          btn.style.opacity = '1';
          window.scrollTo(0, originalScrollY);
        }}).catch(err => {{
          console.error('Export error:', err);
          btn.innerText = '📸 Export PNG';
          btn.style.opacity = '1';
          window.scrollTo(0, originalScrollY);
          alert('Export error, please try again.');
        }});
      }}, 400);
    }}
  </script>
</body>
</html>
'''

output_path = os.path.join(BASE_DIR, "index.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Masterpiece with all interactive polish features compiled successfully: {output_path}")
