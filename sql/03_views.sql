-- =============================================================================
-- 03_views.sql
-- Reusable semantic layer. Analysis queries build on these instead of
-- re-deriving the same business rules in every file.
-- =============================================================================

-- A species "counts" for a park if it is (probably) present today. Historical,
-- unconfirmed and false reports are excluded; a blank occurrence is kept.
-- NOTE: record_status is deliberately NOT filtered. 'In Review' is an NPS
-- administrative status, and it is wildly uneven across parks (75% of
-- Redwood's records vs 0% of many others), so requiring 'Approved' would bias
-- every park comparison.
CREATE VIEW v_present_species AS
SELECT ps.park_code,
       t.taxon_id,
       t.scientific_name,
       t.category,
       t.family,
       t.common_names,
       ps.nativeness,
       ps.abundance,
       ps.conservation_status,
       coalesce(cs.severity, 0)      AS severity,
       coalesce(cs.is_esa_listed, 0) AS is_esa_listed
FROM park_species ps
JOIN taxa t                        ON t.taxon_id = ps.taxon_id
LEFT JOIN conservation_statuses cs ON cs.status  = ps.conservation_status
WHERE coalesce(ps.occurrence, 'Present') IN ('Present', 'Probably Present');


-- One row per park: biodiversity metrics.
CREATE VIEW v_park_biodiversity AS
SELECT park_code,
       count(*)                                                    AS species_richness,
       sum(category IN ('Mammal','Bird','Reptile','Amphibian','Fish'))
                                                                   AS vertebrate_richness,
       sum(nativeness = 'Native')                                  AS native_species,
       sum(nativeness = 'Not Native')                              AS non_native_species,
       round(1.0 * sum(nativeness = 'Not Native')
             / nullif(sum(nativeness IN ('Native','Not Native')), 0), 4)
                                                                   AS non_native_share,
       sum(is_esa_listed)                                          AS esa_listed_species,
       sum(severity BETWEEN 2 AND 5)                               AS at_risk_species,
       round(1000.0 * sum(severity BETWEEN 2 AND 5) / count(*), 2) AS at_risk_per_1k_species
FROM v_present_species
GROUP BY park_code;


-- One row per park: most recent visitation year and the value 10 years before.
CREATE VIEW v_park_visits_latest AS
WITH latest AS (
    SELECT park_code, max(year) AS latest_year
    FROM annual_visits
    GROUP BY park_code
)
SELECT l.park_code,
       l.latest_year,
       cur.visitors                   AS visitors_latest,
       prev.visitors                  AS visitors_10y_ago,
       -- Compound annual growth rate over the decade
       CASE WHEN prev.visitors > 0
            THEN round(power(1.0 * cur.visitors / prev.visitors, 0.1) - 1, 4)
       END                            AS cagr_10y
FROM latest l
JOIN annual_visits cur       ON cur.park_code  = l.park_code AND cur.year  = l.latest_year
LEFT JOIN annual_visits prev ON prev.park_code = l.park_code AND prev.year = l.latest_year - 10;


-- The analytical "wide table": everything known about a park in one row.
CREATE VIEW v_park_scorecard AS
SELECT p.park_code,
       p.park_name,
       p.state,
       p.region,
       p.acres,
       b.species_richness,
       b.vertebrate_richness,
       b.native_species,
       b.non_native_species,
       b.non_native_share,
       b.esa_listed_species,
       b.at_risk_species,
       b.at_risk_per_1k_species,
       v.latest_year,
       v.visitors_latest,
       v.visitors_10y_ago,
       v.cagr_10y,
       round(1.0 * v.visitors_latest / p.acres, 3) AS visitors_per_acre
FROM parks p
LEFT JOIN v_park_biodiversity  b ON b.park_code = p.park_code
LEFT JOIN v_park_visits_latest v ON v.park_code = p.park_code;
