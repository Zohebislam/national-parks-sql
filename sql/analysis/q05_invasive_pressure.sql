-- Q05 · Which parks are most invaded by non-native species?
-- Technique: ratio metric, NTILE quartiles, deviation from system average
-- Why it matters: non-native share is a standard indicator of ecosystem
-- disturbance; comparing to the system mean makes outliers obvious.

WITH s AS (
    SELECT p.park_name, p.state, b.non_native_species, b.native_species,
           b.non_native_share
    FROM v_park_biodiversity b
    JOIN parks p USING (park_code)
    WHERE b.non_native_share IS NOT NULL
)
SELECT park_name,
       state,
       native_species,
       non_native_species,
       round(100 * non_native_share, 1)                                  AS pct_non_native,
       round(100 * (non_native_share - avg(non_native_share) OVER ()), 1) AS pts_vs_system_avg,
       ntile(4) OVER (ORDER BY non_native_share DESC)                    AS invasion_quartile
FROM s
ORDER BY non_native_share DESC;
