-- =============================================================================
-- 04_data_quality.sql
-- Automated data-quality report. Each row is one check with a PASS / WARN /
-- FAIL verdict. FAIL stops the pipeline; WARN is logged and documented.
-- =============================================================================

WITH checks AS (

    -- Row-count sanity -------------------------------------------------------
    SELECT 'parks loaded' AS check_name,
           (SELECT count(*) FROM parks) AS observed,
           '> 0' AS expectation,
           CASE WHEN (SELECT count(*) FROM parks) > 0 THEN 'PASS' ELSE 'FAIL' END AS status

    UNION ALL
    SELECT 'species records loaded',
           (SELECT count(*) FROM park_species), '> 0',
           CASE WHEN (SELECT count(*) FROM park_species) > 0 THEN 'PASS' ELSE 'FAIL' END

    UNION ALL
    SELECT 'visitation rows loaded',
           (SELECT count(*) FROM annual_visits), '> 0',
           CASE WHEN (SELECT count(*) FROM annual_visits) > 0 THEN 'PASS' ELSE 'FAIL' END

    -- Join coverage ----------------------------------------------------------
    UNION ALL
    SELECT 'species rows whose park name did not match parks',
           (SELECT count(*) FROM stg_species s
             WHERE NOT EXISTS (SELECT 1 FROM parks p WHERE p.park_name = trim(s.park_name))),
           '= 0', NULL

    UNION ALL
    SELECT 'parks with no visitation data',
           (SELECT count(*) FROM parks p
             WHERE NOT EXISTS (SELECT 1 FROM annual_visits v WHERE v.park_code = p.park_code)),
           '= 0', NULL

    UNION ALL
    SELECT 'parks with no species data',
           (SELECT count(*) FROM parks p
             WHERE NOT EXISTS (SELECT 1 FROM park_species s WHERE s.park_code = p.park_code)),
           '= 0', NULL

    -- Deduplication / unmapped values ---------------------------------------
    UNION ALL
    SELECT 'duplicate (park, species) source rows removed',
           (SELECT count(*) FROM stg_species) - (SELECT count(*) FROM park_species)
             - (SELECT count(*) FROM stg_species s
                 WHERE NOT EXISTS (SELECT 1 FROM parks p WHERE p.park_name = trim(s.park_name))
                    OR trim(coalesce(s.scientific_name, '')) = ''
                    OR trim(coalesce(s.category, '')) = ''),
           'informational', 'INFO'

    UNION ALL
    SELECT 'non-blank conservation statuses not in lookup (set to NULL)',
           (SELECT count(*) FROM stg_species s
             WHERE trim(coalesce(s.conservation_status, '')) <> ''
               AND NOT EXISTS (SELECT 1 FROM conservation_statuses c
                                WHERE c.status = trim(s.conservation_status))),
           '= 0', NULL

    -- Value plausibility -----------------------------------------------------
    UNION ALL
    SELECT 'visitation years outside 1904-2100',
           (SELECT count(*) FROM annual_visits WHERE year < 1904 OR year > 2100),
           '= 0', NULL

    UNION ALL
    SELECT 'non-native share outside [0,1]',
           (SELECT count(*) FROM v_park_biodiversity
             WHERE non_native_share < 0 OR non_native_share > 1),
           '= 0', NULL
)
SELECT check_name,
       observed,
       expectation,
       coalesce(status,
                CASE WHEN observed = 0 THEN 'PASS' ELSE 'WARN' END) AS status
FROM checks;
