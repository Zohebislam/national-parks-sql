-- Q10 · How strongly are pressure and biodiversity metrics related?
-- Technique: Pearson correlation computed by hand in SQL from aggregates,
-- UNPIVOT-style UNION ALL to test several metric pairs in one query.
--   r = (E[xy] - E[x]E[y]) / (sd(x) * sd(y))
-- log10(visitors_per_acre) is used because crowding is heavily right-skewed.

WITH base AS (
    SELECT log10(visitors_per_acre)   AS log_crowding,
           cagr_10y,
           non_native_share,
           at_risk_per_1k_species,
           log10(species_richness)    AS log_richness,
           log10(acres)               AS log_acres
    FROM v_park_scorecard
    WHERE visitors_per_acre > 0 AND species_richness > 0 AND cagr_10y IS NOT NULL
),
pairs AS (
    SELECT 'log crowding'    AS x_metric, 'non-native share'   AS y_metric, log_crowding AS x, non_native_share       AS y FROM base
    UNION ALL SELECT 'log crowding',    'at-risk per 1k',     log_crowding, at_risk_per_1k_species FROM base
    UNION ALL SELECT 'log crowding',    'log richness',       log_crowding, log_richness           FROM base
    UNION ALL SELECT '10y growth',      'non-native share',   cagr_10y,     non_native_share       FROM base
    UNION ALL SELECT 'log park size',   'log richness',       log_acres,    log_richness           FROM base
    UNION ALL SELECT 'log park size',   'non-native share',   log_acres,    non_native_share       FROM base
)
SELECT x_metric,
       y_metric,
       count(*) AS n_parks,
       round((avg(x*y) - avg(x)*avg(y))
             / nullif(sqrt(avg(x*x) - avg(x)*avg(x)) * sqrt(avg(y*y) - avg(y)*avg(y)), 0), 3)
             AS pearson_r,
       CASE
         WHEN abs((avg(x*y) - avg(x)*avg(y))
             / nullif(sqrt(avg(x*x) - avg(x)*avg(x)) * sqrt(avg(y*y) - avg(y)*avg(y)), 0)) >= 0.5 THEN 'strong'
         WHEN abs((avg(x*y) - avg(x)*avg(y))
             / nullif(sqrt(avg(x*x) - avg(x)*avg(x)) * sqrt(avg(y*y) - avg(y)*avg(y)), 0)) >= 0.3 THEN 'moderate'
         ELSE 'weak'
       END AS strength
FROM pairs
GROUP BY x_metric, y_metric
ORDER BY abs(pearson_r) DESC;
