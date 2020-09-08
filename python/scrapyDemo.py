import scrapy

from scrapy.crawler import CrawlerProcess

class GameLogSpider(scrapy.Spider):
    name = 'blogspider'
    start_urls = [
                   'https://www.espn.com/nba/player/gamelog/_/id/2991230',
                  'https://www.espn.com/nba/player/gamelog/_/id/3064440',
                  'https://www.espn.com/nba/player/gamelog/_/id/6450'
    ]
    custom_settings = {'FEED_FORMAT': 'csv',
                       'FEED_URI': 'items.csv'}
    months = ["january",
              "febuary",
              "march",
              "april",
              "may",
              "june",
              "july",
              "august",
              "september",
              "october",
              "november",
              "december"]

    def parse(self, response):
        # Regular Season ESPN
        header = response.xpath('//*[@id="fittPageContainer"]/div[2]/div[5]/div/div/div[1]/div/div[2]/div[2]/div/section/div/div/div[2]/table')
        player_id = response.url.split('/')[-1]
        scraped_info = dict(player_id = player_id)

        # 14 values for header_cols
        header_cols = header.xpath('.//th/text()').extract()
        assert len(header_cols) == 14
        header_cols.insert(0, 'Game Date')


        rows = header.xpath('.//td/text()').extract()
        print(f'Row length: {len(rows)}')

        month_indexes = list()
        for idx, row in enumerate(rows):
            if type(row) == str and row.lower() in self.months:
                print('Month detected')
                month_indexes.append(idx)

        self.remove_list_indexes(rows, remove_indexes=month_indexes)
        print(f'Trimmed length: {len(rows)}')
        print(rows[:15])
        if len(rows) > 15:
            print(rows[15:])

        for idx, value in enumerate(rows):
            key = header_cols[idx % 15]
            print(f'{idx} {key} {value}')
            scraped_info[key] = value
            if idx != 0 and (idx+1) % 15 == 0:
                print(f'Edge: {idx} {value}')
                yield scraped_info

    def remove_list_indexes(self, rows, remove_indexes):
        offset = 0
        for idx in remove_indexes:
            rows.pop(idx-offset)
            offset += 1


process = CrawlerProcess()

process.crawl(GameLogSpider)
process.start()  # the script will block here until the crawling is finish

# team - header = response.xpath('//*[@id="fittPageContainer"]/div[3]/div[1]/div/div[1]/div[2]')
# header.xpath('//a/@href').extract()