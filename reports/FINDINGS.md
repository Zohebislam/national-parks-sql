# Findings: Visitor Pressure and Biodiversity in U.S. National Parks

*Auto-generated from `sql/analysis/` on October 06, 2026. Every number below
comes from a query result in `results/`; re-run `python run.py all` to refresh.*

## Scope
56 national parks across 27 states covering
51,964,032 acres, 46,022 distinct species
(103,321 park-level records), and visitation from
1904 to 2016
(82,455,174 visits in 2016).

## Key findings

1. **Visitation is at a record high.** Total visits peaked in 2016 at
   82,455,174, up 37.8% over the final decade of data.
2. **Crowding varies by orders of magnitude.** Hot Springs National Park sees
   278.25 visitors per acre, versus
   0.0010 at Gates Of The Arctic National Park and Preserve.
3. **Most crowded vs. least crowded parks.** The top crowding quartile averages
   13.8% non-native species and 41.6
   at-risk species per 1,000, compared with 5.8% and
   35.8 in the least crowded quartile.
4. **Correlation check.** Across parks, crowding has a moderate positive relationship
   with non-native share (r = 0.401) and a weak positive relationship with
   at-risk species density (r = 0.254). Park size has a moderate negative
   relationship with non-native share (r = -0.352), so size is a confounder to keep in mind.
5. **Robustness (Q15).** The crowding–invasion link holds when Hawaii's island parks are
   removed (r = 0.421) but weakens to r = 0.215 after controlling for park size:
   part of the pattern is simply that small parks are both more crowded and easier to invade.
6. **Spider/Scorpion** is the most invaded category
   (24.2% of records non-native).
7. **Bryce Canyon National Park** tops the composite Pressure Index
   (1.1), driven mainly by visitor growth.
8. **Irreplaceable parks.** Redwood National Park holds the most
   species found in no other national park (2,937).

## Supporting tables

**Most biodiverse parks (Q02)**
| # | Park | Species | Per 1k acres |
|---|---|---|---|
| 1 | Great Smoky Mountains | 6,070 | 11.64 |
| 2 | Redwood | 5,828 | 51.80 |
| 3 | Shenandoah | 4,215 | 21.18 |
| 4 | Death Valley | 3,974 | 0.84 |
| 5 | Yellowstone | 3,789 | 1.71 |

**Most at-risk species (Q04)**
| # | Park | ESA-listed | At-risk | Top category |
|---|---|---|---|---|
| 1 | Death Valley | 37 | 222 | Bird |
| 2 | Redwood | 22 | 137 | Bird |
| 3 | Channel Islands | 30 | 135 | Bird |
| 4 | Big Bend | 11 | 130 | Bird |
| 5 | Grand Canyon | 10 | 118 | Bird |

**Most invaded parks (Q05)**
| Park | % non-native | pts vs avg |
|---|---|---|
| Haleakala | 41.00 | 30.40 |
| Hawaii Volcanoes | 40.50 | 29.80 |
| Dry Tortugas | 29.30 | 18.70 |
| Acadia | 23.70 | 13.00 |
| Everglades | 22.50 | 11.80 |

**Fastest-growing parks, 10-yr CAGR (Q07)**
| # | Park | Latest visitors | CAGR % |
|---|---|---|---|
| 1 | Kobuk Valley | 15,500 | 17.83 |
| 2 | Lake Clark and Preserve | 21,102 | 14.77 |
| 3 | Bryce Canyon | 2,365,110 | 10.26 |
| 4 | Capitol Reef | 1,064,904 | 7.61 |
| 5 | Joshua Tree | 2,505,286 | 7.15 |

**Crowding quartiles (Q09)**
| Quartile | Visitors/acre | % non-native | At-risk/1k | Richness |
|---|---|---|---|---|
| Most crowded | 48.93 | 13.80 | 41.60 | 1,788 |
| Middle | 6.84 | 12.40 | 44.40 | 2,113 |
| Middle | 2.74 | 10.70 | 47.70 | 1,860 |
| Least crowded | 0.25 | 5.80 | 35.80 | 1,619 |

**Pressure Index (Q13)**
| # | Park | Index | Main driver |
|---|---|---|---|
| 1 | Bryce Canyon | 1.10 | visitor growth |
| 2 | Dry Tortugas | 0.82 | invasive species |
| 3 | Arches | 0.81 | at-risk species |
| 4 | Acadia | 0.81 | invasive species |
| 5 | Hawaii Volcanoes | 0.78 | invasive species |

**Ecological twins (Q11)**
| Park A | Park B | Jaccard |
|---|---|---|
| Arches | Canyonlands | 0.58 |
| Sequoia and Kings Canyon | Yosemite | 0.55 |
| Gates Of The Arctic and Preserve | Kobuk Valley | 0.52 |
| Canyonlands | Capitol Reef | 0.50 |
| Isle Royale | Voyageurs | 0.48 |

**Hidden gems: above-median biodiversity, below-median crowds (Q14)**
| # | Park | Species | Visitors |
|---|---|---|---|
| 1 | North Cascades | 3,064 | 28,646 |
| 2 | Wrangell - St Elias and Preserve | 1,511 | 79,047 |
| 3 | Great Basin | 2,389 | 144,846 |
| 4 | Congaree | 2,271 | 143,843 |
| 5 | Redwood | 5,828 | 536,297 |

## Caveats
Correlation is not causation. Species lists reflect survey effort as well as true
diversity, and the species snapshot and visitation series do not line up perfectly in
time. See the README's *Limitations* section.
