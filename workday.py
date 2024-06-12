import json
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import argparse
import sys


def read_file(file):
    company_urls = {}
    with open(f"configs/{file}", "r") as inputfile:
        for line in inputfile:
            name, url = line.strip().split(",")
            company_urls[name] = url
    return company_urls


def parse_args():
    parser = argparse.ArgumentParser(description="Available Options")
    parser.add_argument("-f", "--file", dest="file", type=str, required=True)
    parser.add_argument("-p", "--perpetual", dest="perpetual", action="store_true")
    parser.add_argument(
        "-t",
        "--time-period",
        dest="time-period",
        type=int,
        default=1,
        required="--perpetual" in sys.argv,
    )
    parser.add_argument("-i", "--initial", dest="initial", action="store_true")
    args = vars(parser.parse_args())
    return args


def get_driver():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver


def generate_rss(jobs):
    rss = """\
<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">

<channel>
<title>Workday Scraper - RSS Feed</title>
<link>https://github.com/christopherlam888/workday-scraper</link>
<description>An RSS feed for new Workday postings.</description>
"""

    for job_info in jobs:
        job_posting_text = job_info["job_posting_text"].replace("\n", "<br>")
        rss += """\
<item>
    <title><![CDATA[{}]]></title>
    <link><![CDATA[{}]]></link>
    <description><![CDATA[{}]]></description>
</item>
""".format(
            f"{job_info['company']}: {job_info['job_title']}",
            f"{job_info['job_href']}",
            f"{job_posting_text}",
        )

    rss += "\n</channel>\n</rss>"
    return rss


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
                    job_title_element = job_element.find_element(By.XPATH, ".//h3/a")
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

        print(len(jobstosend))

        for jobtosend in jobstosend:
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
            job_info = {
                "company": company,
                "company_url": seturl,
                "job_title": job_title,
                "job_href": job_href,
                "job_posting_text": job_posting_text,
            }
            jobs.append(job_info)

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

    if not perpetual:
        break
    else:
        print(f"Waiting for {period} hours before running again...")
        time.sleep(600 * period)
