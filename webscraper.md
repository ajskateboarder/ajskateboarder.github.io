<hr />

# Building a distributed web scraper

<figure>
  <img src="./webscraper.png" alt="Distributed web scraping process" />
  <figcaption>Distributed web scraping process with headless mode disabled</figcaption>
</figure>

<kbd>python</kbd> <kbd>selenium</kbd> <kbd>web-scraping</kbd> <kbd>ecommerce</kbd>

The source code for this is available on GitHub: [https://github.com/ajskateboarder/wordsmyth/tree/minimal/src/crawling](https://github.com/ajskateboarder/wordsmyth/tree/minimal/src/crawling)

Web scraping, particularly for the purpose of building large datasets, is often overlooked when speed is required. I have yet to see a project out in the wild that parallelizes Selenium instances, which is frankly kind of weird since it's what powers a majority of data driven projects and datasets. Like, how did [this dataset](https://jmcauley.ucsd.edu/data/amazon/) come into fruition, which definitely wasn't built from a synchronous web scraper? 

Here, I'm going to explain what I did to build an optimal, parallel screen scraper to aggregate tons of data, and what tools and logic to apply. Most logic mentioned here would also apply for scrapers that simply parse HTML from an HTTP library.

Yes, I did look into using [Grid](https://www.selenium.dev/documentation/grid/) before going and building my thing from scratch, and don't really recommend it for scraping -- It's more for testing from the looks of it. Grid seems to rely more on a static configuration, which doesn't work particularly well for a scraper that needs to share state between all nodes (and I mean a lot of state). Grid is also a bit difficult to setup, with the need to [compose a Docker network](https://github.com/sleepless-se/selenium-grid-sample) and do other various shenanigans.

## Use multi-threaded Selenium instances

<hr />
