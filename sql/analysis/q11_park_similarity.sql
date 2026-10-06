-- Q11 · Which parks are ecological "twins"?
-- Technique: self-join on a bridge table, Jaccard similarity
--   J(A,B) = |A ∩ B| / |A ∪ B| = shared / (|A| + |B| - shared)
-- Why it matters: shows which parks share ecosystems, which is useful for
-- coordinated management and a nice demonstration of set logic in SQL.

WITH sizes AS (
    SELECT park_code, count(*) AS n FROM v_present_species GROUP BY park_code
),
shared AS (
    SELECT a.park_code AS park_a,
           b.park_code AS park_b,
           count(*)    AS shared_species
    FROM v_present_species a
    JOIN v_present_species b
      ON a.taxon_id = b.taxon_id
     AND a.park_code < b.park_code          -- each unordered pair once
    GROUP BY a.park_code, b.park_code
)
SELECT pa.park_name                                       AS park_a,
       pb.park_name                                       AS park_b,
       s.shared_species,
       round(1.0 * s.shared_species / (sa.n + sb.n - s.shared_species), 3) AS jaccard
FROM shared s
JOIN sizes sa ON sa.park_code = s.park_a
JOIN sizes sb ON sb.park_code = s.park_b
JOIN parks pa ON pa.park_code = s.park_a
JOIN parks pb ON pb.park_code = s.park_b
ORDER BY jaccard DESC
LIMIT 15;
