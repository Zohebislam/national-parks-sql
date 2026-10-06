-- =============================================================================
-- 02_transform.sql
-- Clean staging data and load the model. Every cleaning decision is explicit
-- here so it can be reviewed (and defended in an interview).
-- =============================================================================

-- ------------------------------------------------- conservation lookup ------
-- Severity is an ordinal scale used for weighting; is_esa_listed flags species
-- with legal protection under the U.S. Endangered Species Act.
INSERT INTO conservation_statuses (status, severity, is_esa_listed) VALUES
    ('Extinct',              6, 0),
    ('Endangered',           5, 1),
    ('Threatened',           4, 1),
    ('Proposed Endangered',  4, 0),
    ('Proposed Threatened',  3, 0),
    ('Species of Concern',   2, 0),
    ('Under Review',         2, 0),
    ('In Recovery',          1, 0);

-- ---------------------------------------------------- unit-code aliases ----
-- Sequoia & Kings Canyon is managed (and surveyed) as one park, SEKI, but the
-- visitation file reports it as two units. Map both onto SEKI.
CREATE TEMP TABLE unit_aliases (source_code TEXT PRIMARY KEY, park_code TEXT NOT NULL);
INSERT INTO unit_aliases VALUES ('SEQU', 'SEKI'), ('KICA', 'SEKI');

CREATE TEMP VIEW stg_visits_mapped AS
SELECT v.*,
       coalesce(a.park_code, upper(trim(v.unit_code))) AS park_code
FROM stg_visits v
LEFT JOIN unit_aliases a ON a.source_code = upper(trim(v.unit_code));

-- ------------------------------------------------------------- parks -------
-- Visitation source carries the NPS region; attach it while loading parks.
INSERT INTO parks (park_code, park_name, state, region, acres, latitude, longitude)
SELECT
    upper(trim(p.park_code)),
    trim(p.park_name),
    trim(p.state),
    (SELECT trim(v.region)
       FROM stg_visits_mapped v
      WHERE v.park_code = upper(trim(p.park_code))
        AND trim(v.region) <> ''
      LIMIT 1),
    CAST(replace(p.acres, ',', '') AS INTEGER),
    CAST(p.latitude  AS REAL),
    CAST(p.longitude AS REAL)
FROM stg_parks p
WHERE trim(coalesce(p.park_code, '')) <> '';

-- -------------------------------------------------------------- taxa -------
-- The same scientific name appears once per park. A handful of names are
-- categorised inconsistently across parks, so keep the most common label
-- (ties broken alphabetically) to guarantee one row per species.
INSERT INTO taxa (scientific_name, category, taxon_order, family, common_names)
WITH cleaned AS (
    SELECT trim(scientific_name)                AS scientific_name,
           trim(category)                       AS category,
           nullif(trim(taxon_order), '')        AS taxon_order,
           nullif(trim(family), '')             AS family,
           nullif(trim(common_names), '')       AS common_names
    FROM stg_species
    WHERE trim(coalesce(scientific_name, '')) <> ''
      AND trim(coalesce(category, '')) <> ''
),
votes AS (
    SELECT scientific_name, category, taxon_order, family,
           max(common_names) AS common_names,
           count(*)          AS n
    FROM cleaned
    GROUP BY scientific_name, category, taxon_order, family
),
ranked AS (
    SELECT *,
           row_number() OVER (PARTITION BY scientific_name
                              ORDER BY n DESC, category, taxon_order, family) AS rn
    FROM votes
)
SELECT scientific_name, category, taxon_order, family, common_names
FROM ranked
WHERE rn = 1;

-- ------------------------------------------------------ park_species -------
-- Source has occasional duplicate (park, species) rows. Prefer the Approved
-- record, then the most severe conservation status, so we never under-count
-- at-risk species. Blank strings become NULL; unknown statuses (e.g. raw
-- seasonal labels that leaked into the status column) become NULL too and are
-- reported by 04_data_quality.sql.
INSERT INTO park_species (park_code, taxon_id, record_status, occurrence,
                          nativeness, abundance, seasonality, conservation_status)
WITH joined AS (
    SELECT p.park_code,
           t.taxon_id,
           nullif(trim(s.record_status), '')       AS record_status,
           nullif(trim(s.occurrence), '')          AS occurrence,
           nullif(trim(s.nativeness), '')          AS nativeness,
           nullif(trim(s.abundance), '')           AS abundance,
           nullif(trim(s.seasonality), '')         AS seasonality,
           cs.status                               AS conservation_status,
           coalesce(cs.severity, -1)               AS severity
    FROM stg_species s
    JOIN parks p  ON p.park_name = trim(s.park_name)
    JOIN taxa  t  ON t.scientific_name = trim(s.scientific_name)
    LEFT JOIN conservation_statuses cs ON cs.status = trim(s.conservation_status)
),
deduped AS (
    SELECT *,
           row_number() OVER (
               PARTITION BY park_code, taxon_id
               ORDER BY (record_status = 'Approved') DESC, severity DESC
           ) AS rn
    FROM joined
)
SELECT park_code, taxon_id, record_status, occurrence, nativeness,
       abundance, seasonality, conservation_status
FROM deduped
WHERE rn = 1;

-- ----------------------------------------------------- annual_visits -------
-- The visitation file contains every NPS unit type plus a per-unit 'Total'
-- row. Keep yearly rows for units in our parks dimension. Aliased units are
-- summed (SEQU + KICA -> SEKI); exact duplicate source rows are collapsed first.
INSERT INTO annual_visits (park_code, year, visitors)
WITH per_unit AS (
    SELECT v.park_code,
           upper(trim(v.unit_code))                         AS unit_code,
           CAST(v.year_raw AS INTEGER)                      AS year,
           max(CAST(round(CAST(v.visitors AS REAL)) AS INTEGER)) AS visitors
    FROM stg_visits_mapped v
    JOIN parks p ON p.park_code = v.park_code
    WHERE trim(v.year_raw) GLOB '[12][0-9][0-9][0-9]'
      AND trim(coalesce(v.visitors, '')) <> ''
    GROUP BY v.park_code, upper(trim(v.unit_code)), CAST(v.year_raw AS INTEGER)
)
SELECT park_code, year, sum(visitors)
FROM per_unit
GROUP BY park_code, year;
