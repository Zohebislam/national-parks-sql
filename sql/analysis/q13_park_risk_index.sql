-- Q13 · Which parks are most at risk overall? (composite Pressure Index)
-- Technique: z-score standardisation with window aggregates, weighted sum,
-- RANK — the same pattern used for credit scores or churn-risk scores.
--   z = (x - mean) / population std dev, computed via AVG() OVER ()
-- Components (equal weight): crowding (log), 10-yr growth, non-native share,
-- at-risk species per 1k. Higher index = more pressure.

WITH base AS (
    SELECT park_code, park_name, state,
           log10(visitors_per_acre) AS crowding,
           cagr_10y                 AS growth,
           non_native_share         AS invasion,
           at_risk_per_1k_species   AS fragility
    FROM v_park_scorecard
    WHERE visitors_per_acre > 0 AND cagr_10y IS NOT NULL
      AND non_native_share IS NOT NULL AND at_risk_per_1k_species IS NOT NULL
),
stats AS (
    SELECT *,
           avg(crowding)  OVER () AS m1, sqrt(avg(crowding*crowding)   OVER () - avg(crowding)  OVER () * avg(crowding)  OVER ()) AS s1,
           avg(growth)    OVER () AS m2, sqrt(avg(growth*growth)       OVER () - avg(growth)    OVER () * avg(growth)    OVER ()) AS s2,
           avg(invasion)  OVER () AS m3, sqrt(avg(invasion*invasion)   OVER () - avg(invasion)  OVER () * avg(invasion)  OVER ()) AS s3,
           avg(fragility) OVER () AS m4, sqrt(avg(fragility*fragility) OVER () - avg(fragility) OVER () * avg(fragility) OVER ()) AS s4
    FROM base
),
z AS (
    SELECT park_name, state,
           coalesce((crowding  - m1) / nullif(s1, 0), 0) AS z_crowding,
           coalesce((growth    - m2) / nullif(s2, 0), 0) AS z_growth,
           coalesce((invasion  - m3) / nullif(s3, 0), 0) AS z_invasion,
           coalesce((fragility - m4) / nullif(s4, 0), 0) AS z_fragility
    FROM stats
)
SELECT rank() OVER (ORDER BY (z_crowding + z_growth + z_invasion + z_fragility) DESC) AS risk_rank,
       park_name,
       state,
       round((z_crowding + z_growth + z_invasion + z_fragility) / 4, 2) AS pressure_index,
       round(z_crowding, 2)  AS z_crowding,
       round(z_growth, 2)    AS z_growth,
       round(z_invasion, 2)  AS z_invasion,
       round(z_fragility, 2) AS z_fragility,
       CASE  -- name the single biggest driver for each park
         WHEN max(z_crowding, z_growth, z_invasion, z_fragility) = z_crowding  THEN 'crowding'
         WHEN max(z_crowding, z_growth, z_invasion, z_fragility) = z_growth    THEN 'visitor growth'
         WHEN max(z_crowding, z_growth, z_invasion, z_fragility) = z_invasion  THEN 'invasive species'
         ELSE 'at-risk species'
       END AS main_driver
FROM z
ORDER BY risk_rank;
