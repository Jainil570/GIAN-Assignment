"""Capture screenshots of the running Streamlit app (streamlit run app.py) for the submission.

    python examples/capture_screenshots.py       (needs Microsoft Edge; Selenium Manager fetches the driver)
"""
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
QUESTIONS = [
    ("01_multi_source_answer", "Who developed a method to grow trees with just one litre of water, and how does it work?"),
    ("02_hindi_source_conflicting_values", "How heavy is the Noorjahan mango and who promoted it?"),
    ("03_hindi_question", "नूरजहां आम का वजन कितना होता है और इसे किसने संरक्षित किया?"),
    ("04_name_variants", "Who developed the thornless Khejri, and is the innovator's name written the same way in both parts of the article?"),
    ("05_cross_source_organisations", "Which organisations are associated with both the 51st and the 53rd Shodhyatra in these sources?"),
    ("06_identity_not_established", "Is Dharamveer Khambojji from the 51st Shodhyatra the same person as Shri Dharmveer who built the mahua machine?"),
    ("07_gian_nidhi_listing", "Are there GIAN Nidhi student projects about helmets? List them with their institutions."),
    ("08_refusal_missing_year", "In which year did Himmat Ram Bhambhu receive the Padma Shri?"),
    ("09_refusal_out_of_scope", "Who won the Cricket World Cup in 2011?"),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    opts = webdriver.EdgeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1500,2400")
    drv = webdriver.Edge(options=opts)
    try:
        for name, q in QUESTIONS:
            drv.get("http://localhost:8501")
            box = WebDriverWait(drv, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='Question']")))
            box.send_keys(q)
            box.send_keys(Keys.ENTER)
            WebDriverWait(drv, 240).until(
                lambda d: any("Relevant Information" in e.text for e in d.find_elements(By.TAG_NAME, "h3")))
            time.sleep(1.5)
            for exp in drv.find_elements(By.CSS_SELECTOR, "details summary")[:1]:   # open the retrieval trace
                exp.click()
            time.sleep(1)
            drv.save_screenshot(str(OUT / f"{name}.png"))
            print("saved", name)
    finally:
        drv.quit()


if __name__ == "__main__":
    main()
