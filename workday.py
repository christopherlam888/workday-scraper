# import csv
import json
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import uuid

# Load or initialize job_ids_dict from file
try:
    with open('job_ids_dict.pkl', 'rb') as f:
        job_ids_dict = pickle.load(f)
except FileNotFoundError:
    job_ids_dict = {}

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

wait = WebDriverWait(driver, 10)

company_urls = [
    # 'https://mastercard.wd1.myworkdayjobs.com/en-US/CorporateCareers',
    # 'https://intel.wd1.myworkdayjobs.com/en-US/External',
    # 'https://trimble.wd1.myworkdayjobs.com/en-US/TrimbleCareers/',
    # 'https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite',
    # 'https://cvshealth.wd1.myworkdayjobs.com/CVS_Health_Careers',
    # 'https://motorolasolutions.wd5.myworkdayjobs.com/en-US/Careers/',
    # 'https://bah.wd1.myworkdayjobs.com/en-US/BAH_Jobs',
    'https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite?workerSubType=0c40f6bd1d8f10adf6dae42e46d44a17&workerSubType=ab40a98049581037a3ada55b087049b7&locationHierarchy1=2fcb99c455831013ea52fb338f2932d8',
]  # Add your company URLs here

for company_url in company_urls:
    if company_url not in job_ids_dict:
        job_ids_dict[company_url] = []

while True:
    jobs = []
    for company_url in company_urls:
        jobstosend = []
        driver.get(company_url)
        seturl = company_url
        try:
            today = True
            while today:
                time.sleep(2)
                wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//li[@class="css-1q2dra3"]')))

                job_elements = driver.find_elements(
                    By.XPATH, '//li[@class="css-1q2dra3"]')

                for job_element in job_elements:
                    job_title_element = job_element.find_element(
                        By.XPATH, './/h3/a')
                    job_id_element = job_element.find_element(
                        By.XPATH, './/ul[@data-automation-id="subtitle"]/li')
                    job_id = job_id_element.text
                    posted_on_element = job_element.find_element(
                        By.XPATH, './/dd[@class="css-129m7dg"][preceding-sibling::dt[contains(text(),"posted on")]]')
                    posted_on = posted_on_element.text
                    if 'posted today' in posted_on.lower() or True:
                        job_href = job_title_element.get_attribute('href')
                        job_title = job_title_element.text
                        if job_id not in job_ids_dict[company_url]:
                            job_ids_dict[company_url].append(job_id)
                            jobstosend.append((job_title, job_href))
                        else:
                            print(f"Job ID {job_id} already in job_ids_dict")
                    else:
                        today = False
                try:
                    next_button = driver.find_element(
                        By.XPATH, '//button[@data-uxi-element-id="next"]')
                    if "disabled" in next_button.get_attribute("class"):
                        break  # exit loop if the "next" button is disabled
                    next_button.click()
                except:
                    break

        except Exception as e:
            print(
                f"An error occurred while processing {company_url}: {str(e)}")
            continue

        print(len(job_ids_dict[company_urls[0]]))
        print(len(jobstosend))

        for job_title, job_href in jobstosend:
            driver.get(job_href)
            time.sleep(1)
            job_posting_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, '//div[@data-automation-id="job-posting-details"]')))
            job_posting_text = job_posting_element.text
            redis_id = str(uuid.uuid4())
            job_info = {'company_url': seturl, 'job_title': job_title,
                        'job_href': job_href, 'job_posting_text': job_posting_text}
            jobs.append(job_info)
            # jobs.append((seturl, job_title, job_href, job_posting_text))

    print("Done scraping")

    # Write job postings to a JSON file
    jsondata = json.dumps(jobs, indent=4)
    with open('job_postings.json', 'w') as jsonfile:
        jsonfile.write(jsondata)

    # # Write job postings to a CSV file
    # with open('job_postings.csv', 'w', newline='', encoding='utf-8') as csvfile:
    #     writer = csv.writer(csvfile)
    #     writer.writerow(['companyurl','Job Title', 'Job Href', 'Job Posting'])
    #     for job in jobs:
    #         writer.writerow(job)

    # Save job_ids_dict to file
        with open('job_ids_dict.pkl', 'wb') as f:
            pickle.dump(job_ids_dict, f)

    print("Files written")

    # Wait for a certain period before running again
    time.sleep(600)  # Run every hour
