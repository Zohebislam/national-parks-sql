-- Q14 · Where should a nature lover go to see the most life with the fewest crowds?
-- Technique: PERCENT_RANK to split at the median, multi-condition filter,
-- a "value" ratio — framed as a recommendation, the way a product team would.

WITH ranked AS (
    SELECT *,
           percent_rank() OVER (ORDER BY species_richness)  AS richness_pctl,
           percent_rank() OVER (ORDER BY visitors_latest)   AS visitors_pctl
    FROM v_park_scorecard
    WHERE species_richness IS NOT NULL AND visitors_latest > 0
)
SELECT row_number() OVER (ORDER BY 1.0 * species_richness * 1000000 / visitors_latest DESC) AS gem_rank,
       park_name,
       state,
       species_richness,
       visitors_latest,
       round(1.0 * species_richness * 1000000 / visitors_latest, 1) AS species_per_million_visitors,
       round(100 * richness_pctl, 0) AS richness_percentile,
       round(100 * visitors_pctl, 0) AS visitors_percentile
FROM ranked
WHERE richness_pctl >= 0.5        -- above-median biodiversity
  AND visitors_pctl  < 0.5        -- below-median crowds
ORDER BY gem_rank;
