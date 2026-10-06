-- Q04 · Where are the protected (ESA-listed) and at-risk species concentrated?
-- Technique: CTEs, DENSE_RANK, correlated "top category" pick with ROW_NUMBER
-- Why it matters: identifies the parks carrying the heaviest conservation load.

WITH park_risk AS (
    SELECT park_code,
           sum(is_esa_listed)                   AS esa_listed,
           sum(conservation_status = 'Endangered') AS endangered,
           sum(conservation_status = 'Threatened') AS threatened,
           sum(severity BETWEEN 2 AND 5)        AS at_risk_total,
           count(*)                             AS species_richness
    FROM v_present_species
    GROUP BY park_code
),
top_category AS (
    SELECT park_code, category, n,
           row_number() OVER (PARTITION BY park_code ORDER BY n DESC, category) AS rn
    FROM (SELECT park_code, category, count(*) AS n
            FROM v_present_species
           WHERE severity BETWEEN 2 AND 5
           GROUP BY park_code, category)
)
SELECT dense_rank() OVER (ORDER BY r.at_risk_total DESC)   AS risk_rank,
       p.park_name,
       p.state,
       r.esa_listed,
       r.endangered,
       r.threatened,
       r.at_risk_total,
       round(1000.0 * r.at_risk_total / r.species_richness, 1) AS at_risk_per_1k_species,
       tc.category                                         AS most_at_risk_category
FROM park_risk r
JOIN parks p USING (park_code)
LEFT JOIN top_category tc ON tc.park_code = r.park_code AND tc.rn = 1
WHERE r.at_risk_total > 0
ORDER BY risk_rank, p.park_name;
