import asyncio
import random
from bs4 import BeautifulSoup
from camoufox import AsyncCamoufox


MAX_TIMEOUT = 20000

proxies = [
            f"<user>:<password>@<host>:{port}"
            for port in range(10000, 10200)
        ]

portals = [
    "jobs.lever.co",
]

engines = {
    "google": "https://www.google.com/search?q={search_query}",
    "bing": "https://www.bing.com/search?q={search_query}",
    "brave": "https://search.brave.com/search?q={search_query}/{letter}",
    "yandex": "https://yandex.com/search/?text={search_query}",
    "duckduckgo": "https://duckduckgo.com/?q={search_query}",
}

reversed_engines = {v: k for k, v in engines.items()}

# alphabet = "abcdefghijklmnopqrstuvwxyz"

async def scrape():
    for engine in engines.values():
        temp = random.choice(proxies)
        proxy = {
            "server": temp.split("@")[1],
            "username": temp.split(":")[0],
            "password": temp.split(":")[1].split("@")[0],
        }
        
        # Stealth browser may be needed for some engines
        # async with AsyncCamoufox(headless=False, geoip=True, humanize=True) as browser:
        
        import playwright.async_api as playwright
        async with playwright.async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            for portal in portals:
                # for letter in alphabet:
                search_query = f"site:{portal}"
                # url = engine.format(search_query=search_query, letter=letter)
                url = engine.format(search_query=search_query)
                print(f"Scraping {url}")
                extracted_links = []
                await page.goto(url)
                await asyncio.sleep(15)  # Adjust if needed to allow full page load
                index = 1
                retry = 0
                while True:
                    try:
                        print(f"Extracting links from page {index}, query: {search_query}")
                        index += 1
                        match reversed_engines.get(engine):
                            case "google":
                                # Ensure at least one <h3> tag is loaded
                                await page.wait_for_selector("h3", timeout=MAX_TIMEOUT)
                                
                                # Get the full HTML content of the page and parse it
                                content = await page.content()
                                soup = BeautifulSoup(content, 'html.parser')
                                h3_tags = soup.find_all('h3', recursive=True)
                                
                                for h3 in h3_tags:
                                    # Check if the direct parent is an <a> tag
                                    parent = h3.parent
                                    if parent and parent.name == 'a':
                                        href = parent.get('href')
                                        if href:
                                            extracted_links.append(href)
                                            
                                with open(f'scraping/google_{portal}.txt', 'a') as f:
                                    for link in extracted_links:
                                        f.write(f"\n{link}")
                                                    
                                # Find the "Next" button to navigate to the next page
                                next_button = await page.query_selector("a#pnnext")
                                if not next_button:
                                    break
                                
                                next_url = await next_button.get_attribute("href")
                                if not next_url:
                                    break
                                
                                await page.goto(f"https://www.google.com{next_url}")
                            case "bing":
                                await page.wait_for_selector("h2", timeout=MAX_TIMEOUT)
                                
                                # Get the full HTML content of the page and parse it
                                content = await page.content()
                                soup = BeautifulSoup(content, 'html.parser')
                                h3_tags = soup.find_all('h2', recursive=True)
                                
                                for h3 in h3_tags:
                                    # Check if the direct parent is an <a> tag
                                    href = h3.find('a').get('href')
                                    if href:
                                        extracted_links.append(href)
                                        
                                with open(f'scraping/bing_{portal}.txt', 'a') as f:
                                    for link in extracted_links:
                                        f.write(f"\n{link}")
                                                    
                                # Find the "Next" button to navigate to the next page
                                next_button = await page.query_selector("a.sb_pagN.sb_pagN_bp.b_widePag.sb_bp")
                                if not next_button:
                                    break
                                
                                next_url = await next_button.get_attribute("href")
                                if not next_url:
                                    break
                                
                                await page.goto(f"https://www.bing.com{next_url}")   
                        
                            case "yandex":
                                await page.wait_for_selector("ul", timeout=MAX_TIMEOUT)
                                
                                # Get the full HTML content of the page and parse it
                                content = await page.content()
                                soup = BeautifulSoup(content, 'html.parser')
                                result = soup.find('ul', id="search-result", recursive=True)
                                tags = result.find_all('li', recursive=True)
                                
                                for li in tags:
                                    link = li.find('a', recursive=True)
                                    if link:
                                        href = link.get('href')
                                        if href:
                                            extracted_links.append(href)
                                            
                                with open(f'scraping/yandex_{portal}.txt', 'a') as f:
                                    for link in extracted_links:
                                        f.write(f"\n{link}")
                                                    
                                # Find the "Next" button to navigate to the next page
                                next_button = await page.query_selector('a[aria-label="Next page"]')
                                if not next_button:
                                    break
                                
                                next_url = await next_button.get_attribute("href")
                                if not next_url:
                                    break
                                
                                await page.goto(f"https://yandex.com{next_url}")

                            case "duckduckgo":
                                # Load results before
                                while True:
                                    try:
                                        next_button = await page.query_selector('button#more-results')
                                        if not next_button:
                                            break
                                        is_disabled = await next_button.get_attribute("disabled")
                                        if is_disabled:
                                            break
                                        await next_button.click()
                                        await asyncio.sleep(3)
                                    except Exception as e:
                                        break
                                
                                await page.wait_for_selector("article", timeout=MAX_TIMEOUT)
                                
                                # Get the full HTML content of the page and parse it
                                content = await page.content()
                                soup = BeautifulSoup(content, 'html.parser')
                                elements = soup.find_all('article', recursive=True)
                                
                                for element in elements:
                                    # Check if the direct parent is an <a> tag
                                    tag = element.find('a', recursive=True)
                                    href = tag.get('href')
                                    if href:
                                        extracted_links.append(href)
                                            
                                with open(f'scraping/duckduckgo_{portal}.txt', 'a') as f:
                                    for link in extracted_links:
                                        f.write(f"\n{link}")
                                break # no next url
                                        
                            case "brave":
                                await page.wait_for_selector("div", timeout=MAX_TIMEOUT)
                                
                                # Get the full HTML content of the page and parse it
                                content = await page.content()
                                soup = BeautifulSoup(content, 'html.parser')
                                parent = soup.find('div', id="results", recursive=True)
                                divs = parent.find_all('div', recursive=True)

                                for elem in divs:
                                    tag = elem.find('a', recursive=True)
                                    if tag:
                                        href = tag.get('href')
                                        if href:
                                            extracted_links.append(href)
                                            
                                with open(f'scraping/brave_{portal}.txt', 'a') as f:
                                    for link in extracted_links:
                                        f.write(f"\n{link}")
                                                    
                                # Find the "Next" button to navigate to the next page
                                parent = await page.query_selector('div#pagination')
                                children = await parent.query_selector_all('a')
                                if children:
                                    target_index = 1 if len(children) > 1 else 0
                                    next_button = children[target_index]
                                if not next_button:
                                    break
                                
                                next_url = await next_button.get_attribute("href")
                                if not next_url:
                                    break
                                
                                if "offset" in page.url:
                                    current = int(page.url.split("offset=")[1].split("&")[0])
                                    future = int(next_url.split("offset=")[1].split("&")[0])
                                    if future >= current:
                                        break
                                
                                await page.goto(f"https://search.brave.com{next_url}")
                                
                        await asyncio.sleep(5)  # Wait for the next page to load
                    except Exception as e:
                        print(f"Error on page {index} - {search_query}:", str(e))
                        retry += 1
                        if retry > 2:
                            break
                        continue
                
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape())
    print("Scraping completed.")