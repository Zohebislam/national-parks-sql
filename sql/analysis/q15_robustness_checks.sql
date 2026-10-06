-- Q15 · Does the crowding → invasive-species link survive robustness checks?
-- Technique: correlation under different samples, plus a PARTIAL correlation
-- (controlling for park size) done in SQL by regressing both variables on
-- log(acres) with window aggregates and correlating the residuals.
-- Why it matters: a finding that disappears under scrutiny is not a finding.
-- Hawaii's island parks are extreme invasion outliers; small parks are both
-- denser and easier to invade, so size could explain the whole relationship.

WITH base AS (
    SELECT state,
           log10(visitors_per_acre) AS x,      -- crowding
           non_native_share         AS y,      -- invasion
           log10(acres)             AS z       -- park size (control)
    FROM v_park_scorecard
    WHERE visitors_per_acre > 0 AND non_native_share IS NOT NULL
),
resid AS (   -- residuals of x and y after removing the linear effect of z
    SELECT x - (avg(x) OVER () + (avg(x*z) OVER () - avg(x) OVER () * avg(z) OVER ())
                 / (avg(z*z) OVER () - avg(z) OVER () * avg(z) OVER ()) * (z - avg(z) OVER ())) AS x,
           y - (avg(y) OVER () + (avg(y*z) OVER () - avg(y) OVER () * avg(z) OVER ())
                 / (avg(z*z) OVER () - avg(z) OVER () * avg(z) OVER ()) * (z - avg(z) OVER ())) AS y
    FROM base
),
samples AS (
    SELECT 'All parks'                          AS test, x, y FROM base
    UNION ALL
    SELECT 'Excluding Hawaii (island outliers)',     x, y FROM base WHERE state <> 'HI'
    UNION ALL
    SELECT 'Controlling for park size (partial r)', x, y FROM resid
)
SELECT test,
       count(*) AS n_parks,
       round((avg(x*y) - avg(x)*avg(y))
             / nullif(sqrt(avg(x*x) - avg(x)*avg(x)) * sqrt(avg(y*y) - avg(y)*avg(y)), 0), 3)
             AS pearson_r
FROM samples
GROUP BY test
ORDER BY CASE test WHEN 'All parks' THEN 1
                   WHEN 'Excluding Hawaii (island outliers)' THEN 2 ELSE 3 END;
