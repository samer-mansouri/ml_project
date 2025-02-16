import requests
from bs4 import BeautifulSoup
import json
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://www.tayara.tn/fr/ads/c/Véhicules/?page="
CAR_BASE_URL = "https://www.tayara.tn"
MAX_PAGE = 500
MIN_PRICE = 0  # Minimum price to consider
THREAD_COUNT = 4  # Number of threads to use

def scrape_car_details(link):
    try:
        response = requests.get(link)
        if response.status_code != 200:
            print(f"Failed to fetch car details from {link}")
            return {}

        soup = BeautifulSoup(response.text, 'html.parser')
        criteres_section = soup.find("ul", class_="grid gap-3 grid-cols-12")
        details = {}

        if criteres_section:
            criteres = criteres_section.find_all("li", class_="col-span-6 lg:col-span-3")
            for critere in criteres:
                key_tag = critere.find("span", class_="text-gray-600/80")
                value_tag = critere.find("span", class_="text-gray-700/80")
                if key_tag and value_tag:
                    key = key_tag.get_text(strip=True)
                    value = value_tag.get_text(strip=True)
                    details[key] = value
        else:
            print(f"No criteria found for car at {link}")

        return details
    except Exception as e:
        print(f"Error fetching details for {link}: {e}")
        return {}

def scrape_page(page):
    url = BASE_URL + str(page)
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to fetch page {page}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    results = []

    container = soup.find("div", class_="flex flex-wrap justify-evenly lg:justify-around xl:justify-center mt-10 mb-4 gap-y-5 gap-x-0 lg:gap-x-4 xl:gap-x-4")
    if not container:
        print(f"No data found on page {page}")
        return []

    articles = container.find_all("article", class_="mx-0")
    for article in articles:
        try:
            price_data = article.find("data", class_="font-bold font-arabic text-red-600 undefined")
            if price_data:
                price_text = price_data.get_text(strip=True).replace("DT", "").replace(",", "").strip()
                try:
                    price = int(float(price_text))
                except ValueError:
                    print(f"Invalid price format: {price_text}")
                    continue

                if price > MIN_PRICE:
                    title_tag = article.find("h2", class_="card-title font-arabic text-sm font-medium leading-5 text-gray-800 max-w-min min-w-full line-clamp-2 my-2")
                    link_tag = article.find("a")
                    image_tag = article.find("img")

                    title = title_tag.get_text(strip=True) if title_tag else "Unknown"
                    link = CAR_BASE_URL + link_tag["href"] if link_tag else "Unknown"
                    image_url = image_tag["src"] if image_tag else "Unknown"

                    details = scrape_car_details(link)
                    results.append({
                        "title": title,
                        "price": price,
                        "link": link,
                        "image_url": image_url,
                        **details
                    })
        except Exception as e:
            print(f"Error parsing article: {e}")
            continue

    return results

def scrape_pages_in_range(page_range):
    results = []
    for page in page_range:
        print(f"Scraping page {page}...")
        results.extend(scrape_page(page))
    return results

if __name__ == "__main__":
    # Divide pages into ranges for each thread
    page_ranges = [range(i, MAX_PAGE + 1, THREAD_COUNT) for i in range(1, THREAD_COUNT + 1)]

    all_results = []
    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        # Execute threads
        futures = [executor.submit(scrape_pages_in_range, page_range) for page_range in page_ranges]
        for future in futures:
            all_results.extend(future.result())

    # Save the results to a JSON file
    if all_results:
        with open("detailed_cars.json", "w", encoding="utf-8") as file:
            json.dump(all_results, file, ensure_ascii=False, indent=4)

        print(f"Detailed data saved to 'detailed_cars.json'.")
        print(f"Total data scraped: {len(all_results)}")
    else:
        print("No data was scraped.")
