from scrapy_playwright.page import PageMethod
import scrapy
import json
import re


class QuotesSpider(scrapy.Spider):
    name = "quotes"

    def get_url(self, offset=1):
        return f"https://quotes.toscrape.com/js/page/{offset}/"

    def start_requests(self):
        yield scrapy.Request(
            url=self.get_url(),
            meta={
                "playwright": True,
                "playwright_page_methods": [PageMethod("wait_for_selector", ".quote")],
                "playwright_include_page": True,
                "offset": 1,
            },
            errback=self.close_page,
        )

    async def parse(self, response):
        offset = response.meta["offset"]

        # Preparando la pagina para hacer capturar los datos de la consola:
        page = response.meta["playwright_page"]
        page.on("console", lambda msg: print(msg.text))

        async with page.expect_console_message() as msg_info:
            await page.evaluate(
                "console.log(document.getElementsByTagName('script')[1].text)"
            )
        msg = await msg_info.value

        # Limpiando y construllendo el json que contiene la informacion deseada:
        script_tag = re.findall(r"data\s=\s\[.+?\];", msg.text.replace("\n", ""))
        quotes = json.loads(script_tag[0].replace(f"data = ", "").replace(";", ""))

        # Capturar los datos del json:
        for quote in quotes:
            yield {"author": quote["author"]["name"], "text": quote["text"]}

        # seguir las demas paginas:
        if response.xpath("//li[@class='next']"):
            yield scrapy.Request(
                url=self.get_url(offset=offset + 1),
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", ".quote")
                    ],
                    "playwright_include_page": True,
                    "offset": offset + 1,
                },
                errback=self.close_page,
            )

    async def close_page(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()
