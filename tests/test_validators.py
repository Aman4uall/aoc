import unittest

from aoc.models import (
    GeographicScope,
    ProcessTemplate,
    ProjectBasis,
    ProjectConfig,
    ResearchBundle,
    SourceDomain,
    SourceKind,
    SourceRecord,
)
from aoc.validators import validate_research_bundle


class ValidatorTests(unittest.TestCase):
    def test_india_only_research_bundle_validation(self):
        config = ProjectConfig(
            project_id="eg",
            basis=ProjectBasis(
                target_product="Ethylene Glycol",
                capacity_tpa=200000,
                target_purity_wt_pct=99.9,
                process_template=ProcessTemplate.ETHYLENE_GLYCOL_INDIA,
                india_only=True,
            ),
            require_india_only_data=True,
        )
        bundle = ResearchBundle(
            sources=[
                SourceRecord(
                    source_id="s1",
                    source_kind=SourceKind.HANDBOOK,
                    source_domain=SourceDomain.TECHNICAL,
                    title="Tech",
                    citation_text="Tech",
                    geographic_scope=GeographicScope.GLOBAL,
                    reference_year=2025,
                )
            ],
            corpus_excerpt="seed",
        )
        issues, missing, stale = validate_research_bundle(bundle, config)
        self.assertTrue(issues)
        self.assertIn("india_sources", missing)
        self.assertFalse(stale)

    def test_india_research_bundle_passes_when_coverage_exists(self):
        config = ProjectConfig(
            project_id="eg",
            basis=ProjectBasis(
                target_product="Ethylene Glycol",
                capacity_tpa=200000,
                target_purity_wt_pct=99.9,
                process_template=ProcessTemplate.ETHYLENE_GLYCOL_INDIA,
                india_only=True,
            ),
            require_india_only_data=True,
        )
        bundle = ResearchBundle(
            sources=[
                SourceRecord(
                    source_id="s1",
                    source_kind=SourceKind.HANDBOOK,
                    source_domain=SourceDomain.TECHNICAL,
                    title="Tech",
                    citation_text="Tech",
                    geographic_scope=GeographicScope.GLOBAL,
                    reference_year=2025,
                ),
                SourceRecord(
                    source_id="s2",
                    source_kind=SourceKind.MARKET,
                    source_domain=SourceDomain.ECONOMICS,
                    title="India market",
                    citation_text="India market",
                    geographic_scope=GeographicScope.INDIA,
                    geographic_label="India",
                    country="India",
                    reference_year=2025,
                    normalization_year=2025,
                ),
                SourceRecord(
                    source_id="s3",
                    source_kind=SourceKind.COMPANY_REPORT,
                    source_domain=SourceDomain.SITE,
                    title="India site",
                    citation_text="India site",
                    geographic_scope=GeographicScope.INDIA,
                    geographic_label="India",
                    country="India",
                    reference_year=2025,
                ),
                SourceRecord(
                    source_id="s4",
                    source_kind=SourceKind.UTILITY,
                    source_domain=SourceDomain.UTILITIES,
                    title="India utility",
                    citation_text="India utility",
                    geographic_scope=GeographicScope.STATE,
                    geographic_label="Gujarat",
                    country="India",
                    reference_year=2025,
                    normalization_year=2025,
                ),
            ],
            technical_source_ids=["s1"],
            india_source_ids=["s2", "s3", "s4"],
            corpus_excerpt="seed",
        )
        issues, missing, stale = validate_research_bundle(bundle, config)
        self.assertFalse(issues)
        self.assertFalse(missing)
        self.assertFalse(stale)
