-- Q12 · Which parks protect species found in no other national park?
-- Technique: HAVING count(*) = 1 to find singletons, then roll up by park
-- Why it matters: a park that is the *only* refuge for many species is
-- irreplaceable, regardless of how famous it is.

WITH singletons AS (
    SELECT taxon_id
    FROM v_present_species
    GROUP BY taxon_id
    HAVING count(DISTINCT park_code) = 1
)
SELECT rank() OVER (ORDER BY count(*) DESC)               AS uniqueness_rank,
       p.park_name,
       p.state,
       count(*)                                           AS species_found_only_here,
       round(100.0 * count(*) / b.species_richness, 1)    AS pct_of_park_species,
       sum(v.severity BETWEEN 2 AND 5)                    AS of_which_at_risk
FROM v_present_species v
JOIN singletons s       ON s.taxon_id = v.taxon_id
JOIN parks p            ON p.park_code = v.park_code
JOIN v_park_biodiversity b ON b.park_code = v.park_code
GROUP BY p.park_code, p.park_name, p.state, b.species_richness
ORDER BY uniqueness_rank, p.park_name;
