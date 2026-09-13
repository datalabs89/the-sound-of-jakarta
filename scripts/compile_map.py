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
# Track city statistics for summary cards
city_stats = defaultdict(lambda: {"anies_v": 0, "prabowo_v": 0, "ganjar_v": 0, "anies_kel": 0, "prabowo_kel": 0, "ganjar_kel": 0, "close_kel": 0, "total_kel": 0})

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

        # Accurate Candidate Ranking (1st, 2nd, 3rd place)
        candidates = [
            {"code": "01", "name": "Anies - Muhaimin", "pct": p1, "votes": v1, "color": "#AF4D64"},
            {"code": "02", "name": "Prabowo - Gibran", "pct": p2, "votes": v2, "color": "#7CA1BF"},
            {"code": "03", "name": "Ganjar - Mahfud", "pct": p3, "votes": v3, "color": "#75556B"}
        ]
        candidates.sort(key=lambda x: (x["pct"], x["votes"]), reverse=True)
        first, second, third = candidates[0], candidates[1], candidates[2]

        diff = round(first["pct"] - second["pct"], 2)
        vote_diff = first["votes"] - second["votes"]
        lead_code = first["code"]
        lead_name = first["name"]
        
        # Accumulate city stats
        c_stat = city_stats[city]
        c_stat["total_kel"] += 1
        c_stat["anies_v"] += v1
        c_stat["prabowo_v"] += v2
        c_stat["ganjar_v"] += v3
        if diff <= 2.0:
            c_stat["close_kel"] += 1
        elif lead_code == "01":
            c_stat["anies_kel"] += 1
        elif lead_code == "02":
            c_stat["prabowo_kel"] += 1
        else:
            c_stat["ganjar_kel"] += 1
        
        # Plurality default
        if diff <= 2.0:
            winner_label = "Close Contest (<2% margin)"
            color = "#EAA86D"
        else:
            winner_label = lead_name
            color = first["color"]
            
        # Margin color shade and description
        if diff <= 2.0:
            margin_color = "#EAA86D"
            margin_str = f"Close: {lead_code} +{diff:.1f}% ({vote_diff:,} votes)" if vote_diff > 1 else f"Close: {lead_code} +{diff:.2f}% (1 vote)"
        elif lead_code == "01":
            margin_str = f"01 Leads +{diff:.1f}%"
            if diff > 15.0: margin_color = "#782438"
            elif diff > 7.0: margin_color = "#AF4D64"
            else: margin_color = "#CD7286"
        elif lead_code == "02":
            margin_str = f"02 Leads +{diff:.1f}%"
            if diff > 15.0: margin_color = "#486E8D"
            elif diff > 7.0: margin_color = "#7CA1BF"
            else: margin_color = "#A2C0D9"
        else:  # 03 Ganjar
            margin_str = f"03 Leads +{diff:.1f}%"
            if diff > 15.0: margin_color = "#52364B"
            elif diff > 7.0: margin_color = "#75556B"
            else: margin_color = "#9A7B90"

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
        vote_diff = 0
        lead_code = "02"
        lead_name = "Prabowo - Gibran"
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
            "leader_code": lead_code,
            "leader_name": lead_name,
            "pct_anies": p1,
            "pct_prabowo": p2,
            "pct_ganjar": p3,
            "votes_anies": v1,
            "votes_prabowo": v2,
            "votes_ganjar": v3,
            "total_votes": total,
            "diff": diff,
            "vote_diff": vote_diff,
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
ganjar_wins = sum(1 for f in features if "Ganjar" in f["properties"]["winner"] and "Close" not in f["properties"]["winner"])
close_wins = sum(1 for f in features if "Close" in f["properties"]["winner"])

pct_anies_total = round(total_anies / total_votes * 100, 2)
pct_prabowo_total = round(total_prabowo / total_votes * 100, 2)
pct_ganjar_total = round(total_ganjar / total_votes * 100, 2)

pct_anies_kel = round(anies_wins / len(features) * 100, 1)
pct_prabowo_kel = round(prabowo_wins / len(features) * 100, 1)
pct_ganjar_kel = round(ganjar_wins / len(features) * 100, 1)
pct_close_kel = round(close_wins / len(features) * 100, 1)

html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The Voice of Jakarta | 2024 Presidential Election</title>
  
  <!-- SEO & Social OpenGraph Meta Tags -->
  <meta name="description" content="The Voice of Jakarta: A high-density tessellated hexagonal cartogram analyzing candidate voting patterns across 261 mainland urban villages in the 2024 Indonesian Presidential Election.">
  <meta name="keywords" content="Jakarta Election 2024, Pilpres 2024 Jakarta, Hex Cartogram, Jakarta Datawrapper, Peta Pilpres Jakarta, KawalPemilu, Tedy Iskandar">
  <meta name="author" content="Tedy Iskandar">
  
  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://datalabs89.github.io/the-sound-of-jakarta/">
  <meta property="og:title" content="The Voice of Jakarta | 2024 Presidential Election Cartogram">
  <meta property="og:description" content="Interactive tessellated hexagonal election cartogram covering 261 mainland urban villages of DKI Jakarta. Explore victory margins, plurality winners, and turnout density.">
  <meta property="og:image" content="https://datalabs89.github.io/the-sound-of-jakarta/The_Sound_of_Jakarta_Election_Map_4K.png">

  <!-- Twitter / X -->
  <meta property="twitter:card" content="summary_large_image">
  <meta property="twitter:url" content="https://datalabs89.github.io/the-sound-of-jakarta/">
  <meta property="twitter:title" content="The Voice of Jakarta | 2024 Presidential Election Cartogram">
  <meta property="twitter:description" content="Interactive tessellated hexagonal election cartogram covering 261 mainland urban villages of DKI Jakarta. Explore victory margins, plurality winners, and turnout density.">
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
      max-width: 1040px;
      background-color: var(--dw-canvas);
      background-image: 
        radial-gradient(#ECE7DE 15%, transparent 16%),
        radial-gradient(#EEE9E0 15%, transparent 16%);
      background-size: 60px 60px;
      background-position: 0 0, 30px 30px;
      border: 1px solid #D6CEBE;
      box-shadow: 0 20px 60px rgba(0,0,0,0.13);
      padding: 44px 44px 36px 44px;
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
      justify-content: center;
      gap: 6px;
      padding: 6px 14px;
      background: #FFFFFF;
      border: 1.5px solid #111111;
      border-radius: 3px;
      font-size: 0.78rem;
      font-weight: 700;
      color: #111111;
      cursor: pointer;
      transition: all 0.15s ease;
      font-family: inherit;
      white-space: nowrap;
      text-decoration: none;
      box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }}

    .export-btn:hover {{
      background: #111111;
      color: #FFFFFF;
      box-shadow: 0 3px 8px rgba(0,0,0,0.15);
      transform: translateY(-1px);
    }}

    .export-btn:active {{
      transform: translateY(0);
      box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }}

    h1.dw-headline {{
      font-family: 'Libre Baskerville', Georgia, serif;
      font-size: 2.95rem;
      font-weight: 700;
      line-height: 1.10;
      letter-spacing: -0.012em;
      word-spacing: 0.055em;
      font-kerning: normal;
      text-rendering: optimizeLegibility;
      font-feature-settings: "kern" 1, "liga" 1;
      text-wrap: balance;
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
      grid-template-columns: repeat(6, 1fr);
      gap: 8px;
      margin-bottom: 20px;
    }}

    .city-card {{
      background: rgba(255, 255, 255, 0.94);
      border: 1.5px solid #D8D1C4;
      border-radius: 4px;
      padding: 10px 6px 8px 6px;
      text-align: center;
      transition: all 0.15s ease;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: space-between;
      min-height: 86px;
      box-sizing: border-box;
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
    .city-card.all-city.active .city-card-count {{
      color: #FFFFFF !important;
    }}
    .city-card.all-city.active .city-card-lead {{
      background: rgba(255, 255, 255, 0.18);
      border-color: rgba(255, 255, 255, 0.35);
      color: #FFFFFF !important;
    }}
    .city-card.all-city.active .lead-primary,
    .city-card.all-city.active .lead-secondary {{
      color: #FFFFFF !important;
    }}

    .city-card-name {{
      font-size: 0.77rem;
      font-weight: 800;
      letter-spacing: 0.03em;
      text-transform: uppercase;
      color: #111;
      margin-bottom: 2px;
      line-height: 1.2;
      text-align: center;
      white-space: nowrap;
    }}

    .city-card-count {{
      font-size: 0.70rem;
      color: #6E685E;
      font-weight: 600;
      margin-bottom: 6px;
      white-space: nowrap;
    }}

    .city-card-lead {{
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      width: 100%;
      padding: 4px 4px;
      border-radius: 3px;
      line-height: 1.25;
      box-sizing: border-box;
      gap: 1px;
    }}

    .city-card-lead.prabowo {{
      background: #EBF1F6;
      color: #2D506F;
      border: 1px solid #D2DFEB;
    }}
    .city-card-lead.anies {{
      background: #F8EDEF;
      color: #782438;
      border: 1px solid #ECD2D8;
    }}
    .city-card-lead.all {{
      background: #ECE7DF;
      color: #333333;
      border: 1px solid #D8D1C4;
    }}

    .lead-primary {{
      font-size: 0.73rem;
      font-weight: 800;
      white-space: nowrap;
    }}

    .lead-secondary {{
      font-size: 0.66rem;
      font-weight: 600;
      white-space: nowrap;
      opacity: 0.85;
    }}

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
      font-size: 0.68rem;
      font-weight: 700;
      color: #666056;
      background: #EFECE5;
      border: 1px solid #DFD9CE;
      padding: 2px 7px;
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

    .dw-icon {{
      display: inline-block;
      vertical-align: middle;
      filter: grayscale(100%) !important;
      -webkit-filter: grayscale(100%) !important;
      color: currentColor;
      flex-shrink: 0;
    }}

    .search-icon {{
      position: absolute;
      left: 11px;
      top: 50%;
      transform: translateY(-50%);
      color: #666666;
      pointer-events: none;
      display: flex;
      align-items: center;
      justify-content: center;
      filter: grayscale(100%) !important;
      -webkit-filter: grayscale(100%) !important;
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
      opacity: 0.55;
      filter: grayscale(100%) contrast(88%) brightness(102%);
    }}

    /* HEXAGON DYNAMIC TEXT LABELS (P2) */
    .hex-label-item {{
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      pointer-events: none !important;
    }}

    .hex-label-text {{
      font-family: 'IBM Plex Sans', -apple-system, sans-serif;
      font-size: 8px;
      font-weight: 700;
      color: #111111;
      text-shadow: 
        -1.5px -1.5px 0 #FFFFFF,  
         1.5px -1.5px 0 #FFFFFF,
        -1.5px  1.5px 0 #FFFFFF,
         1.5px  1.5px 0 #FFFFFF,
         0 0 3px #FFFFFF;
      text-align: center;
      line-height: 1.05;
      white-space: nowrap;
      pointer-events: none;
      user-select: none;
      letter-spacing: -0.02em;
      transition: opacity 0.2s ease, font-size 0.15s ease;
    }}

    .labels-toggle-wrap {{
      display: flex;
      align-items: center;
      gap: 5px;
      font-size: 0.74rem;
      font-weight: 700;
      color: #333333;
      background: #ECE7DE;
      padding: 5px 9px;
      border-radius: 3px;
      border: 1px solid #D6CEBE;
      cursor: pointer;
      user-select: none;
      transition: all 0.15s ease;
    }}

    .labels-toggle-wrap:hover {{
      background: #E4DEC5;
    }}

    /* MOBILE BOTTOM SHEET DRAWER (P2 UX ENHANCEMENT) */
    .drawer-backdrop {{
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.38);
      z-index: 9998;
      backdrop-filter: blur(2px);
      -webkit-backdrop-filter: blur(2px);
      opacity: 0;
      transition: opacity 0.25s ease;
    }}

    .drawer-backdrop.active {{
      display: block;
      opacity: 1;
    }}

    .mobile-drawer {{
      display: none;
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: #FFFFFF;
      border-top: 1.5px solid #D6CEBE;
      border-radius: 16px 16px 0 0;
      box-shadow: 0 -6px 30px rgba(0, 0, 0, 0.22);
      z-index: 9999;
      padding: 12px 18px 24px 18px;
      transform: translateY(105%);
      transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1);
      max-height: 75vh;
      overflow-y: auto;
      font-family: 'IBM Plex Sans', -apple-system, sans-serif;
    }}

    .mobile-drawer.active {{
      transform: translateY(0);
    }}

    .drawer-drag-pill {{
      width: 36px;
      height: 4.5px;
      background: #D8D2C5;
      border-radius: 3px;
      margin: 0 auto 12px auto;
      cursor: pointer;
    }}

    .drawer-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: clamp(8px, 1.5vw, 12px);
      padding-bottom: clamp(6px, 1.2vw, 8px);
      border-bottom: 1px solid #ECE7DE;
      gap: 10px;
    }}

    .drawer-title-box {{
      flex: 1 1 auto;
      min-width: 0;
    }}

    .drawer-title {{
      font-family: 'Libre Baskerville', Georgia, serif;
      font-size: clamp(1.05rem, 3.8vw, 1.25rem);
      font-weight: 700;
      color: #111111;
      margin-bottom: 2px;
      line-height: 1.22;
      overflow-wrap: break-word;
    }}

    .drawer-sub {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 4px 8px;
      line-height: 1.30;
    }}

    .drawer-sub .tt-geo {{
      font-size: clamp(0.72rem, 2.2vw, 0.80rem);
      color: #555555;
      font-weight: 500;
      flex: 1 1 auto;
      min-width: 110px;
    }}

    .drawer-sub .tt-margin {{
      font-size: clamp(0.68rem, 2vw, 0.76rem);
      font-weight: 700;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
      color: #111111;
      background: #F2ECE1;
      padding: 2px 7px;
      border-radius: 3px;
      border: 1px solid #E2D9C8;
      display: inline-block;
      flex-shrink: 0;
      margin-left: auto;
    }}

    .drawer-close-btn {{
      background: #ECE7DE;
      border: none;
      border-radius: 50%;
      width: 30px;
      height: 30px;
      font-size: 13px;
      font-weight: 700;
      color: #444444;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.15s ease, transform 0.15s ease;
      flex-shrink: 0;
    }}

    .drawer-close-btn:hover {{
      background: #DDD5C7;
      transform: scale(1.08);
    }}

    @media (max-width: 768px) {{
      .mobile-drawer {{
        display: block;
      }}
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
      position: relative;
      z-index: 700;
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
    .leaflet-pane.leaflet-tooltip-pane {{
      z-index: 1000 !important;
    }}

    .leaflet-tooltip.dw-custom-tooltip {{
      background: #FFFFFF !important;
      border-radius: 4px !important;
      border: 1px solid #C4BCAC !important;
      box-shadow: 0 8px 28px rgba(0,0,0,0.16) !important;
      padding: clamp(10px, 1.4vw, 15px) clamp(12px, 1.8vw, 18px) !important;
      font-family: 'IBM Plex Sans', -apple-system, sans-serif !important;
      font-size: clamp(0.78rem, 1vw, 0.85rem) !important;
      color: #111111 !important;
      opacity: 1 !important;
      width: clamp(240px, 24vw, 315px) !important;
      max-width: calc(100vw - 32px) !important;
      box-sizing: border-box !important;
      white-space: normal !important;
      z-index: 1000 !important;
      pointer-events: none !important;
    }}

    .leaflet-tooltip-top:before, 
    .leaflet-tooltip-bottom:before, 
    .leaflet-tooltip-left:before, 
    .leaflet-tooltip-right:before,
    .leaflet-tooltip-top:after, 
    .leaflet-tooltip-bottom:after, 
    .leaflet-tooltip-left:after, 
    .leaflet-tooltip-right:after {{
      border: none !important;
      display: none !important;
    }}

    .dw-tt-title {{
      font-family: 'Libre Baskerville', Georgia, serif;
      font-size: clamp(0.95rem, 1.25vw, 1.12rem);
      font-weight: 700;
      color: #111111;
      margin-bottom: clamp(2px, 0.35vw, 4px);
      line-height: 1.22;
      letter-spacing: -0.01em;
      word-break: normal;
      overflow-wrap: break-word;
    }}

    .dw-tt-sub {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 4px 8px;
      border-bottom: 1px solid #ECE7DE;
      padding-bottom: clamp(4px, 0.6vw, 6px);
      margin-bottom: clamp(6px, 0.9vw, 9px);
      line-height: 1.30;
    }}

    .dw-tt-sub .tt-geo {{
      font-size: clamp(0.70rem, 0.95vw, 0.77rem);
      color: #555555;
      font-weight: 500;
      flex: 1 1 auto;
      min-width: 110px;
      letter-spacing: 0.01em;
    }}

    .dw-tt-sub .tt-margin {{
      font-size: clamp(0.67rem, 0.90vw, 0.74rem);
      font-weight: 700;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
      color: #111111;
      background: #F2ECE1;
      padding: 1.5px 6px;
      border-radius: 3px;
      border: 1px solid #E2D9C8;
      display: inline-block;
      flex-shrink: 0;
      margin-left: auto;
      letter-spacing: 0.01em;
    }}

    .dw-tt-row {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 6px;
      margin-bottom: clamp(3px, 0.5vw, 4px);
      font-size: clamp(0.78rem, 1vw, 0.84rem);
      line-height: 1.25;
    }}

    .dw-tt-row.lead {{
      font-weight: 700;
      color: #000000;
    }}

    .dw-tt-row .c-cand-name {{
      flex: 1 1 auto;
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-weight: 500;
      color: #222222;
      letter-spacing: -0.01em;
    }}

    .dw-tt-row.lead .c-cand-name {{
      font-weight: 700;
      color: #000000;
    }}

    .dw-tt-row .c-cand-val {{
      flex-shrink: 0;
      font-variant-numeric: tabular-nums;
      text-align: right;
      white-space: nowrap;
      font-size: clamp(0.77rem, 0.98vw, 0.83rem);
    }}

    .dw-tt-row .c-cand-val b {{
      font-weight: 700;
    }}

    .dw-tt-row .c-cand-votes {{
      font-size: clamp(0.67rem, 0.85vw, 0.74rem);
      color: #666666;
      font-weight: 500;
      margin-left: 3px;
      font-variant-numeric: tabular-nums;
    }}

    .dw-tt-row.lead .c-cand-votes {{
      color: #333333;
      font-weight: 600;
    }}

    .dw-tt-bar-wrap {{
      background: #EEE9DF;
      height: clamp(5px, 0.7vw, 6px);
      border-radius: 3px;
      overflow: hidden;
      margin-bottom: clamp(6px, 0.9vw, 8px);
    }}

    .dw-tt-bar-fill {{
      height: 100%;
      border-radius: 3px;
      transition: width 0.15s ease-out;
    }}

    .dw-tt-total {{
      border-top: 1px dashed #D6CEBE;
      margin-top: clamp(6px, 0.9vw, 8px);
      padding-top: clamp(5px, 0.7vw, 7px);
      font-size: clamp(0.68rem, 0.88vw, 0.75rem);
      color: #666666;
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      letter-spacing: 0.02em;
      text-transform: uppercase;
      font-weight: 600;
    }}

    .dw-tt-total span:first-child {{
      flex: 1 1 auto;
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}

    .dw-tt-total span:last-child {{
      flex-shrink: 0;
      font-size: clamp(0.76rem, 1vw, 0.83rem);
      font-weight: 700;
      color: #111111;
      font-variant-numeric: tabular-nums;
      margin-left: 8px;
      text-transform: none;
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

    .brand-logo-datalabs {{
      height: 36px;
      max-width: 140px;
      object-fit: contain;
      filter: grayscale(100%) opacity(0.80);
      transition: filter 0.2s ease, opacity 0.2s ease;
    }}

    .brand-logo-datalabs:hover {{
      filter: grayscale(100%) opacity(1.0);
    }}

    /* STRICT PUBLICATION GRAYSCALE FOR ALL ICONS & SVGS */
    .dw-icon,
    .search-icon,
    .search-icon svg,
    .export-btn svg,
    .brand-logo-datalabs {{
      filter: grayscale(100%) !important;
      -webkit-filter: grayscale(100%) !important;
    }}

    /* =========================================================================
       COMPREHENSIVE MULTI-DEVICE RESPONSIVE BREAKPOINTS (MOBILE / TABLET / DESKTOP)
       ========================================================================= */
    @media (max-width: 1080px) {{
      .dw-editorial-artboard {{
        padding: 28px 22px;
      }}
      .city-summary-grid {{
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
      }}
      #mapViewport {{
        height: 580px;
      }}
    }}

    @media (max-width: 768px) {{
      body {{
        padding: 8px 4px;
      }}
      .dw-editorial-artboard {{
        padding: 18px 12px;
        border-radius: 2px;
      }}
      .header-top-row {{
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }}
      .badge-top {{
        font-size: clamp(0.60rem, 1.8vw, 0.70rem);
        letter-spacing: 0.08em;
        line-height: 1.25;
        border-bottom-width: 1.5px;
        padding-bottom: 2px;
      }}
      .export-btn {{
        width: auto !important;
        max-width: fit-content !important;
        align-self: center;
        padding: 5px 12px;
        font-size: 0.72rem;
        gap: 5px;
        white-space: nowrap;
        flex-shrink: 0;
      }}
      h1.dw-headline {{
        font-size: clamp(1.65rem, 5.5vw, 2.25rem);
        letter-spacing: -0.01em;
        word-spacing: 0.045em;
        line-height: 1.14;
      }}
      .dw-subheadline {{
        font-size: 0.90rem;
        line-height: 1.45;
        margin-bottom: 16px;
      }}
      .stats-bar {{
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin-bottom: 16px;
      }}
      .stat-box {{
        padding: 10px 12px;
      }}
      .stat-val {{
        font-size: 1.25rem;
      }}
      .city-summary-grid {{
        grid-template-columns: repeat(2, 1fr);
        gap: 6px;
        margin-bottom: 16px;
      }}
      .city-card {{
        padding: 8px 6px;
      }}
      .city-card-name {{
        font-size: 0.78rem;
      }}
      .city-card-count {{
        font-size: 0.68rem;
      }}
      .storyline-strip, .extremes-strip {{
        grid-template-columns: 1fr;
        gap: 8px;
        margin-bottom: 16px;
      }}
      .toolbar-area {{
        flex-direction: column;
        align-items: stretch;
        gap: 10px;
        margin-bottom: 16px;
      }}
      .view-toggles {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px;
        width: 100%;
      }}
      .toggle-btn {{
        width: 100%;
        text-align: center;
        padding: 7px 6px;
        font-size: 0.75rem;
      }}
      .basemap-toggle-wrap {{
        width: 100%;
        justify-content: space-between;
        padding: 7px 10px;
        box-sizing: border-box;
      }}
      .search-box-wrap {{
        width: 100%;
        min-width: 100%;
      }}
      .search-input {{
        width: 100%;
        padding: 8px 30px 8px 32px;
        font-size: 0.85rem;
        box-sizing: border-box;
      }}
      .legend-card {{
        padding: 14px 12px;
        margin-bottom: 16px;
      }}
      .legend-list {{
        display: flex;
        flex-direction: column;
        gap: 6px;
      }}
      .spectrum-labels {{
        flex-wrap: wrap;
        gap: 6px;
        font-size: 0.70rem;
      }}
      #mapViewport {{
        height: 480px;
      }}
      .city-perimeter-label {{
        padding: 3px 7px;
        font-size: 0.70rem;
        gap: 4px;
      }}
      .city-perimeter-label .c-name {{
        font-size: 0.70rem;
      }}
      .city-perimeter-label .c-badge {{
        font-size: 0.65rem;
        padding: 1px 4px;
      }}
      .leaflet-tooltip.dw-custom-tooltip {{
        width: clamp(230px, 75vw, 290px) !important;
        padding: 11px 13px !important;
      }}
      .dw-footer {{
        flex-direction: column-reverse;
        gap: 14px;
        align-items: flex-start;
      }}
      .brand-logo-datalabs {{
        height: 30px;
      }}
    }}

    @media (max-width: 420px) {{
      .header-top-row {{
        gap: 6px;
      }}
      .badge-top {{
        font-size: 0.58rem;
        letter-spacing: 0.06em;
      }}
      .export-btn {{
        padding: 4px 10px;
        font-size: 0.69rem;
        gap: 4px;
      }}
      .stats-bar {{
        grid-template-columns: 1fr;
      }}
      .city-summary-grid {{
        grid-template-columns: 1fr 1fr;
      }}
      .leaflet-tooltip.dw-custom-tooltip {{
        width: clamp(210px, 86vw, 265px) !important;
        padding: 9px 11px !important;
      }}
      #mapViewport {{
        height: 400px;
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
        <button class="export-btn" id="btnExport" onclick="exportPoster()">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          <span id="btnExportText">Download</span>
        </button>
      </div>

      <h1 class="dw-headline">The Voice of Jakarta</h1>
      <p class="dw-subheadline">
        Across 261 mainland urban villages, Prabowo and Anies divide the capital's presidential electoral map
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
          <div class="stat-sub">Leading in <b>105</b> Villages (40.2%)</div>
        </div>

        <div class="stat-box">
          <div class="stat-label">03 Ganjar - Mahfud</div>
          <div class="stat-val">17.21% <span class="stat-sub">(966,547 votes)</span></div>
          <div class="stat-sub">Leading in <b>2</b> Villages (0.8%)</div>
        </div>

        <div class="stat-box">
          <div class="stat-label">Battleground (&lt;2% diff)</div>
          <div class="stat-val">35 <span class="stat-sub">Villages</span></div>
          <div class="stat-sub">13.4% of Mainland Jakarta</div>
        </div>
      </div>

      <!-- 6-COLUMN ADMINISTRATIVE CITY SUMMARY GRID -->
      <div class="city-summary-grid">
        <div class="city-card all-city active" id="card-ALL" onclick="filterCity(null)">
          <div class="city-card-name">All Jakarta</div>
          <div class="city-card-count">261 Villages</div>
          <div class="city-card-lead all">
            <span class="lead-primary">Complete Map</span>
            <span class="lead-secondary">5 Mainland Cities</span>
          </div>
        </div>

        <div class="city-card" id="card-JAKARTA-UTARA" onclick="filterCity('JAKARTA UTARA')">
          <div class="city-card-name">North Jakarta</div>
          <div class="city-card-count">31 Villages</div>
          <div class="city-card-lead prabowo">
            <span class="lead-primary">02 Lead &middot; 83.9%</span>
            <span class="lead-secondary">26 of 31 villages</span>
          </div>
        </div>

        <div class="city-card" id="card-JAKARTA-BARAT" onclick="filterCity('JAKARTA BARAT')">
          <div class="city-card-name">West Jakarta</div>
          <div class="city-card-count">56 Villages</div>
          <div class="city-card-lead prabowo">
            <span class="lead-primary">02 Lead &middot; 69.6%</span>
            <span class="lead-secondary">39 of 56 villages</span>
          </div>
        </div>

        <div class="city-card" id="card-JAKARTA-PUSAT" onclick="filterCity('JAKARTA PUSAT')">
          <div class="city-card-name">Central Jakarta</div>
          <div class="city-card-count">44 Villages</div>
          <div class="city-card-lead anies">
            <span class="lead-primary">01 Lead &middot; 54.5%</span>
            <span class="lead-secondary">24 of 44 villages</span>
          </div>
        </div>

        <div class="city-card" id="card-JAKARTA-TIMUR" onclick="filterCity('JAKARTA TIMUR')">
          <div class="city-card-name">East Jakarta</div>
          <div class="city-card-count">65 Villages</div>
          <div class="city-card-lead anies">
            <span class="lead-primary">01 Lead &middot; 61.5%</span>
            <span class="lead-secondary">40 of 65 villages</span>
          </div>
        </div>

        <div class="city-card" id="card-JAKARTA-SELATAN" onclick="filterCity('JAKARTA SELATAN')">
          <div class="city-card-name">South Jakarta</div>
          <div class="city-card-count">65 Villages</div>
          <div class="city-card-lead anies">
            <span class="lead-primary">01 Lead &middot; 75.4%</span>
            <span class="lead-secondary">49 of 65 villages</span>
          </div>
        </div>
      </div>

      <!-- DEDICATED STORYLINE STRIP -->
      <div class="storyline-strip">
        <div class="story-card prabowo">
          <strong><svg class="dw-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:-2px; margin-right:4px;"><circle cx="12" cy="5" r="3"/><line x1="12" y1="22" x2="12" y2="8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3"/></svg>Northern Ports & Western Belt:</strong>
          Prabowo-Gibran established decisive commanding leads across coastal industrial ports and western commercial urban villages.
        </div>
        <div class="story-card anies">
          <strong><svg class="dw-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:-2px; margin-right:4px;"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>Eastern & Southern Residential Bastion:</strong>
          Anies-Muhaimin captured substantial momentum across high-density residential belts in East and South Jakarta.
        </div>
      </div>

      <!-- KEY ELECTORAL EXTREMES STRIP WITH CLICK-TO-FOCUS -->
      <div class="extremes-strip">
        <div class="extreme-card" onclick="focusKelurahan('PAL MERIAM')" title="Click to locate Pal Meriam on map">
          <div class="ex-label">
            <span style="display:inline-flex; align-items:center; gap:4px;">
              <svg class="dw-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="22" y1="12" x2="18" y2="12"/><line x1="6" y1="12" x2="2" y2="12"/><line x1="12" y1="6" x2="12" y2="2"/><line x1="12" y1="22" x2="12" y2="18"/></svg>
              Closest Margin
            </span>
            <span class="ex-hint">Locate ↗</span>
          </div>
          <div class="ex-val">Pal Meriam (East Jkt)</div>
          <div class="ex-sub">0.01% diff &middot; Margin of 1 ballot</div>
        </div>

        <div class="extreme-card" onclick="focusKelurahan('SUKABUMI UTARA')" title="Click to locate Sukabumi Utara on map">
          <div class="ex-label">
            <span style="display:inline-flex; align-items:center; gap:4px;">
              <svg class="dw-icon" width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/></svg>
              Strongest 01 Bastion
            </span>
            <span class="ex-hint">Locate ↗</span>
          </div>
          <div class="ex-val">Sukabumi Utara (West Jkt)</div>
          <div class="ex-sub">Anies: 65.5% &middot; Margin +39.3%</div>
        </div>

        <div class="extreme-card" onclick="focusKelurahan('KAPUK')" title="Click to locate Kapuk on map">
          <div class="ex-label">
            <span style="display:inline-flex; align-items:center; gap:4px;">
              <svg class="dw-icon" width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/></svg>
              Strongest 02 Stronghold
            </span>
            <span class="ex-hint">Locate ↗</span>
          </div>
          <div class="ex-val">Kapuk (West Jkt)</div>
          <div class="ex-sub">Prabowo: 56.5% &middot; Margin +31.5%</div>
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
            <span id="opacityValBadge" style="font-size: 0.70rem; color: #555; font-weight: 700; min-width: 26px;">60%</span>
          </div>

          <div class="labels-toggle-wrap" title="Toggle village names on hex cells (Auto-appears when zooming in)">
            <label style="display: flex; align-items: center; gap: 5px; cursor: pointer; user-select: none;">
              <input type="checkbox" id="chkHexLabels" onchange="toggleHexLabels(this.checked)" style="cursor: pointer;">
              <span style="display:inline-flex; align-items:center; gap:4px;">
                <svg class="dw-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><circle cx="7" cy="7" r="1" fill="currentColor"/></svg>
                Labels
              </span>
            </label>
          </div>

          <div class="search-box-wrap">
            <span class="search-icon">
              <svg class="dw-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16" y2="16"/></svg>
            </span>
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
            <span><b>Close contest</b> (Difference &lt;2.0% victory margin between top two candidates)</span>
          </li>
          <li class="legend-row" onmouseenter="highlightLegendCategory('ganjar')" onmouseleave="resetLegendHighlight()">
            <span class="legend-chip" style="background: var(--c-ganjar);"></span>
            <span><b>Ganjar - Mahfud</b></span>
          </li>
        </ul>

        <!-- SEAT / KELURAHAN DISTRIBUTION SPECTRUM -->
        <div class="spectrum-title" id="spectrumTitle">Urban Village Distribution Breakdown (261 total):</div>
        <div class="spectrum-bar" id="spectrumBar">
          <div class="spec-segment" id="specAnies" style="width: 45.6%; background: var(--c-anies);" title="Anies: 119 Villages"></div>
          <div class="spec-segment" id="specClose" style="width: 13.4%; background: var(--c-close);" title="Close: 35 Villages"></div>
          <div class="spec-segment" id="specPrabowo" style="width: 40.2%; background: var(--c-prabowo);" title="Prabowo: 105 Villages"></div>
          <div class="spec-segment" id="specGanjar" style="width: 0.8%; background: var(--c-ganjar);" title="Ganjar: 2 Villages"></div>
        </div>
        <div class="spectrum-labels" id="spectrumLabels">
          <span><b>01 Anies:</b> <span id="lblAnies">119 Villages (45.6%)</span></span>
          <span><b>Close &lt;2%:</b> <span id="lblClose">35 Villages (13.4%)</span></span>
          <span><b>02 Prabowo:</b> <span id="lblPrabowo">105 Villages (40.2%)</span></span>
          <span><b>03 Ganjar:</b> <span id="lblGanjar">2 Villages (0.8%)</span></span>
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
        *Includes all 261 urban villages across the 5 mainland administrative cities of DKI Jakarta (Excl. Thousand Islands)<br>
        <strong>Design:</strong> Tedy Iskandar &middot; <strong>Data Source:</strong> KawalPemilu.org / KPU RI (2024 Presidential Election Certified Results)<br>
        <strong>Format:</strong> Tessellated Hexagonal Tile Cartogram
      </div>
      
      <div class="brand-mark">
        <img src="data:image/png;base64,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" alt="DataLabs Logo" class="brand-logo-datalabs">
      </div>
    </div>

  </div>

  <!-- MOBILE BOTTOM SHEET DETAIL DRAWER (P2) -->
  <div id="mobileDrawerBackdrop" class="drawer-backdrop" onclick="closeMobileDrawer()"></div>
  <div id="mobileDetailDrawer" class="mobile-drawer" role="dialog" aria-modal="true" aria-label="Urban Village Details">
    <div class="drawer-drag-pill" onclick="closeMobileDrawer()"></div>
    <div class="drawer-header">
      <div class="drawer-title-box">
        <h3 id="drawerTitle" class="drawer-title">Urban Village</h3>
        <div id="drawerSub" class="drawer-sub"><span class="tt-geo">Kecamatan, Kota</span><span class="tt-margin">Margin</span></div>
      </div>
      <button class="drawer-close-btn" onclick="closeMobileDrawer()" aria-label="Close drawer">✕</button>
    </div>
    <div id="drawerBody" class="drawer-body"></div>
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
    const svgRenderer = L.svg({{ padding: 0 }});

    const map = L.map('mapViewport', {{
      attributionControl: false,
      zoomControl: true,
      scrollWheelZoom: false,
      doubleClickZoom: false,
      dragging: true,
      zoomSnap: 0.05,
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
      crossOrigin: 'anonymous'
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
        crossOrigin: 'anonymous'
      }});
      
      if (isChecked) {{
        mapboxLayer.addTo(map);
        mapboxLayer.bringToBack();
      }}
    }}

    function setBasemapOpacity(val) {{
      const opacity = parseFloat(val);
      if (mapboxLayer) mapboxLayer.setOpacity(opacity);
      const badge = document.getElementById('opacityValBadge');
      if (badge) badge.innerText = Math.round(opacity * 100) + '%';
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
        
        let p1Bold = (p.pct_anies >= p.pct_prabowo && p.pct_anies >= p.pct_ganjar) ? "lead" : "";
        let p2Bold = (p.pct_prabowo >= p.pct_anies && p.pct_prabowo >= p.pct_ganjar) ? "lead" : "";
        let p3Bold = (p.pct_ganjar >= p.pct_anies && p.pct_ganjar >= p.pct_prabowo) ? "lead" : "";
        
        const tooltipContent = `
          <div class="dw-tt-title">${{p.kelurahan}}</div>
          <div class="dw-tt-sub"><span class="tt-geo">${{p.kecamatan}}, ${{p.kota}}</span><span class="tt-margin">${{p.margin_str}}</span></div>
          
          <div class="dw-tt-row ${{p1Bold}}">
            <span class="c-cand-name">01 Anies - Muhaimin</span>
            <span class="c-cand-val"><b>${{p.pct_anies}}%</b> <span class="c-cand-votes">(${{p.votes_anies.toLocaleString()}})</span></span>
          </div>
          <div class="dw-tt-bar-wrap">
            <div class="dw-tt-bar-fill" style="width: ${{p.pct_anies}}%; background: var(--c-anies);"></div>
          </div>

          <div class="dw-tt-row ${{p2Bold}}">
            <span class="c-cand-name">02 Prabowo - Gibran</span>
            <span class="c-cand-val"><b>${{p.pct_prabowo}}%</b> <span class="c-cand-votes">(${{p.votes_prabowo.toLocaleString()}})</span></span>
          </div>
          <div class="dw-tt-bar-wrap">
            <div class="dw-tt-bar-fill" style="width: ${{p.pct_prabowo}}%; background: var(--c-prabowo);"></div>
          </div>

          <div class="dw-tt-row ${{p3Bold}}">
            <span class="c-cand-name">03 Ganjar - Mahfud</span>
            <span class="c-cand-val"><b>${{p.pct_ganjar}}%</b> <span class="c-cand-votes">(${{p.votes_ganjar.toLocaleString()}})</span></span>
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
          className: 'dw-custom-tooltip',
          pane: 'tooltipPane'
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
          if (layer !== currentFocusedLayer) {{
            geojsonLayer.resetStyle(layer);
          }}
        }});

        layer.on('click', function(e) {{
          L.DomEvent.stopPropagation(e);
          focusKelurahan(p.kelurahan);
          if (window.innerWidth <= 768) {{
            layer.closeTooltip();
            showMobileDrawer(p);
          }}
        }});
      }}
    }}).addTo(map);

    // Dedicated Panes for Map Layers:
    // cityBordersPane: z-index 500 (Borders above hexagons)
    // hexLabelsPane: z-index 550 (Hex labels above borders, underneath perimeter badges at 700)
    map.createPane('cityBordersPane');
    map.getPane('cityBordersPane').style.zIndex = 500;
    map.getPane('cityBordersPane').style.pointerEvents = 'none';

    map.createPane('hexLabelsPane');
    map.getPane('hexLabelsPane').style.zIndex = 550;
    map.getPane('hexLabelsPane').style.pointerEvents = 'none';

    if (map.getPane('markerPane')) {{
      map.getPane('markerPane').style.zIndex = 700;
    }}
    // Tooltip Pane must ALWAYS be layered above city labels (z-index 1000)
    if (map.getPane('tooltipPane')) {{
      map.getPane('tooltipPane').style.zIndex = 1000;
    }}

    const borderSvgRenderer = L.svg({{ pane: 'cityBordersPane', padding: 0 }});

    // Solid Bold Pure White City Boundaries Layer (Always prominently above hex cells)
    const borderLayer = L.geoJSON(bordersData, {{
      pane: 'cityBordersPane',
      renderer: borderSvgRenderer,
      style: {{
        color: '#FFFFFF',
        weight: 5.5,
        opacity: 1.0,
        lineCap: 'round',
        lineJoin: 'round'
      }}
    }}).addTo(map);

    // =========================================================================
    // DYNAMIC HEXAGON KELURAHAN TEXT LABELS (P2)
    // =========================================================================
    function formatHexLabel(rawName) {{
      if (!rawName) return '';
      const words = rawName.trim().split(/\\s+/).map(w => {{
        let low = w.toLowerCase();
        if (low === 'dki' || low === 'ii' || low === 'iii' || low === 'iv' || low === 'v' || low === 'vi' || low === 'vii') return w.toUpperCase();
        if (low === 'tg.' || low === 'tanjung') return 'Tg.';
        if (low === 'kp.' || low === 'kampung') return 'Kp.';
        if (low === 'klp.' || low === 'kelapa') return 'Klp.';
        if (low === 'cip.' || low === 'cipinang') return 'Cip.';
        if (low === 'pdk.' || low === 'pondok') return 'Pdk.';
        if (low === 'gn.' || low === 'gunung') return 'Gn.';
        return low.charAt(0).toUpperCase() + low.slice(1);
      }});

      if (words.length === 1) {{
        return words[0];
      }} else if (words.length === 2) {{
        return words[0] + '<br>' + words[1];
      }} else {{
        return words[0] + ' ' + words[1] + '<br>' + words[2];
      }}
    }}

    const hexLabelsGroup = L.layerGroup([], {{ pane: 'hexLabelsPane' }}).addTo(map);
    const hexLabelMarkers = [];
    let userExplicitLabelToggle = null;

    geojsonLayer.eachLayer(layer => {{
      const p = layer.feature.properties;
      const center = layer.getBounds().getCenter();
      const normName = p.kelurahan.toUpperCase().replace(/[^A-Z0-9]/g, '');
      const formatted = formatHexLabel(p.kelurahan);

      const labelIcon = L.divIcon({{
        className: 'hex-label-item',
        html: `<div class="hex-label-text" id="hexlbl-${{normName}}">${{formatted}}</div>`,
        iconSize: [64, 26],
        iconAnchor: [32, 13]
      }});

      const m = L.marker(center, {{
        icon: labelIcon,
        pane: 'hexLabelsPane',
        interactive: false
      }});

      hexLabelsGroup.addLayer(m);
      hexLabelMarkers.push({{
        marker: m,
        kota: p.kota,
        kel: p.kelurahan,
        norm: normName,
        id: `hexlbl-${{normName}}`
      }});
    }});

    function toggleHexLabels(enabled) {{
      userExplicitLabelToggle = enabled;
      updateHexLabelsVisibility();
    }}

    function updateHexLabelsVisibility() {{
      const zoom = map.getZoom();
      const chk = document.getElementById('chkHexLabels');
      let shouldShow = false;

      if (userExplicitLabelToggle !== null) {{
        shouldShow = userExplicitLabelToggle;
      }} else {{
        shouldShow = zoom >= 11.60;
        if (chk) chk.checked = shouldShow;
      }}

      const labelPane = map.getPane('hexLabelsPane');
      if (labelPane) {{
        labelPane.style.display = shouldShow ? 'block' : 'none';
      }}

      let fontSize = '8px';
      if (zoom >= 13.0) fontSize = '11px';
      else if (zoom >= 12.2) fontSize = '9.5px';
      else if (zoom >= 11.6) fontSize = '8.5px';
      else fontSize = '7.5px';

      document.querySelectorAll('.hex-label-text').forEach(t => {{
        t.style.fontSize = fontSize;
      }});
    }}

    map.on('zoomend', updateHexLabelsVisibility);
    updateHexLabelsVisibility();

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

    const perimeterMarkers = [];
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

      const m = L.marker([c.lat, c.lng], {{ icon: customIcon, interactive: true }}).addTo(map);
      perimeterMarkers.push(m);
    }});

    // Combined Feature Group of all map elements (Hexagons + Perimeter badges)
    const allMapElementsGroup = L.featureGroup([geojsonLayer, ...perimeterMarkers]);

    // Symmetrical Absolute Mathematical Center of 261 Mainland Kelurahan & City Badges
    const JAKARTA_CENTER_LAT = -6.1756;
    const JAKARTA_CENTER_LON = 106.8400;

    function getResponsiveZoom() {{
      const w = window.innerWidth;
      if (w >= 1200) return 11.20;
      if (w >= 992) return 11.00;
      if (w >= 768) return 10.70;
      if (w >= 480) return 10.35;
      return 9.95;
    }}

    function centerMapBounds() {{
      const zoom = getResponsiveZoom();
      map.setView([JAKARTA_CENTER_LAT, JAKARTA_CENTER_LON], zoom, {{
        animate: false
      }});
    }}

    centerMapBounds();

    // Dynamic Viewport Resize & Orientation Change Auto-Calibrator
    let resizeDebounce;
    window.addEventListener('resize', () => {{
      clearTimeout(resizeDebounce);
      resizeDebounce = setTimeout(() => {{
        map.invalidateSize();
        centerMapBounds();
      }}, 120);
    }});

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
          <li class="legend-row" onmouseenter="highlightLegendCategory('close')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: var(--c-close);"></span><span><b>Close contest</b> (&lt;2.0% victory margin between top two)</span></li>
          <li class="legend-row" onmouseenter="highlightLegendCategory('ganjar')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: var(--c-ganjar);"></span><span><b>Ganjar - Mahfud</b></span></li>
        `;
      }} else if (mode === 'margin') {{
        document.getElementById('btnMargin').classList.add('active');
        title.innerHTML = 'Victory margin strength across urban villages:';
        items.innerHTML = `
          <li class="legend-row" onmouseenter="highlightLegendMargin('anies-high')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: #782438;"></span><span><b>Anies &gt;15% Lead</b> (Decisive landslide)</span></li>
          <li class="legend-row" onmouseenter="highlightLegendMargin('anies-mod')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: #CD7286;"></span><span><b>Anies 2-15% Lead</b> (Moderate lead)</span></li>
          <li class="legend-row" onmouseenter="highlightLegendCategory('close')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: #EAA86D;"></span><span><b>Close Margin (&lt;2%)</b> (Swing battleground)</span></li>
          <li class="legend-row" onmouseenter="highlightLegendMargin('prabowo-mod')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: #A2C0D9;"></span><span><b>Prabowo 2-15% Lead</b> (Moderate lead)</span></li>
          <li class="legend-row" onmouseenter="highlightLegendMargin('prabowo-high')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: #486E8D;"></span><span><b>Prabowo &gt;15% Lead</b> (Decisive stronghold)</span></li>
          <li class="legend-row" onmouseenter="highlightLegendMargin('ganjar-lead')" onmouseleave="resetLegendHighlight()"><span class="legend-chip" style="background: #75556B;"></span><span><b>Ganjar &gt;2% Lead</b> (Glodok &amp; Roa Malaka)</span></li>
        `;
      }} else if (mode === 'close') {{
        document.getElementById('btnClose').classList.add('active');
        title.innerHTML = 'Close battleground contests (Victory margin &lt; 2.0%):';
        items.innerHTML = `
          <li class="legend-row"><span class="legend-chip" style="background: #EAA86D;"></span><span><b>Battleground Urban Villages (35 Villages, 13.4%)</b></span></li>
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
      updateSpectrumBar(selectedCity, mode);
    }}

    // Dynamic Multi-View Distribution Spectrum Slider Update
    function updateSpectrumBar(cityName, mode) {{
      mode = mode || currentMode;
      const barContainer = document.getElementById('spectrumBar');
      const labelsContainer = document.getElementById('spectrumLabels');
      const titleElem = document.getElementById('spectrumTitle');
      
      const filtered = geojsonData.features.filter(f => !cityName || f.properties.kota === cityName);
      const total = filtered.length;
      const titlePrefix = cityName ? cityName : "Urban Village";

      if (mode === 'plurality') {{
        titleElem.innerText = `${{titlePrefix}} Plurality Distribution (${{total}} total):`;
        let anies = 0, prabowo = 0, close = 0, ganjar = 0;
        filtered.forEach(f => {{
          const w = f.properties.winner;
          if (w.includes("Close")) close++;
          else if (w.includes("Anies")) anies++;
          else if (w.includes("Prabowo")) prabowo++;
          else if (w.includes("Ganjar")) ganjar++;
        }});

        const pA = ((anies / total) * 100).toFixed(1);
        const pC = ((close / total) * 100).toFixed(1);
        const pP = ((prabowo / total) * 100).toFixed(1);
        const pG = ((ganjar / total) * 100).toFixed(1);

        barContainer.innerHTML = `
          <div class="spec-segment" style="width: ${{pA}}%; background: var(--c-anies);" title="Anies: ${{anies}} Vil"></div>
          <div class="spec-segment" style="width: ${{pC}}%; background: var(--c-close);" title="Close: ${{close}} Vil"></div>
          <div class="spec-segment" style="width: ${{pP}}%; background: var(--c-prabowo);" title="Prabowo: ${{prabowo}} Vil"></div>
          <div class="spec-segment" style="width: ${{pG}}%; background: var(--c-ganjar);" title="Ganjar: ${{ganjar}} Vil"></div>
        `;

        labelsContainer.innerHTML = `
          <span><b>01 Anies:</b> ${{anies}} Vil (${{pA}}%)</span>
          <span><b>Close &lt;2%:</b> ${{close}} Vil (${{pC}}%)</span>
          <span><b>02 Prabowo:</b> ${{prabowo}} Vil (${{pP}}%)</span>
          ${{ganjar > 0 ? `<span><b>03 Ganjar:</b> ${{ganjar}} Vil (${{pG}}%)</span>` : ''}}
        `;
      }} else if (mode === 'margin') {{
        titleElem.innerText = `${{titlePrefix}} Victory Margin Strength (${{total}} total):`;
        let aHigh = 0, aMod = 0, close = 0, pMod = 0, pHigh = 0, gLead = 0;
        filtered.forEach(f => {{
          const p = f.properties;
          if (p.diff <= 2.0) {{
            close++;
          }} else if (p.leader_code === '01') {{
            if (p.diff > 15.0) aHigh++;
            else aMod++;
          }} else if (p.leader_code === '02') {{
            if (p.diff > 15.0) pHigh++;
            else pMod++;
          }} else if (p.leader_code === '03') {{
            gLead++;
          }}
        }});

        const paH = ((aHigh / total) * 100).toFixed(1);
        const paM = ((aMod / total) * 100).toFixed(1);
        const pC = ((close / total) * 100).toFixed(1);
        const ppM = ((pMod / total) * 100).toFixed(1);
        const ppH = ((pHigh / total) * 100).toFixed(1);
        const pgL = ((gLead / total) * 100).toFixed(1);

        barContainer.innerHTML = `
          <div class="spec-segment" style="width: ${{paH}}%; background: #782438;" title="Anies >15%: ${{aHigh}} Vil"></div>
          <div class="spec-segment" style="width: ${{paM}}%; background: #CD7286;" title="Anies 2-15%: ${{aMod}} Vil"></div>
          <div class="spec-segment" style="width: ${{pC}}%; background: #EAA86D;" title="Close <2%: ${{close}} Vil"></div>
          <div class="spec-segment" style="width: ${{ppM}}%; background: #A2C0D9;" title="Prabowo 2-15%: ${{pMod}} Vil"></div>
          <div class="spec-segment" style="width: ${{ppH}}%; background: #486E8D;" title="Prabowo >15%: ${{pHigh}} Vil"></div>
          ${{gLead > 0 ? `<div class="spec-segment" style="width: ${{pgL}}%; background: #75556B;" title="Ganjar >2%: ${{gLead}} Vil"></div>` : ''}}
        `;

        labelsContainer.innerHTML = `
          <span><b>01 &gt;15%:</b> ${{aHigh}} (${{paH}}%)</span>
          <span><b>01 2-15%:</b> ${{aMod}} (${{paM}}%)</span>
          <span><b>Close &lt;2%:</b> ${{close}} (${{pC}}%)</span>
          <span><b>02 2-15%:</b> ${{pMod}} (${{ppM}}%)</span>
          <span><b>02 &gt;15%:</b> ${{pHigh}} (${{ppH}}%)</span>
          ${{gLead > 0 ? `<span><b>03 &gt;2%:</b> ${{gLead}} (${{pgL}}%)</span>` : ''}}
        `;
      }} else if (mode === 'close') {{
        titleElem.innerText = `${{titlePrefix}} Battleground vs Decisive Margins (${{total}} total):`;
        let battleground = 0, decisive = 0;
        filtered.forEach(f => {{
          if (f.properties.diff <= 2.0) battleground++;
          else decisive++;
        }});

        const pB = ((battleground / total) * 100).toFixed(1);
        const pD = ((decisive / total) * 100).toFixed(1);

        barContainer.innerHTML = `
          <div class="spec-segment" style="width: ${{pB}}%; background: #EAA86D;" title="Battleground: ${{battleground}} Vil"></div>
          <div class="spec-segment" style="width: ${{pD}}%; background: #DED9CE;" title="Decisive: ${{decisive}} Vil"></div>
        `;

        labelsContainer.innerHTML = `
          <span><b>Battleground (&lt;2% diff):</b> ${{battleground}} Vil (${{pB}}%)</span>
          <span><b>Decisive Margin (&gt;2% diff):</b> ${{decisive}} Vil (${{pD}}%)</span>
        `;
      }} else if (mode === 'density') {{
        titleElem.innerText = `${{titlePrefix}} Voter Turnout Volume Density (${{total}} total):`;
        let vHigh = 0, high = 0, mod = 0, low = 0;
        filtered.forEach(f => {{
          const tot = f.properties.total_votes;
          if (tot > 40000) vHigh++;
          else if (tot > 25000) high++;
          else if (tot > 15000) mod++;
          else low++;
        }});

        const pvH = ((vHigh / total) * 100).toFixed(1);
        const pH = ((high / total) * 100).toFixed(1);
        const pM = ((mod / total) * 100).toFixed(1);
        const pL = ((low / total) * 100).toFixed(1);

        barContainer.innerHTML = `
          <div class="spec-segment" style="width: ${{pvH}}%; background: #2D4B66;" title=">40k: ${{vHigh}} Vil"></div>
          <div class="spec-segment" style="width: ${{pH}}%; background: #537D9F;" title="25-40k: ${{high}} Vil"></div>
          <div class="spec-segment" style="width: ${{pM}}%; background: #8CAFC8;" title="15-25k: ${{mod}} Vil"></div>
          <div class="spec-segment" style="width: ${{pL}}%; background: #C5D8E6;" title="<15k: ${{low}} Vil"></div>
        `;

        labelsContainer.innerHTML = `
          <span><b>&gt;40k Ballots:</b> ${{vHigh}} (${{pvH}}%)</span>
          <span><b>25k-40k:</b> ${{high}} (${{pH}}%)</span>
          <span><b>15k-25k:</b> ${{mod}} (${{pM}}%)</span>
          <span><b>&lt;15k:</b> ${{low}} (${{pL}}%)</span>
        `;
      }}
    }}

    let currentFocusedLayer = null;

    // Filter City (with All Jakarta reset support & dynamic spectrum)
    function filterCity(cityName) {{
      selectedCity = cityName;
      closeMobileDrawer();
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

      // Dim non-selected hex labels
      if (typeof hexLabelMarkers !== 'undefined') {{
        hexLabelMarkers.forEach(item => {{
          const el = document.getElementById(item.id);
          if (!el) return;
          if (!cityName || item.kota === cityName) {{
            el.style.opacity = '1';
          }} else {{
            el.style.opacity = '0.20';
          }}
        }});
      }}

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
        if (typeof hexLabelMarkers !== 'undefined') {{
          hexLabelMarkers.forEach(item => {{
            const el = document.getElementById(item.id);
            if (el) {{
              el.style.opacity = '1';
              el.style.fontWeight = '700';
            }}
          }});
        }}
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
        const norm = layer.feature.properties.kelurahan.toUpperCase().replace(/[^A-Z0-9]/g, '');
        const lbl = document.getElementById(`hexlbl-${{norm}}`);

        if (name.includes(q) || kec.includes(q)) {{
          layer.setStyle({{
            weight: 3.5,
            color: '#000000',
            fillOpacity: 1
          }});
          layer.bringToFront();
          if (lbl) {{
            lbl.style.opacity = '1';
            lbl.style.fontWeight = '800';
          }}
        }} else {{
          layer.setStyle({{
            fillOpacity: 0.15,
            weight: 0.5,
            color: '#EEE'
          }});
          layer.closeTooltip();
          if (lbl) {{
            lbl.style.opacity = '0.20';
          }}
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

      closeMobileDrawer();

      if (currentFocusedLayer) {{
        currentFocusedLayer.closeTooltip();
        currentFocusedLayer = null;
      }}
      geojsonLayer.eachLayer(l => {{
        geojsonLayer.resetStyle(l);
        l.closeTooltip();
      }});
      if (typeof hexLabelMarkers !== 'undefined') {{
        hexLabelMarkers.forEach(item => {{
          const el = document.getElementById(item.id);
          if (el) {{
            el.style.opacity = '1';
            el.style.fontWeight = '700';
          }}
        }});
      }}
    }}

    // Hide dropdown on document click
    document.addEventListener('click', function(e) {{
      const searchBox = document.querySelector('.search-box-wrap');
      const dropdown = document.getElementById('searchDropdown');
      if (dropdown && searchBox && !searchBox.contains(e.target)) {{
        dropdown.style.display = 'none';
      }}
    }});

    // Click-to-Focus on Extremes cards (Strict Single Tooltip Focus & Mobile Drawer)
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

        if (window.innerWidth <= 768) {{
          showMobileDrawer(layer.feature.properties);
        }} else {{
          layer.openTooltip();
        }}
        
        // Scroll map smoothly into view if needed
        const mapElem = document.getElementById('mapViewport');
        if (mapElem) {{
          mapElem.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
      }}
    }}

    // Mobile Bottom Sheet Detail Drawer Controls (P2)
    function showMobileDrawer(p) {{
      const drawer = document.getElementById('mobileDetailDrawer');
      const backdrop = document.getElementById('mobileDrawerBackdrop');
      if (!drawer || !backdrop) return;

      let p1Bold = (p.pct_anies >= p.pct_prabowo && p.pct_anies >= p.pct_ganjar) ? "lead" : "";
      let p2Bold = (p.pct_prabowo >= p.pct_anies && p.pct_prabowo >= p.pct_ganjar) ? "lead" : "";
      let p3Bold = (p.pct_ganjar >= p.pct_anies && p.pct_ganjar >= p.pct_prabowo) ? "lead" : "";

      document.getElementById('drawerTitle').innerText = p.kelurahan;
      document.getElementById('drawerSub').innerHTML = `<span class="tt-geo">${{p.kecamatan}}, ${{p.kota}}</span><span class="tt-margin">${{p.margin_str}}</span>`;

      document.getElementById('drawerBody').innerHTML = `
        <div class="dw-tt-row ${{p1Bold}}">
          <span class="c-cand-name">01 Anies - Muhaimin</span>
          <span class="c-cand-val"><b>${{p.pct_anies}}%</b> <span class="c-cand-votes">(${{p.votes_anies.toLocaleString()}})</span></span>
        </div>
        <div class="dw-tt-bar-wrap">
          <div class="dw-tt-bar-fill" style="width: ${{p.pct_anies}}%; background: var(--c-anies);"></div>
        </div>

        <div class="dw-tt-row ${{p2Bold}}">
          <span class="c-cand-name">02 Prabowo - Gibran</span>
          <span class="c-cand-val"><b>${{p.pct_prabowo}}%</b> <span class="c-cand-votes">(${{p.votes_prabowo.toLocaleString()}})</span></span>
        </div>
        <div class="dw-tt-bar-wrap">
          <div class="dw-tt-bar-fill" style="width: ${{p.pct_prabowo}}%; background: var(--c-prabowo);"></div>
        </div>

        <div class="dw-tt-row ${{p3Bold}}">
          <span class="c-cand-name">03 Ganjar - Mahfud</span>
          <span class="c-cand-val"><b>${{p.pct_ganjar}}%</b> <span class="c-cand-votes">(${{p.votes_ganjar.toLocaleString()}})</span></span>
        </div>
        <div class="dw-tt-bar-wrap">
          <div class="dw-tt-bar-fill" style="width: ${{p.pct_ganjar}}%; background: var(--c-ganjar);"></div>
        </div>

        <div class="dw-tt-total" style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #ECE7DE;">
          <span>Total Valid Ballots</span>
          <span>${{p.total_votes.toLocaleString()}}</span>
        </div>
      `;

      backdrop.classList.add('active');
      drawer.classList.add('active');
    }}

    function closeMobileDrawer() {{
      const drawer = document.getElementById('mobileDetailDrawer');
      const backdrop = document.getElementById('mobileDrawerBackdrop');
      if (drawer) drawer.classList.remove('active');
      if (backdrop) backdrop.classList.remove('active');
    }}

    // Touch swipe down to dismiss mobile drawer
    (function() {{
      const drawer = document.getElementById('mobileDetailDrawer');
      if (!drawer) return;
      let startY = 0;
      let currentY = 0;
      drawer.addEventListener('touchstart', function(e) {{
        startY = e.touches[0].clientY;
      }}, {{ passive: true }});
      drawer.addEventListener('touchmove', function(e) {{
        currentY = e.touches[0].clientY;
      }}, {{ passive: true }});
      drawer.addEventListener('touchend', function() {{
        if (currentY - startY > 60) {{
          closeMobileDrawer();
        }}
        startY = 0;
        currentY = 0;
      }});
    }})();

    // Close open focused tooltip or mobile drawer when clicking map background
    map.on('click', function() {{
      closeMobileDrawer();
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
        if (marginCat === 'anies-high' && p.leader_code === '01' && p.diff > 15) match = true;
        if (marginCat === 'anies-mod' && p.leader_code === '01' && p.diff >= 2 && p.diff <= 15) match = true;
        if (marginCat === 'prabowo-mod' && p.leader_code === '02' && p.diff >= 2 && p.diff <= 15) match = true;
        if (marginCat === 'prabowo-high' && p.leader_code === '02' && p.diff > 15) match = true;
        if (marginCat === 'ganjar-lead' && p.leader_code === '03' && p.diff > 2) match = true;

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

                    // Helper: Convert all active streetmap tile images to true pixel grayscale
    function convertTilesToGrayscale(doc) {{
      const tileImgs = (doc || document).querySelectorAll('.leaflet-tile-pane img');
      tileImgs.forEach(img => {{
        try {{
          if (img.complete && (img.naturalWidth > 0 || img.width > 0)) {{
            const w = img.naturalWidth || img.width || 512;
            const h = img.naturalHeight || img.height || 512;
            const c = document.createElement('canvas');
            c.width = w;
            c.height = h;
            const ctx = c.getContext('2d');
            ctx.filter = 'grayscale(100%) contrast(90%) brightness(102%)';
            ctx.drawImage(img, 0, 0, w, h);
            try {{
              const dataUrl = c.toDataURL('image/png');
              if (dataUrl && dataUrl.length > 50) {{
                img.src = dataUrl;
              }}
            }} catch (e) {{
              // In case canvas is tainted, apply pixel iteration fallback
              try {{
                const imgData = ctx.getImageData(0, 0, w, h);
                const d = imgData.data;
                for (let i = 0; i < d.length; i += 4) {{
                  const gray = Math.round(0.299 * d[i] + 0.587 * d[i+1] + 0.114 * d[i+2]);
                  d[i] = gray; d[i+1] = gray; d[i+2] = gray;
                }}
                ctx.putImageData(imgData, 0, 0);
                img.src = c.toDataURL('image/png');
              }} catch (err2) {{
                // fallback ignored
              }}
            }}
          }}
        }} catch (err) {{
          console.warn('Tile grayscale conversion note:', err);
        }}
      }});
    }}

    // Bulletproof High-Res Poster Export with Pure Vector Rasterization & Exact Centering
    async function exportPoster() {{
      const btn = document.getElementById('btnExport');
      const btnText = document.getElementById('btnExportText');
      const isMobile = window.innerWidth <= 768;
      if (btnText) {{
        btnText.innerText = isMobile ? 'Exporting...' : 'Rendering 4K...';
      }} else {{
        btn.innerText = isMobile ? '⏳ Exporting...' : '⏳ Rendering 4K...';
      }}
      btn.style.opacity = '0.7';

      const originalScrollY = window.scrollY;
      window.scrollTo(0, 0);

      map.invalidateSize();
      centerMapBounds();

      // 1. Convert all tiles on screen to true grayscale before html2canvas starts
      convertTilesToGrayscale(document);

      // Wait 350ms for tiles and map center to settle
      await new Promise(r => setTimeout(r, 350));

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
          // Hide export button and search dropdown
          const clonedBtn = clonedDoc.getElementById('btnExport');
          if (clonedBtn) clonedBtn.style.display = 'none';
          const dropdown = clonedDoc.getElementById('searchDropdown');
          if (dropdown) dropdown.style.display = 'none';

          // Hide mobile drawer and backdrop in publication export
          const clonedDrawer = clonedDoc.getElementById('mobileDetailDrawer');
          if (clonedDrawer) clonedDrawer.style.display = 'none';
          const clonedBackdrop = clonedDoc.getElementById('mobileDrawerBackdrop');
          if (clonedBackdrop) clonedBackdrop.style.display = 'none';

          // Clean up basemap controls for publication export
          const basemapWrap = clonedDoc.querySelector('.basemap-toggle-wrap');
          if (basemapWrap) {{
            const opacity = document.getElementById('basemapOpacity').value || '0.60';
            const styleSelect = document.getElementById('basemapStyleSelect');
            const styleName = styleSelect ? styleSelect.options[styleSelect.selectedIndex].text : 'City Streets';
            const isChecked = document.getElementById('chkBasemap').checked;
            if (isChecked) {{
              basemapWrap.innerHTML = `<span style="font-size:0.75rem; font-weight:700; color:#333;">Basemap: ${{styleName}} (${{Math.round(parseFloat(opacity)*100)}}% Opacity)</span>`;
            }} else {{
              basemapWrap.innerHTML = `<span style="font-size:0.75rem; font-weight:700; color:#666;">Basemap: Off</span>`;
            }}
          }}

          // Clean up labels toggle for publication export
          const labelsWrap = clonedDoc.querySelector('.labels-toggle-wrap');
          if (labelsWrap) {{
            const chkLbl = document.getElementById('chkHexLabels');
            const isLblChecked = chkLbl && chkLbl.checked;
            labelsWrap.innerHTML = `<span style="font-size:0.75rem; font-weight:700; color:#333;">Labels: ${{isLblChecked ? 'On' : 'Off'}}</span>`;
          }}

          // 2. Ensure all cloned tiles are also pure grayscale
          convertTilesToGrayscale(clonedDoc);
        }}
      }}).then(canvas => {{
        const link = document.createElement('a');
        link.download = 'The_Voice_of_Jakarta_Election_Map_4K.png';
        link.href = canvas.toDataURL('image/png', 1.0);
        link.click();
        if (btnText) {{
          btnText.innerText = 'Download';
        }} else {{
          btn.innerText = 'Download';
        }}
        btn.style.opacity = '1';
        window.scrollTo(0, originalScrollY);
      }}).catch(err => {{
        console.error('Export error:', err);
        if (btnText) {{
          btnText.innerText = 'Download';
        }} else {{
          btn.innerText = 'Download';
        }}
        btn.style.opacity = '1';
        window.scrollTo(0, originalScrollY);
        alert('Export error, please try again.');
      }});
    }}
  </script>
</body>
</html>
'''

output_path = os.path.join(BASE_DIR, "index.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Masterpiece with all interactive polish features compiled successfully: {output_path}")
