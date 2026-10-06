-- Q02 · Which parks hold the most biodiversity, and how does it break down?
-- Technique: conditional aggregation (pivot), RANK() window, ratio metrics
-- Why it matters: raw species counts favour huge parks, so we also rank by
-- density (species per 1,000 acres) to surface small-but-rich parks.

WITH by_park AS (
    SELECT ps.park_code,
           count(*)                                    AS species_richness,
           sum(category = 'Vascular Plant')            AS plants,
           sum(category = 'Bird')                      AS birds,
           sum(category = 'Mammal')                    AS mammals,
           sum(category IN ('Reptile','Amphibian'))    AS herps,
           sum(category = 'Fish')                      AS fish,
           sum(category IN ('Insect','Invertebrate','Spider/Scorpion',
                            'Slug/Snail','Crab/Lobster/Shrimp'))  AS invertebrates,
           sum(category IN ('Fungi','Nonvascular Plant','Algae')) AS fungi_mosses_algae
    FROM v_present_species ps
    GROUP BY ps.park_code
)
SELECT rank() OVER (ORDER BY b.species_richness DESC)                    AS richness_rank,
       p.park_name,
       p.state,
       b.species_richness,
       b.plants, b.birds, b.mammals, b.herps, b.fish,
       b.invertebrates, b.fungi_mosses_algae,
       round(1000.0 * b.species_richness / p.acres, 2)                   AS species_per_1k_acres,
       rank() OVER (ORDER BY 1.0 * b.species_richness / p.acres DESC)    AS density_rank
FROM by_park b
JOIN parks p USING (park_code)
ORDER BY richness_rank;
