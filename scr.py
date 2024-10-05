from pandas.core import series
from selenium import webdriver
from selenium.webdriver.chromium import service
from selenium.webdriver.common.by import By
import time, uuid
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains

import time
import re
import os
import json
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# import html_extraction
import string
import random
from html_extraction import extract_job_details
# Path to save progress
PROGRESS_FILE = "crawling_progress.json"


def save_progress(processed_jobs, last_position):
  """
    Save the current progress (processed jobs and last scroll position).
    """
  progress_data = {
      "processed_jobs": list(processed_jobs),
      "last_position": last_position
  }
  with open(PROGRESS_FILE, 'w') as file:
    json.dump(progress_data, file)
  # print("Progress saved.")


def load_progress():
  """
    Load the saved progress from file, if it exists.
    """
  if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, 'r') as file:
      progress_data = json.load(file)
    print("Progress loaded.")
    return set(progress_data["processed_jobs"]), progress_data["last_position"]
  else:
    return set(), 0  # Return empty set if no progress file exists


def click_until_invisible(driver, button_locator):
  """
    Clicks a button multiple times until it is no longer visible on the page.
    """
  max_clicks = 25
  wait_time = 3
  clicks = 0
  while clicks < max_clicks:
    try:
      # Scroll to make sure the button is in view
      driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

      # Locate the button
      button = driver.find_element(*button_locator)

      # Ensure the button is visible
      if button.is_displayed() and button.is_enabled():
        # Use JavaScript to ensure the button is clickable
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        time.sleep(1)

        # Click the button
        if random.choice([True, False, False, False]):
          driver.execute_script("arguments[0].click();", button)
        else:
          actions = ActionChains(driver)
          actions.move_to_element(button).click().perform()
          print('action_chain clicked')
        clicks += 1
        print(f"Clicked 'See more jobs' button {clicks} times.")

        # Wait for content to load
        time.sleep(wait_time)
      else:
        print(f"Button not visible or clickable after {clicks} clicks.")
        break
    except Exception as e:
      print(f"Error clicking the button after {clicks} clicks: {e}")
      break
  else:
    print(
        f"Reached maximum clicks ({max_clicks}) without the button disappearing."
    )


def scroll_down(driver):
  """
    Scroll the page.
    """
  last_height = driver.execute_script("return document.body.scrollHeight")
  while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
      driver.execute_script("window.scrollBy(0, -50);")
      time.sleep(.7)
      driver.execute_script("window.scrollBy(0, 500);")
      time.sleep(.7)
      driver.execute_script("window.scrollBy(0, -50);")
      time.sleep(.7)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
      break
    last_height = new_height


def process_job(driver, processed_jobs):
  """
    Process each job and save details.
    """
  jobs = driver.find_elements(By.XPATH,
                              '//ul[@class="jobs-search__results-list"]/li')
  print(f"Found {len(jobs)} jobs.")

  for job in jobs:
    job_id = str(uuid.uuid4())
    try:
      soup = BeautifulSoup(job.get_attribute('outerHTML'), 'html.parser')
      job_url = soup.find('a', class_='base-card__full-link')['href']
      job_id = job_url.split('?')[0]
    except:
      pass
    if job_id in processed_jobs:
      print('skipping')
      continue
    job.click()
    time.sleep(5)

    # Extract job details (pseudo-code for job extraction)
    section = driver.find_element(By.CLASS_NAME,
                                  'two-pane-serp-page__detail-view')
    section_html = section.get_attribute('outerHTML')

    # Save the job details
    df = extract_job_details(section_html)
    output_file = 'Linkedin_crawling_output.csv'
    if os.path.exists(output_file):
      df.to_csv(output_file, mode='a', index=False, header=False)
    else:
      df.to_csv(output_file, mode='w', index=False, header=True)

    processed_jobs.add(job_id)  # Mark job as processed

    # Save progress after each job
    save_progress(processed_jobs,
                  driver.execute_script("return window.pageYOffset;"))


def scroll_and_load(driver):
  try:
    # Load saved progress (processed jobs and scroll position)
    processed_jobs, last_position = load_progress()

    # Scroll to last position
    driver.execute_script(f"window.scrollTo(0, {last_position});")
    time.sleep(2)

    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
      process_job(driver, processed_jobs)

      # Scroll down and wait for content to load
      scroll_down(driver)

      # Click "See more jobs" if available
      try:
        load_more_button = (By.XPATH, '//button[@aria-label="See more jobs"]')
        click_until_invisible(driver, load_more_button)
        time.sleep(2.5)
      except Exception as e:
        print("No more 'See more jobs' buttons or an error occurred:", e)
        # break

      # Check if new content was loaded
      new_height = driver.execute_script("return document.body.scrollHeight")
      if new_height == last_height:
        print("No more content loaded automatically.")
        break
      last_height = new_height

  except Exception as e:
    print(f"An error occurred: {e}")
  finally:
    # Ensure final saving of progress before quitting
    process_job(driver, processed_jobs)
    processed_jobs, last_position = load_progress()
    save_progress(processed_jobs,
                  driver.execute_script("return window.pageYOffset;"))


# ChromeDriver path
def get_driver():
  chromedriver_path = '/home/runner/.cache/selenium/chromedriver/linux64/129.0.6668.89/chromedriver'
  s = Service(chromedriver_path)
  options = Options()
  options.add_argument('--headless')
  options.add_argument('--no-sandbox')
  options.add_argument('--disable-dev-shm-usage')
  driver = webdriver.Chrome(service=s, options=options)
  return driver


driver = get_driver()

for url in [
    'https://in.linkedin.com/jobs/search?geoId=102713980&f_TPR=r86000&keywords=&f_E=5&f_WT=1&f_PP=105282602'
]:
  while True:
    keyword = 'linkedin.com/jobs/search'
    driver.get(url)
    time.sleep(4.23)  # Wait for page to load

    current_url = driver.current_url  # Get the current URL

    if keyword in current_url:
      print("Keywords found in URL! Proceeding with the script...")
      try:
        time.sleep(3)
        driver.execute_script("document.elementFromPoint(0, 0).click();")
        print('action_chain clicked')
        # Scroll the button into view
        print(
            '########################################################################################'
        )
        print(
            '########################################################################################'
        )
        print("Popup closed successfully.")
      except Exception as e:
        print(f"Error closing popup: {e}")
      break
  scroll_and_load(driver)
driver.quit()
