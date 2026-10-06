-- Q06 · How has total National Park visitation changed over time?
-- Technique: LAG() for year-over-year change, 5-year moving average frame
-- Why it matters: the macro trend that every park-level story sits inside.

WITH yearly AS (
    SELECT year,
           sum(visitors)     AS total_visitors,
           count(*)          AS parks_reporting
    FROM annual_visits
    GROUP BY year
)
SELECT year,
       total_visitors,
       parks_reporting,
       round(100.0 * (total_visitors - lag(total_visitors) OVER w)
             / nullif(lag(total_visitors) OVER w, 0), 2)        AS yoy_pct,
       CAST(round(avg(total_visitors) OVER (
                ORDER BY year ROWS BETWEEN 4 PRECEDING AND CURRENT ROW)) AS INTEGER)
                                                                AS moving_avg_5y
FROM yearly
WINDOW w AS (ORDER BY year)
ORDER BY year;
