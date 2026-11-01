-- Ten lowest total investment (low end), unit-franchise offers only
SELECT brand_name, total_investment_low_usd, total_investment_high_usd FROM v_brand_summary WHERE edition_note IS NULL AND total_investment_low_usd > 1000 ORDER BY total_investment_low_usd LIMIT 10;

-- Highest comparable revenue in quick-service food
SELECT b.brand_name, r.annual_revenue_usd, r.basis FROM comparable_revenue r JOIN brands b USING (brand_slug) WHERE b.industry LIKE 'food-quick-service%' ORDER BY r.annual_revenue_usd DESC LIMIT 10;

-- Brands whose franchised outlets fell in every year on file
SELECT brand_slug, COUNT(*) AS years FROM turnover_by_year GROUP BY brand_slug HAVING COUNT(*) >= 3 AND SUM(outlets_end < outlets_start) = COUNT(*);

-- Highest closure rate among brands with 100+ franchised outlets
SELECT b.brand_name, m.closure_rate_pct, m.closures, m.franchised_outlet_years, m.closure_year_from, m.closure_year_to FROM brand_metrics m JOIN brands b USING (brand_slug) WHERE m.franchised_outlets >= 100 AND m.closure_ranking_eligible = 1 ORDER BY m.closure_rate_pct DESC LIMIT 10;

-- Every Item 19 figure for one brand, with page numbers
SELECT metric_label, cohort_label, outlet_count, avg_value, median_value, period, fdd_page FROM item19_figures WHERE brand_slug = 'great-clips';

-- Brands disclosing net profit or EBITDA in Item 19
SELECT DISTINCT b.brand_name, i.metric FROM item19_figures i JOIN brands b USING (brand_slug) WHERE i.metric IN ('net_profit','ebitda') ORDER BY b.brand_name;

-- Lowest royalty + marketing % of sales among brands with 50+ outlets
SELECT f.brand_name, f.pct_of_sales_to_franchisor FROM v_fee_burden f JOIN brand_metrics m USING (brand_slug) WHERE m.total_outlets >= 50 ORDER BY f.pct_of_sales_to_franchisor LIMIT 10;

-- Brands with the most outlets in Texas (latest year)
SELECT brand_name, outlets_end FROM v_state_footprint WHERE state = 'TX' ORDER BY outlets_end DESC LIMIT 10;

-- Brands absent from California but in 10+ other states
SELECT brand_name FROM v_brand_summary WHERE states_count >= 10 AND brand_slug NOT IN (SELECT brand_slug FROM v_state_footprint WHERE state = 'CA');

-- Average initial fee by industry
SELECT b.industry_label, ROUND(AVG(f.initial_fee_low_usd)) AS avg_fee_low, COUNT(*) AS brands FROM fees f JOIN brands b USING (brand_slug) WHERE f.initial_fee_low_usd IS NOT NULL GROUP BY 1 HAVING COUNT(*) >= 10 ORDER BY 2 DESC;

-- Agreement terms: shortest initial term with a renewal option
SELECT b.brand_name, a.term_years, a.renewal_term_years, a.renewal_count FROM agreement_terms a JOIN brands b USING (brand_slug) WHERE a.renewal_count >= 1 ORDER BY a.term_years LIMIT 10;

-- The ten most similar brands to Great Clips
SELECT rank, alternative_name, same_sub_category, alternative_investment_low_usd, alternative_total_outlets FROM alternatives WHERE brand_slug = 'great-clips' ORDER BY rank;

-- Where one brand ranks against its peers
SELECT metric, value, rank, peers, peer_median, rank_order, peer_group FROM peer_ranks WHERE brand_slug = 'great-clips';

-- Highest revenue relative to investment (revenue is not profit)
SELECT b.brand_name, v.comparable_annual_revenue_usd, v.investment_midpoint_usd, v.revenue_to_investment FROM value_ratios v JOIN brands b USING (brand_slug) WHERE v.revenue_to_investment IS NOT NULL ORDER BY v.revenue_to_investment DESC LIMIT 10;

-- Year-by-year terminations for one brand
SELECT year, outlets_start, terminated, non_renewed, ceased_other, transferred, outlets_end FROM turnover_by_year WHERE brand_slug = 'subway' ORDER BY year;
