-- Q03 · Across the whole system, which kinds of life are most invaded?
-- Technique: GROUP BY with filtered aggregates, share-of-total window
-- Why it matters: tells managers where invasive-species effort is best spent.

SELECT category,
       count(DISTINCT taxon_id)                                    AS distinct_species,
       count(*)                                                    AS park_records,
       round(100.0 * count(*) / sum(count(*)) OVER (), 2)          AS pct_of_all_records,
       sum(nativeness = 'Not Native')                              AS non_native_records,
       round(100.0 * sum(nativeness = 'Not Native')
             / nullif(sum(nativeness IN ('Native','Not Native')), 0), 1)
                                                                   AS pct_non_native,
       sum(is_esa_listed)                                          AS esa_listed_records
FROM v_present_species
GROUP BY category
ORDER BY park_records DESC;
