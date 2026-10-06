-- Q07 · Which parks are growing fastest, and which had the biggest single-year surge?
-- Technique: CAGR via power(), LAG() inside a partition, ROW_NUMBER to pick max
-- Why it matters: rapid growth is a leading indicator of crowding pressure.

WITH yoy AS (
    SELECT park_code, year, visitors,
           visitors - lag(visitors) OVER (PARTITION BY park_code ORDER BY year) AS abs_change,
           1.0 * visitors / nullif(lag(visitors) OVER (PARTITION BY park_code ORDER BY year), 0) - 1
                                                                                 AS pct_change
    FROM annual_visits
),
biggest_jump AS (
    SELECT park_code, year AS surge_year, pct_change,
           row_number() OVER (PARTITION BY park_code ORDER BY pct_change DESC) AS rn
    FROM yoy
    WHERE year > (SELECT max(year) - 10 FROM annual_visits)   -- recent decade only
      AND pct_change IS NOT NULL
)
SELECT rank() OVER (ORDER BY v.cagr_10y DESC)   AS growth_rank,
       p.park_name,
       p.state,
       v.visitors_10y_ago,
       v.visitors_latest,
       round(100 * v.cagr_10y, 2)              AS cagr_10y_pct,
       b.surge_year,
       round(100 * b.pct_change, 1)            AS surge_pct
FROM v_park_visits_latest v
JOIN parks p USING (park_code)
LEFT JOIN biggest_jump b ON b.park_code = v.park_code AND b.rn = 1
WHERE v.cagr_10y IS NOT NULL
ORDER BY growth_rank;
