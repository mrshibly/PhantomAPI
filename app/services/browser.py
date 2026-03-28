"""PhantomAPI — Browser automation engine.

Launches a persistent headless Chrome instance via Playwright
and interacts with chatgpt.com to generate responses.
"""

import asyncio
import threading
from app.config import settings


class BrowserEngine(threading.Thread):
    """A dedicated thread that runs an async Playwright browser.

    This avoids blocking the FastAPI event loop while still giving
    us a persistent browser instance that can handle sequential requests.
    """

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.loop = asyncio.new_event_loop()
        self.ready = threading.Event()
        self.browser = None
        self.playwright = None

    # ------------------------------------------------------------------
    # Thread lifecycle
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Thread entry point — start browser and run the event loop forever."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._launch())
        self.ready.set()
        print("[PhantomAPI] ⚡ Browser engine ready.")
        self.loop.run_forever()

    async def _launch(self) -> None:
        """Launch a stealth Chromium browser."""
        from playwright.async_api import async_playwright

        print("[PhantomAPI] 🚀 Launching browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=settings.HEADLESS,
            channel="chrome",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
            ],
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(self, prompt: str) -> str:
        """Send a prompt to ChatGPT and return the response text.

        This is a blocking call that schedules work on the browser
        thread's event loop and waits for the result.
        """
        if not self.ready.wait(timeout=30) or self.browser is None:
            raise RuntimeError("Browser engine is not ready. Is Chrome installed?")

        future = asyncio.run_coroutine_threadsafe(
            self._interact(prompt), self.loop
        )
        return future.result(timeout=settings.BROWSER_TIMEOUT // 1000 + 30)

    # ------------------------------------------------------------------
    # Private — browser interaction
    # ------------------------------------------------------------------

    async def _interact(self, prompt: str) -> str:
        """Open a new ChatGPT session, send the prompt, and scrape the reply."""
        context = await self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )

        # Hide the webdriver flag so ChatGPT thinks we're a real user
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page = await context.new_page()

        try:
            page.set_default_timeout(settings.BROWSER_TIMEOUT)

            # Navigate to ChatGPT
            await page.goto("https://chatgpt.com/", wait_until="domcontentloaded")

            # Type the prompt
            await page.wait_for_selector("#prompt-textarea", timeout=60000)
            await page.fill("#prompt-textarea", prompt)
            await asyncio.sleep(0.5)
            await page.press("#prompt-textarea", "Enter")

            # Wait for the assistant to start responding
            await page.wait_for_selector(
                '[data-message-author-role="assistant"]',
                timeout=settings.BROWSER_TIMEOUT,
            )

            # Poll until the response stabilises (no new text for ~2 seconds)
            last_text = ""
            unchanged_count = 0
            while unchanged_count < 4:
                elements = await page.query_selector_all(
                    '[data-message-author-role="assistant"]'
                )
                if elements:
                    current_text = await elements[-1].inner_text()
                    if current_text == last_text and current_text.strip():
                        unchanged_count += 1
                    else:
                        last_text = current_text
                        unchanged_count = 0
                await asyncio.sleep(0.5)

            return last_text.strip()

        except Exception as exc:
            print(f"[PhantomAPI] ❌ Browser error: {exc}")
            raise
        finally:
            await page.close()
            await context.close()


# ---------------------------------------------------------------------------
# Singleton — created once at import time, started in app lifespan
# ---------------------------------------------------------------------------
engine = BrowserEngine()
