-- Q01 · What does the dataset cover?
-- Technique: scalar subqueries, single-row KPI summary
-- Why it matters: every analysis starts by stating its scope.

SELECT
    (SELECT count(*)                  FROM parks)              AS parks,
    (SELECT count(DISTINCT state)     FROM parks)              AS states,
    (SELECT sum(acres)                FROM parks)              AS total_acres,
    (SELECT count(*)                  FROM taxa)               AS distinct_species,
    (SELECT count(*)                  FROM v_present_species)  AS park_species_records,
    (SELECT min(year)                 FROM annual_visits)      AS first_visit_year,
    (SELECT max(year)                 FROM annual_visits)      AS last_visit_year,
    (SELECT sum(visitors) FROM annual_visits
      WHERE year = (SELECT max(year) FROM annual_visits))      AS visitors_last_year,
    (SELECT sum(is_esa_listed)        FROM v_present_species)  AS esa_listed_records;
