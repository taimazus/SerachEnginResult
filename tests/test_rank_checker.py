import pytest

import rank_checker
from rank_checker import check_google_rank, domain_matches, normalize_domain


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://www.example.ir/path", "www.example.ir"),
        ("example.ir/", "example.ir"),
        ("sub.example.ir", "sub.example.ir"),
        ("مثال.ایران", "xn--mgbh0fb.xn--mgba3a4f16a"),
    ],
)
def test_normalize_domain(value, expected):
    assert normalize_domain(value) == expected


def test_domain_match_accepts_subdomains_but_not_suffix_impostors():
    assert domain_matches("https://shop.example.ir/product", "example.ir")
    assert not domain_matches("https://notexample.ir/", "example.ir")
    assert not domain_matches("https://example.ir.attacker.test/", "example.ir")


@pytest.mark.parametrize(
    ("query", "domain", "max_pages"),
    [("", "example.ir", 1), ("query", "", 1), ("query", "example.ir", 0), ("query", "example.ir", 6)],
)
def test_invalid_search_inputs_fail_before_browser_launch(query, domain, max_pages):
    with pytest.raises(ValueError):
        check_google_rank(query, domain, max_pages)


class FakeLocator:
    def __init__(self, selector, links, captcha):
        self.selector = selector
        self.links = links
        self.captcha = captcha

    def count(self):
        return int(self.captcha and self.selector == "form#captcha-form")

    def evaluate_all(self, _script):
        return self.links


class FakePage:
    def __init__(self, links, captcha=False):
        self.links = links
        self.captcha = captcha
        self.url = "https://www.google.com/search"

    def goto(self, url, **_kwargs):
        self.url = url

    def locator(self, selector):
        return FakeLocator(selector, self.links, self.captcha)


class FakeBrowser:
    def __init__(self, pages):
        self.pages = iter(pages)
        self.closed = False

    def new_context(self, **_kwargs):
        return self

    def new_page(self):
        return next(self.pages)

    def close(self):
        self.closed = True


class FakePlaywrightManager:
    def __init__(self, browser):
        self.chromium = self
        self.browser = browser

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def launch(self, **_kwargs):
        return self.browser


def test_check_returns_rank_and_page_and_closes_browser(monkeypatch):
    browser = FakeBrowser(
        [
            FakePage(
                [
                    "https://other.example/one",
                    "https://shop.example.ir/product",
                ]
            )
        ]
    )
    monkeypatch.setattr(
        rank_checker, "sync_playwright", lambda: FakePlaywrightManager(browser)
    )

    result = check_google_rank("query", "example.ir", max_pages=1)

    assert result["status"] == "found"
    assert result["rank"] == 2
    assert result["result_page"] == 1
    assert browser.closed


def test_check_stops_and_closes_browser_on_captcha(monkeypatch):
    browser = FakeBrowser([FakePage([], captcha=True)])
    monkeypatch.setattr(
        rank_checker, "sync_playwright", lambda: FakePlaywrightManager(browser)
    )

    result = check_google_rank("query", "example.ir", max_pages=1)

    assert result["status"] == "captcha"
    assert result["rank"] is None
    assert browser.closed
