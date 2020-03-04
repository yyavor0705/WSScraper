import scrapy


class TableItem(scrapy.Item):
    name = scrapy.Field()
    category = scrapy.Field()
    model = scrapy.Field()
    upc_code = scrapy.Field()
    unit = scrapy.Field()
    min_lots = scrapy.Field()
    whole_sale_price = scrapy.Field()
    regular_price = scrapy.Field()


class AuthorSpider(scrapy.Spider):
    name = 'wsscrap'

    start_urls = ['https://www.webstaurantstore.com/office-products.html']

    def parse(self, response):
        # open product types links
        for prod_type in response.css('.grid__block-wrap div.grid__block'):
            type_page_link = prod_type.css('a::attr(href)').get()
            self.logger.info("Found type page link: {}".format(type_page_link))
            if type_page_link is not None:
                yield response.follow(type_page_link, callback=self.parse_types_page)

    def parse_types_page(self, response):
        # open product types categories links
        for category in response.css('div.grid-module.grid-children-max div.grid-children'):
            category_page_link = category.css('a::attr(href)').get()
            self.logger.info("Found category page link: {}".format(category_page_link))
            if category_page_link is not None:
                yield response.follow(category_page_link, callback=self.parse_products_page)

    def parse_products_page(self, response):
        for product in response.css('#product_listing div.ag-item.gtm-product'):
            product_page_link = product.css('div.details a.description::attr(href)').get()
            if product_page_link is not None:
                yield response.follow(product_page_link, callback=self.final_product_parse)

        next_products_page = response.css("div.pagination ul li a::attr(href)").get()
        if next_products_page is not None:
            yield response.follow(next_products_page, self.parse_products_page)

    def final_product_parse(self, response):
        name = response.css("h1.page-header::text").get()

        category = None
        category_li_texts = response.css("div.global-header div.global-breadcrumb.container ul li a span::text").extract()
        if len(category_li_texts) > 1:
            category = category_li_texts[1]

        model = None
        model_selector = response.css("span.mfr-number::text")
        if model_selector:
            model = model_selector.get().strip()

        upc_code = None
        upc_selector = response.css("span.product__stat-desc::text")
        if upc_selector:
            upc_code = upc_selector.get().strip()

        price_selector = response.css("p.price")
        unit = None
        whole_sale_price = None
        if price_selector:
            span_selectors = price_selector.css("span::text")
            if span_selectors:
                unit = span_selectors[1].get()
                whole_sale_price = span_selectors[0].get()

        min_lots = None
        min_lots_selector = response.css("div.pricing label::text")
        if min_lots_selector:
            min_lots = min_lots_selector.get().strip()

        regular_price = None
        regular_price_selector = response.css("div.pricing table tbody tr td::text")
        if regular_price_selector:
            regular_price = regular_price_selector.get()
            regular_price_span_selector = response.css("div.pricing table tbody tr td span::text")
            if regular_price_span_selector:
                unit = regular_price_span_selector.get()
                regular_price = "{}{}".format(regular_price, unit)

        return TableItem(name=name, category=category, model=model, upc_code=upc_code, unit=unit, min_lots=min_lots,
                         whole_sale_price=whole_sale_price, regular_price=regular_price)
