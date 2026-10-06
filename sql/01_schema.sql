-- =============================================================================
-- 01_schema.sql
-- Star-style relational model for U.S. National Park visitation + biodiversity.
--
--   staging (raw, untyped)          model (clean, typed, constrained)
--   ----------------------          ---------------------------------
--   stg_parks          ───────────► parks                 (dimension)
--   stg_species        ──┬────────► taxa                  (dimension)
--                        └────────► park_species          (fact: park × species)
--   stg_visits         ───────────► annual_visits         (fact: park × year)
--   (seeded in 02)     ───────────► conservation_statuses (lookup)
-- =============================================================================

PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS v_park_scorecard;
DROP VIEW  IF EXISTS v_park_biodiversity;
DROP VIEW  IF EXISTS v_park_visits_latest;
DROP VIEW  IF EXISTS v_present_species;

DROP TABLE IF EXISTS park_species;
DROP TABLE IF EXISTS annual_visits;
DROP TABLE IF EXISTS taxa;
DROP TABLE IF EXISTS conservation_statuses;
DROP TABLE IF EXISTS parks;

-- ---------------------------------------------------------------- staging ----
-- Staging tables mirror the source CSVs column-for-column, all TEXT, so the
-- load step never fails on dirty values. All typing/cleaning happens in SQL.

DROP TABLE IF EXISTS stg_parks;
CREATE TABLE stg_parks (
    park_code TEXT, park_name TEXT, state TEXT,
    acres TEXT, latitude TEXT, longitude TEXT
);

DROP TABLE IF EXISTS stg_species;
CREATE TABLE stg_species (
    species_id TEXT, park_name TEXT, category TEXT, taxon_order TEXT,
    family TEXT, scientific_name TEXT, common_names TEXT, record_status TEXT,
    occurrence TEXT, nativeness TEXT, abundance TEXT, seasonality TEXT,
    conservation_status TEXT
);

DROP TABLE IF EXISTS stg_visits;
CREATE TABLE stg_visits (
    year_raw TEXT, unit_code TEXT, unit_name TEXT, unit_type TEXT,
    region TEXT, state TEXT, visitors TEXT
);

-- ------------------------------------------------------------------ model ----

CREATE TABLE parks (
    park_code   TEXT    PRIMARY KEY CHECK (length(park_code) = 4),
    park_name   TEXT    NOT NULL UNIQUE,
    state       TEXT    NOT NULL,
    region      TEXT,                       -- NPS administrative region
    acres       INTEGER NOT NULL CHECK (acres > 0),
    latitude    REAL    CHECK (latitude  BETWEEN -90  AND 90),
    longitude   REAL    CHECK (longitude BETWEEN -180 AND 180)
);

CREATE TABLE conservation_statuses (
    status        TEXT    PRIMARY KEY,
    severity      INTEGER NOT NULL CHECK (severity BETWEEN 0 AND 6),
    is_esa_listed INTEGER NOT NULL CHECK (is_esa_listed IN (0, 1))  -- Endangered Species Act
);

CREATE TABLE taxa (
    taxon_id        INTEGER PRIMARY KEY,
    scientific_name TEXT    NOT NULL UNIQUE,
    category        TEXT    NOT NULL,       -- Mammal, Bird, Vascular Plant, ...
    taxon_order     TEXT,
    family          TEXT,
    common_names    TEXT
);

CREATE TABLE park_species (
    park_code           TEXT    NOT NULL REFERENCES parks(park_code),
    taxon_id            INTEGER NOT NULL REFERENCES taxa(taxon_id),
    record_status       TEXT,
    occurrence          TEXT,
    nativeness          TEXT,
    abundance           TEXT,
    seasonality         TEXT,
    conservation_status TEXT    REFERENCES conservation_statuses(status),
    PRIMARY KEY (park_code, taxon_id)
);

CREATE TABLE annual_visits (
    park_code TEXT    NOT NULL REFERENCES parks(park_code),
    year      INTEGER NOT NULL CHECK (year BETWEEN 1900 AND 2100),
    visitors  INTEGER NOT NULL CHECK (visitors >= 0),
    PRIMARY KEY (park_code, year)
);

-- Indexes chosen for the access paths the analysis actually uses.
CREATE INDEX ix_park_species_taxon  ON park_species (taxon_id);
CREATE INDEX ix_park_species_status ON park_species (conservation_status);
CREATE INDEX ix_annual_visits_year  ON annual_visits (year);
CREATE INDEX ix_taxa_category       ON taxa (category);
