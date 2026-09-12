# The Sound of Jakarta — 2024 Presidential Election Cartogram

> **An interactive, publication-grade tessellated hexagonal cartogram analyzing the 2024 Indonesian Presidential Election across 261 mainland urban villages (*Kelurahan*) of DKI Jakarta.**

[![GitHub Pages](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-success?style=for-the-badge&logo=github)](https://datalabs89.github.io/the-sound-of-jakarta/)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9.4-199900?style=for-the-badge&logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![GeoJSON](https://img.shields.io/badge/Data-GeoJSON%20261%20Villages-blue?style=for-the-badge)](https://kawalpemilu.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

---

## 🌐 Live Interactive Application
Experience the live interactive map directly in your browser:  
👉 **[https://datalabs89.github.io/the-sound-of-jakarta/](https://datalabs89.github.io/the-sound-of-jakarta/)**

---

## 📖 Executive Summary & Electoral Narrative

In the 2024 Indonesian Presidential Election, the capital territory of **DKI Jakarta** emerged as the nation's most closely contested battlefield. Across **5,524,091 certified valid ballots** cast across **261 mainland urban villages (*Kelurahan*)**, the electorate was divided between two opposing political coalitions:

* **01 Anies Baswedan – Muhaimin Iskandar**: **41.64%** *(2,338,237 votes)* — Plurality leader in **119 Villages (45.6%)**
* **02 Prabowo Subianto – Gibran Rakabuming Raka**: **41.15%** *(2,311,122 votes)* — Plurality leader in **106 Villages (40.6%)**
* **03 Ganjar Pranowo – Mahfud MD**: **17.21%** *(966,547 votes)* — Plurality leader in **3 Villages (1.1%)**
* **Battleground (<2.0% victory margin)**: **33 Villages (12.6%)** — Swing battlegrounds decided on razor-thin margins.

---

## 🗺️ Cartographic Methodology: Tessellated Hexagonal Tile Cartogram

Standard geographical choropleth maps suffer from severe **area bias**: sparse rural/industrial districts (such as Kapuk or Marunda) visually overpower high-density urban residential centers (such as Kebon Melati, Menteng, or Pal Meriam).

This project utilizes a **Tessellated Hexagonal Tile Cartogram**:
1. **Equal Visual Weight**: Every urban village is represented by an equal-area regular hexagon ( = 0.0088^\circ$).
2. **Preserved Topological Adjacency**: Relative spatial neighbors and inter-city boundaries across Jakarta's 5 mainland administrative cities (*West, South, Central, East, North Jakarta*) are strictly maintained.
3. **Surrounding Regional Anchors**: Outer perimeter labels and satellite administrative badges (*Tangerang City, South Tangerang/BSD, Depok & Bogor Regency, Bekasi City & Regency, Java Sea*) frame the territory naturally.

---

## ✨ Key Features & Interactive Architecture

### 1. 🎛️ Four Dynamic Analytical Modes
* **Plurality Winner**: Clean candidate preference map (*Prabowo Slate Blue, Anies Dusty Wine, Close Coral, Ganjar Muted Plum*).
* **Victory Margin**: Multi-tier shaded gradients showing landslide bastions ($>15\%$), moderate leads (-7\%$), and tight contests.
* **Close Contests (<2%)**: High-contrast isolation of the 33 swing battleground urban villages.
* **Voter Density**: Turnout density breakdown highlighting mega-polling villages ($>40,000$ ballots).

### 2. 🎯 Click-to-Focus Record Extremes (*Locate ↗*)
Interactive cards allow instant navigation to notable electoral extremes:
* **⚔️ Closest Margin**: **Pal Meriam (East Jakarta)** — .01\%$ difference (*decided by exactly 1 ballot*).
* **🔴 Strongest 01 Bastion**: **Sukabumi Utara (West Jakarta)** — Anies .5\%$ vs Prabowo .3\%$ ($+39.3\%$ lead).
* **🔵 Strongest 02 Stronghold**: **Kapuk Muara (North Jakarta)** — Prabowo .1\%$ vs Anies .4\%$ ($+35.7\%$ lead).

### 3. 🔍 Instant Search & Keyboard Navigation
* Search 261 kelurahans in real-time with automatic highlighting.
* Includes dedicated **✕** clear button and full keyboard **Escape** shortcut support to reset filters instantly.

### 4. 📊 6-Column City Drilldown & Dynamic Proportion Spectrum
* Filter between **All Jakarta**, **North**, **West**, **Central**, **East**, and **South Jakarta**.
* The distribution spectrum bar recalculates exact village counts and percentages dynamically upon city selection.

### 5. 📸 4K Ultra-HD Pure Vector PNG Export
* One-click poster generation exporting a **~3,920px wide (4K / 300+ DPI)** high-resolution PNG.
* Powered by mathematical **SVG Vector rendering** with Leaflet DOM matrix transform normalization for zero-drift, razor-sharp output.

---

## 🎨 Editorial Design Aesthetics

Inspired by the visual journalism of *The European Correspondent*, *The Financial Times*, and *The Economist*:
* **Typography**: Classic serif headlines in *Libre Baskerville* paired with clean, geometric data labeling in *IBM Plex Sans*.
* **Editorial Canvas**: Warm paper background (#F6F3EE) with subtle halftone dot-matrix patterns.
* **Sophisticated Swatches**:
  * Anies–Muhaimin: Crimson Wine (#AF4D64 / #782438)
  * Prabowo–Gibran: Slate Navy (#7CA1BF / #486E8D)
  * Battleground Swing: Warm Coral (#EAA86D)
  * Ganjar–Mahfud: Muted Plum (#75556B)

---

## 📂 Repository Structure

`
├── index.html                                 # Standalone interactive application (served on GitHub Pages)
├── data/
│   ├── mainland_tessellated_kelurahan.json   # 261 Tessellated grid node coordinates & mappings
│   └── real_hyper_votes.json                 # Certified KPU / KawalPemilu election data
├── scripts/
│   └── compile_map.py                        # Automated Python build engine
└── README.md                                 # Project documentation
`

---

## 💻 Local Development & Build

To run locally or rebuild the cartogram from source data:

1. **Clone the repository:**
   `ash
   git clone https://github.com/datalabs89/the-sound-of-jakarta.git
   cd the-sound-of-jakarta
   `

2. **Open directly in browser:**
   Simply double-click index.html or serve with any local HTTP server:
   `ash
   npx serve .
   # or
   python -m http.server 8000
   `

3. **Recompile HTML via Python engine:**
   `ash
   python scripts/compile_map.py
   `

---

## 📊 Data Sources & Credits

* **Election Results Data**: Certified 2024 Presidential Election results from [KawalPemilu.org](https://kawalpemilu.org/) & [KPU RI](https://kpu.go.id/).
* **Cartography & Frontend Engineering**: [Tedy Iskandar](https://github.com/datalabs89).
* **Libraries Used**: [Leaflet.js](https://leafletjs.com/), [html2canvas](https://html2canvas.hertzen.com/).

---

## 📄 License

This project is licensed under the **MIT License** — feel free to use, adapt, and build upon for journalistic, research, or educational purposes.
