import json
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

import multiprocessing.dummy as multiprocessing
import tqdm

from .parse_args import parse_args
from .rss_funcs import generate_rss
from .email_funcs import compose_email, send_email


def read_file(file):
    company_urls = {}
    with open(f"configs/{file}", "r") as inputfile:
        for line in inputfile:
            name, url = line.strip().split(",")
            company_urls[name] = url
    return company_urls


def get_driver():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver


def scrape_job_posting(jobtosend, company, seturl):
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, 10)
        job_title = jobtosend[0]
        job_href = jobtosend[1]
        driver.get(job_href)
        time.sleep(1)
        job_posting_element = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@data-automation-id="job-posting-details"]')
            )
        )
        job_posting_text = job_posting_element.text
        driver.close()
        job_info = {
            "company": company,
            "company_url": seturl,
            "job_title": job_title,
            "job_href": job_href,
            "job_posting_text": job_posting_text,
        }
        return job_info
    except:
        print("Failed! Retrying...")
        return scrape_job_posting(jobtosend, company, seturl)


def main():
    args = parse_args()
    file = args["file"]
    perpetual = args["perpetual"]
    period = args["time-period"]
    initial = args["initial"]

    # Load or initialize job_ids_dict from file
    try:
        with open("job_ids_dict.pkl", "rb") as f:
            job_ids_dict = pickle.load(f)
    except FileNotFoundError:
        job_ids_dict = {}

    company_urls = read_file(file)

    for company in company_urls:
        if company_urls[company] not in job_ids_dict:
            job_ids_dict[company_urls[company]] = []

    driver = get_driver()
    wait = WebDriverWait(driver, 10)

    while True:
        jobs = []
        for company in company_urls:
            print(f"Scraping {company}...")
            company_url = company_urls[company]
            jobstosend = []
            driver.get(company_url)
            seturl = company_url
            try:
                today = True
                while today or initial:
                    time.sleep(2)
                    wait.until(
                        EC.presence_of_element_located(
                            (By.XPATH, '//li[@class="css-1q2dra3"]')
                        )
                    )

                    job_elements = driver.find_elements(
                        By.XPATH, '//li[@class="css-1q2dra3"]'
                    )

                    for job_element in job_elements:
                        job_title_element = job_element.find_element(
                            By.XPATH, ".//h3/a"
                        )
                        job_id_element = job_element.find_element(
                            By.XPATH, './/ul[@data-automation-id="subtitle"]/li'
                        )
                        job_id = job_id_element.text
                        posted_on_element = job_element.find_element(
                            By.XPATH,
                            './/dd[@class="css-129m7dg"][preceding-sibling::dt[contains(text(),"posted on")]]',
                        )
                        posted_on = posted_on_element.text
                        if "posted today" in posted_on.lower() or initial:
                            job_href = job_title_element.get_attribute("href")
                            job_title = job_title_element.text
                            if job_id not in job_ids_dict[company_url]:
                                job_ids_dict[company_url].append(job_id)
                                jobstosend.append((job_title, job_href))
                            else:
                                print(f"Job ID {job_id} already in job_ids_dict.")
                        else:
                            today = False
                    try:
                        next_button = driver.find_element(
                            By.XPATH, '//button[@data-uxi-element-id="next"]'
                        )
                        if "disabled" in next_button.get_attribute("class"):
                            break  # exit loop if the "next" button is disabled
                        next_button.click()
                    except:
                        break

            except Exception as e:
                print(f"An error occurred while processing {company_url}: {str(e)}")
                continue

            print(f"Found {len(jobstosend)} jobs for {company}.")

            # for job_info in jobstosend:
            #     job_info = scrape_job_posting(job_info, company, seturl)
            #     jobs.append(job_info)

            with multiprocessing.Pool() as pool, tqdm.tqdm(
                total=len(jobstosend)
            ) as pbar:
                params = [(jobtosend, company, seturl) for jobtosend in jobstosend]
                for job_info in pool.starmap(scrape_job_posting, params):
                    jobs.append(job_info)
                    pbar.update()

        print("Done scraping.")

        # Write job postings to a JSON file
        jsondata = json.dumps(jobs, indent=4)
        with open("job_postings.json", "w") as jsonfile:
            jsonfile.write(jsondata)

        # Write job postings to an RSS file
        with open("rss.xml", "w") as rssfile:
            rssfile.write(generate_rss(jobs))

        # Save job_ids_dict to file
        with open("job_ids_dict.pkl", "wb") as f:
            pickle.dump(job_ids_dict, f)

        print("Files written.")

        # Send an email if option given
        sender = args["email"]
        if sender and len(jobs) > 0:
            subject = "Workday Scraper: Today's Jobs"
            body = compose_email(jobs)
            recipients = args["recipients"].split(",")
            password = args["password"]
            send_email(subject, body, sender, recipients, password)
            print("Email sent.")

        if not perpetual:
            break
        else:
            print(f"Waiting for {period} hours before running again...")
            time.sleep(600 * period)


if __name__ == "__main__":
    main()
