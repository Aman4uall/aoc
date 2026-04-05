import unittest

from aoc.models import GeographicScope, ProvenanceTag, SourceDomain, SourceKind, SourceRecord
from aoc.publish import references_markdown


class PublishTests(unittest.TestCase):
    def test_references_markdown_uses_numbered_bibliography_style(self):
        source_index = {
            "patent_CN109553539B": SourceRecord(
                source_id="patent_CN109553539B",
                source_kind=SourceKind.PATENT,
                source_domain=SourceDomain.TECHNICAL,
                title="Preparation method of benzalkonium chloride",
                url_or_doi="https://patents.google.com/patent/CN109553539B/en",
                citation_text="CN109553539B - Preparation method of benzalkonium chloride - Google Patents.",
                provenance_tag=ProvenanceTag.SOURCED,
                geographic_scope=GeographicScope.UNKNOWN,
                reference_year=2021,
            ),
            "site_pcpir_dahej": SourceRecord(
                source_id="site_pcpir_dahej",
                source_kind=SourceKind.WEB,
                source_domain=SourceDomain.SITE,
                title="Gujarat PCPIR: A Premier Chemical Hub in India",
                url_or_doi="https://pcpir.gujarat.gov.in/",
                citation_text="Gujarat PCPIR. A Premier Chemical Hub in India.",
                provenance_tag=ProvenanceTag.SOURCED,
                geographic_scope=GeographicScope.INDIA,
            ),
        }

        markdown = references_markdown(source_index)

        self.assertIn("## References", markdown)
        self.assertIn("1. Gujarat PCPIR. *Gujarat PCPIR: A Premier Chemical Hub in India*. n.d.", markdown)
        self.assertIn("2. CN109553539B - Preparation method of benzalkonium chloride - Google Patents. *Preparation method of benzalkonium chloride*. 2021.", markdown)
        self.assertIn("Available at: https://pcpir.gujarat.gov.in/.", markdown)
        self.assertIn("[Source ID: site_pcpir_dahej; Domain: site; Geography: india]", markdown)


if __name__ == "__main__":
    unittest.main()
