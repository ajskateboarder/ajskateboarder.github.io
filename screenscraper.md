# Building a parallelized screen scraper

<figure>
  <img src="./screenscraper.png" alt="Distributed web scraping process" />
  <figcaption>Scraping process with headless mode disabled</figcaption>
</figure>

<kbd>python</kbd> <kbd>selenium</kbd> <kbd>web-scraping</kbd> <kbd>ecommerce</kbd>

The source code for this is available on GitHub: [https://github.com/ajskateboarder/wordsmyth/tree/minimal/src/crawling](https://github.com/ajskateboarder/wordsmyth/tree/minimal/src/crawling)

Web scraping, particularly for the purpose of building large datasets, is often overlooked when speed is required. I have yet to see a project out in the wild that parallelizes Selenium instances, which is frankly kind of weird since it's what powers a majority of data driven projects and datasets. Like, how did [this dataset](https://jmcauley.ucsd.edu/data/amazon/) come into fruition, which definitely wasn't built from a synchronous web scraper? 

Here, I'm going to explain what I did to build an optimal, parallel screen scraper to aggregate tons of data, and what tools and logic to apply. Most logic mentioned here would also apply for scrapers that simply parse HTML from an HTTP library.

Yes, I did look into using [Grid](https://www.selenium.dev/documentation/grid/) before going and building my thing from scratch, and don't really recommend it for scraping -- It's more for testing from the looks of it. Grid seems to rely more on a static configuration, which doesn't work particularly well for a scraper that needs to share state between all nodes (and I mean a lot of state).

## Layout

The end goal of every screen scraping project will obviously vary, but in my project, I intend to do the following on Amazon:

1\. Scrape an initial set of product IDs from links from [best selling](https://amazon.com/gp/bestselling)

2\. Login with given user credentials, hand any CAPTCHAs to user

3\. For every ID
  
- 3a. Collect product data, such as title, price, rating, review proportionality

- 3b. Collect other product IDs from visited pages
  
- 3c. Collect a balanced amount of text reviews for each star category (1 through 5) from each browser, based on mentioned review proportionality
  
- 3d. Pipe above data to a processor

4\. Repeat steps 1-3 with newly aggregated product IDs

This project makes use of seven browsers, one running before step 1 and six running in parallel after. The implementation details of the first step don't really matter; other steps are probably more important.

## Orchestrating multiple browsers

This simply involves using a ThreadPoolExecutor or something similar to create and send commands to multiple browsers at once.

```py
...
with futures.ThreadPoolExecutor() as executor:
    browsers = list(
        map(
            lambda fut: fut.result(),
            futures.as_completed(
                [executor.submit(Firefox, options=opts) for _ in range(5)]
            ),
        )
    )
```

```py
with ThreadPoolExecutor() as executor:
  for browser in browsers:
      executor.submit(lambda browser: some_function(browser))
```

To propagate exceptions, simply add a done callback and attempt to access the future's result from the callback:

```py
try:
    future.result()
except SomeException as e:
    ...
```

This works nicely in the case of handling custom error pages and such. 

## CAPTCHA handling

Not sure if this has been done in the past, but from the looks of it, it sure hasn't. Simply pass CAPTCHA responses from the browser directly to the user to solve. As of now, this seems to be a foolproof strategy to scrape sites that require some kind of human authentication, and works with all forms of CAPTCHA to some extent. After the user solves them, the site leaves the scraper alone for hours, if not entire months until another is requested.

In Amazon's case, this is particularly easy since CAPTCHAs are (still, in 2024) sent as plain images, which also allows them to be displayed and answered directly from the [kitty](https://sw.kovidgoyal.net/kitty/) terminal.

I use a hook set through a class attribute to receive the CAPTCHA solution from the script and send it into the browser:

```py
captcha = self.captcha_hook(browser)
...
browser.find_element(
    By.CSS_SELECTOR, "input[name=cvf_captcha_input]"
).send_keys(captcha)
browser.find_element(
    By.CSS_SELECTOR, "input[name=cvf_captcha_captcha_action]"
).click()
```

The kitty CAPTCHA hook itself is defined in a script:

```py
def kitty_captcha(browser):
    # select the image url and display via kitty icat
    captcha_image = (
      browser.find_element("css selector", "img[alt='captcha']")
        .get_attribute("src")
    )
    subprocess.run(
      ["/usr/bin/kitty", "icat", captcha_image],
      check=True
    )
    return input("(login) Please solve the provided captcha: ")

main_scraper.captcha_hook = kitty_captcha
```

This is a good lesson to make your code configurable as soon as your project requires it. :)
