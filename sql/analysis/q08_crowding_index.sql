-- Q08 · Which parks are the most crowded relative to their size?
-- Technique: derived density metric, NTILE(4) bucketing, PERCENT_RANK
-- Why it matters: total visitors hides that a small park with 3M visitors is
-- under far more pressure per acre than a huge one with the same count.

SELECT p.park_name,
       p.state,
       p.acres,
       v.visitors_latest,
       round(1.0 * v.visitors_latest / p.acres, 3)                         AS visitors_per_acre,
       ntile(4) OVER (ORDER BY 1.0 * v.visitors_latest / p.acres DESC)     AS crowding_quartile,
       round(100 * percent_rank() OVER (ORDER BY 1.0 * v.visitors_latest / p.acres), 1)
                                                                           AS crowding_percentile
FROM v_park_visits_latest v
JOIN parks p USING (park_code)
ORDER BY visitors_per_acre DESC;
