from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from functools import partial
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import quote
from dotenv import load_dotenv


load_dotenv()

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--remote-debugging-port=9222')
    return webdriver.Chrome(options=options)

def parse_review_count(text):
    text = text.lower().replace("reviews", "").strip()
    if "k" in text:
        return int(float(text.replace("k", "")) * 1000)
    return int("".join(filter(str.isdigit, text)))

def scroll_to_load_all_courses(driver, max_scrolls=30, scroll_pause_time=2):
    wait = WebDriverWait(driver, 10)
    action = ActionChains(driver)

    seen_elements = set()

    for i in range(max_scrolls):
        #print(f"Scroll {i+1} — Simulating scroll & hover...")

        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)

        # Detect all course containers
        course_containers = driver.find_elements(By.CSS_SELECTOR, "div.cds-ProductCard-content")
        current_count = len(course_containers)
        #print(f"🔍 Found {current_count} course containers.")

        if current_count > 0:
            last_card = course_containers[-1]
            try:
                action.move_to_element(last_card).perform()
            except Exception as e:
                print(f"Could not hover: {e}")

        # Use the memory id of each element to detect new ones
        new_elements = set(course_containers)
        if new_elements.issubset(seen_elements):
            print(f"Scrolling complete after {i+1} scrolls. No new cards.")
            break

        seen_elements.update(new_elements)

def scrape_coursera_courses(query, max_courses=50, min_rating=4.5, min_reviews=3000):
    driver = setup_driver()
    search_url = f"https://www.coursera.org/search?query={quote(query)}"
    driver.get(search_url)
    time.sleep(5)

    scroll_to_load_all_courses(driver)

    base_url = "https://www.coursera.org"
    course_containers = driver.find_elements(By.CSS_SELECTOR, "div.cds-ProductCard-content")
    print(f"🔍 Found {len(course_containers)} course containers.")
    results = []

    for container in course_containers:
        try:
            # Extract title and URL
            link = container.find_element(By.CSS_SELECTOR, "a[data-click-key='search.search.click.search_card']")
            title = link.text.strip()
            relative_url = link.get_attribute("href")
            full_url = relative_url if relative_url.startswith("http") else f"{base_url}{relative_url}"

            # Extract rating
            rating_elem = container.find_element(By.CSS_SELECTOR, "div[role='meter'] span")
            rating = float(rating_elem.text.strip())

            # Extract number of reviews
            review_elem = container.find_element(By.CSS_SELECTOR, "div.css-vac8rf")
            reviews = parse_review_count(review_elem.text)


            # Extract skills
            skills_block = container.find_elements(By.CSS_SELECTOR, "div.cds-ProductCard-body p.css-vac8rf")
            skills = []
            for p in skills_block:
                if "Skills you'll gain:" in p.text:
                    skills_text = p.text.split("Skills you'll gain:")[-1].strip()
                    skills = [s.strip() for s in skills_text.split(',') if s.strip()]
                    break

            results.append({
                "title": title,
                "url": full_url,
                "rating": rating,
                "reviews": reviews,
                "skills": skills
            })

            if len(results) >= max_courses:
                break

        except Exception as e:
            print(f"Error while parsing course: {e}")
            continue

    driver.quit()
    return results