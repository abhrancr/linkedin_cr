from bs4 import BeautifulSoup
import pandas as pd
import re


def extract_job_details(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extracting title
    title = soup.find(
        'h2', class_='top-card-layout__title').text.strip() if soup.find(
            'h2', class_='top-card-layout__title') else None

    # Extracting company name
    company_name = soup.find(
        'a', class_='topcard__org-name-link').text.strip() if soup.find(
            'a', class_='topcard__org-name-link') else None

    # Extracting location
    location = soup.find(
        'span', class_='topcard__flavor--bullet').text.strip() if soup.find(
            'span', class_='topcard__flavor--bullet') else None

    # Extracting posting time
    posting_time = soup.find(
        'span', class_='posted-time-ago__text').text.strip() if soup.find(
            'span', class_='posted-time-ago__text') else None

    # Extracting number of applicants
    applicants = soup.find(
        'figcaption',
        class_='num-applicants__caption').text.strip() if soup.find(
            'figcaption', class_='num-applicants__caption') else None

    # Extracting apply URL
    # apply_url = soup.find('code', id='applyUrl').text if soup.find('code', id='applyUrl') else None
    apply_url_tag = soup.find('code', id='applyUrl')
    apply_url = None
    if apply_url_tag:
        match = re.search(r'"(https?://.*?)"', apply_url_tag.decode_contents())
        if match:
            apply_url = match.group(1)

    # Extracting company URL
    company_url = soup.find(
        'a', class_='topcard__org-name-link')['href'] if soup.find(
            'a', class_='topcard__org-name-link') else None

    # Extracting job URL
    job_url = soup.find('a', class_='topcard__link')['href'] if soup.find(
        'a', class_='topcard__link') else None

    seniority_level = None
    employment_type = None
    job_function = None
    industries = None

    criteria_list = soup.find_all('li',
                                  class_='description__job-criteria-item')
    for item in criteria_list:
        header = item.find(
            'h3', class_='description__job-criteria-subheader').text.strip()
        value = item.find(
            'span',
            class_='description__job-criteria-text--criteria').text.strip()

        if header == "Seniority level":
            seniority_level = value
        if header == "Employment type":
            employment_type = value
        if header == "Job function":
            job_function = value
        if header == "Industries":
            industries = value

    # Extracting the description text
    description_details = {}
    description_section = soup.find('div',
                                    class_='show-more-less-html__markup')
    if description_section:
        current_header = None
        for element in description_section.children:
            if element.name == 'strong':
                current_header = element.get_text(strip=True).rstrip(':')
                description_details[current_header] = []
            elif element.name == 'ul':
                if current_header:
                    description_details[current_header].extend([
                        li.get_text(strip=True)
                        for li in element.find_all('li')
                    ])
            elif element.name == 'br':
                continue
            else:
                if current_header and element.name is None:
                    description_details[current_header].append(element.strip())

    # Creating a dictionary for the data
    job_data = {
        'Title': title,
        'Company Name': company_name,
        'Location': location,
        'Posting Time': posting_time,
        'Applicants': applicants,
        'Seniority Level':
        seniority_level,  # Placeholder, add extraction if possible
        'Job Function':
        job_function,  # Placeholder, add extraction if possible
        'Employment Type':
        employment_type,  # Placeholder, add extraction if possible
        'Industry': industries,  # Placeholder, add extraction if possible
        'Apply URL': apply_url,
        'Company URL': company_url,
        'Job URL': job_url,
        'Description': description_details
    }

    # Creating a pandas DataFrame
    df = pd.DataFrame([job_data])

    return df
