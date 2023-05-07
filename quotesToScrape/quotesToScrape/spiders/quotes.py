from scrapy_playwright.page import PageMethod
from scrapy.selector import Selector
import scrapy


class QuotesSpider(scrapy.Spider):
    name = "quotes"
    custom_settings = {
        "FEED_URI": "consoleMessage.json",
        "FEED_FORMAT": "json",
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    def start_requests(self):
        yield scrapy.Request(
            url="http://quotes.toscrape.com/js",
            meta={
                "playwright": True,
                "playwright_page_methods": [PageMethod("wait_for_selector", ".quote")],
                "playwright_include_page": True,
            },
            errback=self.close_page,
        )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        page.on("console", lambda msg: print(msg.text))

        async with page.expect_console_message() as msg_info:
            await page.evaluate("console.log('Hola desde la consola')")
        msg = await msg_info.value
        valores = await msg.args[0].json_value()

        yield {"Mensaje": valores}

    async def close_page(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()
