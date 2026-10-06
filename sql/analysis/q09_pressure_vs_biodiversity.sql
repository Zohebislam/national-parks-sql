-- Q09 · CORE QUESTION: Do more crowded parks show signs of ecological stress?
-- Technique: NTILE grouping, then aggregate comparison across quartiles
-- Why it matters: tests the hypothesis that visitor pressure goes hand in hand
-- with more non-native species and a higher share of at-risk species.
-- NOTE: association, not causation (see README › Limitations).

WITH q AS (
    SELECT *,
           ntile(4) OVER (ORDER BY visitors_per_acre DESC) AS crowding_quartile
    FROM v_park_scorecard
    WHERE visitors_per_acre IS NOT NULL
      AND species_richness IS NOT NULL
)
SELECT crowding_quartile,
       CASE crowding_quartile WHEN 1 THEN 'Most crowded'
                              WHEN 4 THEN 'Least crowded' ELSE 'Middle' END AS label,
       count(*)                                    AS parks,
       round(avg(visitors_per_acre), 2)            AS avg_visitors_per_acre,
       CAST(round(avg(species_richness)) AS INTEGER) AS avg_species_richness,
       round(100 * avg(non_native_share), 1)       AS avg_pct_non_native,
       round(avg(at_risk_per_1k_species), 1)       AS avg_at_risk_per_1k_species,
       round(100 * avg(cagr_10y), 2)               AS avg_cagr_10y_pct
FROM q
GROUP BY crowding_quartile
ORDER BY crowding_quartile;
