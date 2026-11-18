import unittest
from growthaudit.htmlcheck import analyze_html,PageParser

HTML="""<!doctype html><html lang='en'><head>
<title>Shopify Automation for Growing Retail Businesses</title>
<meta name='description' content='Get tailored Shopify webhook processing, inventory alerts, CRM integration and secure returns workflows with a clear engineering scope and source ownership.'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<link rel='canonical' href='https://www.example.com/services'>
<script type='application/ld+json'>{"@context":"https://schema.org","@type":"Service"}</script>
</head><body><header><a href='/'>Home</a><a href='/contact'>Contact our team</a></header>
<h1>Shopify Automation Services</h1><h2>Inventory</h2>
<img src='/demo.png' alt='Shopify inventory operations dashboard'>
<form><label for='email'>Email</label><input id='email' name='email'></form>
</body></html>"""
HEADERS={"x-content-type-options":"nosniff","content-security-policy":"default-src 'self'"}

class HTMLTests(unittest.TestCase):
    def test_full_html_produces_17_checks(self):
        r=analyze_html("https://www.example.com/services",HTML,HEADERS,robots_status="found",sitemap_status="found")
        self.assertEqual(len(r["findings"]),17)
        self.assertEqual(r["summary"]["checks"],17)
        self.assertGreater(r["score"],75)
    def test_score_is_checklist_only(self):
        r=analyze_html("https://www.example.com/services",HTML,HEADERS,robots_status="found",sitemap_status="found")
        self.assertIn("Not a Google score",r["score_explanation"])
        self.assertIsNone(r["measurements"]["core_web_vitals"])
    def test_missing_metadata_is_flagged(self):
        r=analyze_html("https://www.example.com/","<html><body><h2>hello</h2></body></html>",{})
        failures={x["id"] for x in r["findings"] if not x["passed"]}
        self.assertTrue({"SEO-01","SEO-02","SEO-04","SEO-05","UX-01","CRO-01"}<=failures)
    def test_noindex_is_flagged(self):
        r=analyze_html("https://www.example.com/","<html><head><meta name='robots' content='noindex'></head></html>",{})
        self.assertFalse(next(x["passed"] for x in r["findings"] if x["id"]=="SEO-03"))
    def test_x_robots_header_noindex(self):
        r=analyze_html("https://www.example.com/",HTML,{"x-robots-tag":"noindex"})
        self.assertFalse(next(x["passed"] for x in r["findings"] if x["id"]=="SEO-03"))
    def test_canonical_mismatch(self):
        r=analyze_html("https://www.example.com/pricing",HTML,{})
        self.assertFalse(next(x["passed"] for x in r["findings"] if x["id"]=="SEO-05"))
    def test_no_canonical(self):
        r=analyze_html("https://www.example.com/","<html><head><title>A nice title</title></head></html>",{})
        self.assertFalse(next(x["passed"] for x in r["findings"] if x["id"]=="SEO-05"))
    def test_image_without_alt(self):
        html=HTML.replace("alt='Shopify inventory operations dashboard'","")
        r=analyze_html("https://www.example.com/services",html,{})
        self.assertEqual(r["page"]["images_missing_alt"],1)
        self.assertFalse(next(x["passed"] for x in r["findings"] if x["id"]=="UX-03"))
    def test_invalid_jsonld(self):
        html=HTML.replace('{"@context":"https://schema.org","@type":"Service"}','{"invalid-json":')
        r=analyze_html("https://www.example.com/services",html,{})
        self.assertEqual(r["page"]["jsonld_invalid"],1)
        self.assertFalse(next(x["passed"] for x in r["findings"] if x["id"]=="SEO-07"))
    def test_contact_link_detected(self):
        r=analyze_html("https://www.example.com/services",HTML,{})
        self.assertTrue(next(x["passed"] for x in r["findings"] if x["id"]=="CRO-01"))
    def test_noncontact_link_not_imply_contact(self):
        html="<html><body><a href='/about'>Our story</a><h1>Home</h1></body></html>"
        r=analyze_html("https://www.example.com/",html,{})
        self.assertFalse(next(x["passed"] for x in r["findings"] if x["id"]=="CRO-01"))
    def test_form_counts(self):
        r=analyze_html("https://www.example.com/services",HTML,{})
        self.assertEqual(r["page"]["forms"],1)
    def test_unsafe_markup_not_executed(self):
        html="<html><head><title>X<script>alert(1)</script> bad example</title></head></html>"
        r=analyze_html("https://www.example.com/",html,{})
        self.assertTrue(isinstance(r["page"]["title"],str))
    def test_plain_http_fails_transport(self):
        r=analyze_html("http://www.example.com/services",HTML,{})
        self.assertFalse(next(x["passed"] for x in r["findings"] if x["id"]=="SEC-01"))
    def test_parser_tracks_anchors_only_inside_the_tag(self):
        p=PageParser();p.feed("<a href='/about'>About</a> Contact us without link")
        self.assertEqual(p.anchors[0]["text"],"About")
    def test_count_categories(self):
        r=analyze_html("https://www.example.com/services",HTML,{})
        cats={f["category"] for f in r["findings"]}
        self.assertEqual(len(cats),5)

if __name__=="__main__":unittest.main()
