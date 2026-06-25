import unittest

from packages.news_layer.news_policy import classify_sec_filing, clean_text, parse_yahoo_rss


SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8" ?>
<rss><channel>
  <item>
    <title>Apple announces executive change</title>
    <link>https://example.com/aapl-exec</link>
    <description><![CDATA[Company update with <b>details</b>.]]></description>
    <pubDate>Wed, 25 Jun 2026 14:30:00 GMT</pubDate>
  </item>
</channel></rss>
"""


class NewsPolicyLayerTest(unittest.TestCase):
    def test_parse_yahoo_rss(self) -> None:
        items = parse_yahoo_rss(SAMPLE_RSS, "AAPL", limit=10)

        self.assertEqual(1, len(items))
        self.assertEqual("Apple announces executive change", items[0].title)
        self.assertEqual("company_news", items[0].category)
        self.assertEqual(["AAPL"], items[0].symbols)
        self.assertIn("2026-06-25T14:30:00", items[0].published_at)

    def test_classify_sec_filing_marks_8k_as_management_candidate(self) -> None:
        self.assertEqual("management_change", classify_sec_filing("8-K", "aapl-item-5-02.htm"))
        self.assertEqual("governance", classify_sec_filing("8-K", "aapl-8k.htm"))
        self.assertEqual("sec_filing", classify_sec_filing("10-K", "aapl-10k.htm"))

    def test_clean_text_removes_html(self) -> None:
        self.assertEqual("Hello World", clean_text("<p>Hello&nbsp;<b>World</b></p>"))


if __name__ == "__main__":
    unittest.main()
