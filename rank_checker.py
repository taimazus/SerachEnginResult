from urllib.parse import quote_plus, urlsplit

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright


MAX_PAGES = 5
PAGE_SIZE = 10


class RankCheckError(RuntimeError):
    pass


def normalize_domain(value: str) -> str:
    candidate = value.strip().lower()
    if not candidate:
        raise ValueError("دامنهٔ هدف الزامی است.")
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    host = urlsplit(candidate).hostname
    if not host:
        raise ValueError("دامنهٔ هدف معتبر نیست.")
    try:
        return host.rstrip(".").encode("idna").decode("ascii")
    except UnicodeError as error:
        raise ValueError("دامنهٔ هدف معتبر نیست.") from error


def domain_matches(url: str, target_domain: str) -> bool:
    target = normalize_domain(target_domain)
    host = (urlsplit(url).hostname or "").lower().rstrip(".")
    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError:
        return False
    return host == target or host.endswith(f".{target}")


def _captcha_detected(page) -> bool:
    return (
        "sorry/index" in page.url
        or page.locator("form#captcha-form").count() > 0
        or page.locator('iframe[src*="recaptcha"]').count() > 0
    )


def _launch_browser(chromium):
    failures = []
    for options in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
        try:
            return chromium.launch(headless=True, **options)
        except PlaywrightError as error:
            failures.append(str(error))

    raise RankCheckError(
        "مرورگر Chromium در کنار پروژه و Chrome/Edge نصب‌شده پیدا نشد. "
        "اتصال اینترنت را بررسی کنید و `run.bat` را دوباره اجرا کنید تا Chromium نصب شود. "
        f"جزئیات: {failures[-1]}"
    )


def verify_browser() -> None:
    with sync_playwright() as playwright:
        browser = _launch_browser(playwright.chromium)
        browser.close()


def check_google_rank(
    query: str, target_domain: str, max_pages: int = 3
) -> dict:
    if not query.strip():
        raise ValueError("عبارت جست‌وجو الزامی است.")
    target = normalize_domain(target_domain)
    if not 1 <= max_pages <= MAX_PAGES:
        raise ValueError(f"تعداد صفحه باید بین ۱ و {MAX_PAGES} باشد.")

    seen_urls = set()
    rank = 0
    try:
        with sync_playwright() as playwright:
            browser = _launch_browser(playwright.chromium)
            try:
                context = browser.new_context(locale="fa-IR")
                page = context.new_page()
                for page_index in range(max_pages):
                    start = page_index * PAGE_SIZE
                    url = (
                        "https://www.google.com/search"
                        f"?q={quote_plus(query)}"
                        f"&gl=ir&pws=0&start={start}"
                    )
                    page.goto(
                        url, wait_until="domcontentloaded", timeout=30_000
                    )
                    if _captcha_detected(page):
                        return {
                            "status": "captcha",
                            "rank": None,
                            "result_page": None,
                            "message": (
                                "Google CAPTCHA را نمایش داد؛ بررسی متوقف شد. "
                                "بعداً به‌صورت دستی دوباره امتحان کنید."
                            ),
                        }

                    links = page.locator("a:has(h3)").evaluate_all(
                        "elements => elements.map(element => element.href)"
                    )
                    for link in links:
                        if (
                            not link.startswith(("http://", "https://"))
                            or (urlsplit(link).hostname or "").lower()
                            in {"google.com", "www.google.com"}
                            or link in seen_urls
                        ):
                            continue
                        seen_urls.add(link)
                        rank += 1
                        if domain_matches(link, target):
                            return {
                                "status": "found",
                                "rank": rank,
                                "result_page": page_index + 1,
                                "message": f"دامنه در نتایج ارگانیک صفحهٔ {page_index + 1} پیدا شد.",
                            }
                return {
                    "status": "not_found",
                    "rank": None,
                    "result_page": None,
                    "message": f"دامنه در {max_pages} صفحهٔ بررسی‌شده پیدا نشد.",
                }
            finally:
                browser.close()
    except PlaywrightError as error:
        raise RankCheckError(
            f"اجرای مرورگر یا بارگذاری نتایج ناموفق بود: {error}"
        ) from error
