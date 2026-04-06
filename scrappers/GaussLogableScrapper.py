import json
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import abc
import os
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

class GaussLoginScrapper(abc.ABC):
    """
    Gestiona el login y el ciclo de vida del driver.
    """

    def __init__(self, username, password, directory, suffix = "", debug_html= False, tab_delay=0.5, extractor_workers=1):
        self.__extractor_workers = extractor_workers
        self.__debug_html = debug_html
        self.__tab_delay = tab_delay
        self.__directory = directory
        if self.__directory[-1] != "/":
            self.__directory += "/"
        self.__suffix = suffix
        self.username = username
        self.password = password
        self.driver = None
        self.__logged = False
        self._login_url = "https://www.upm.es/gauss/login.upm"

    def is_loged_in(self):
        return self.__logged

    def login(self):
        try:
            # Navigate to the GAUSS login page
            driver = webdriver.Chrome()
            driver.get(self._login_url)
            # Wait for the page to load
            time.sleep(self.__tab_delay)  # 2

            # Locate the username and password fields
            username_field = driver.find_element(By.NAME, "username")
            password_field = driver.find_element(By.NAME, "upasswd")

            # Enter your credentials
            username_field.send_keys(self.username)  # Replace with your username
            password_field.send_keys(self.password)  # Replace with your password

            # Submit the login form
            login_button = driver.find_element(By.NAME, "form_login_enviar")
            login_button.click()



            # Check if login was successful by looking for a specific element
            if "Su sesión ha expirado" in driver.page_source:
                print("Login failed: Session expired.")
            else:
                # print("Login successful!")
                self.__logged = True
                self.driver = driver
                return driver
        except Exception as e:
            raise Exception(e)

    def close(self) -> None:
        if self.driver is not None:
            self.driver.quit()
            self.driver = None

    @abc.abstractmethod
    def get_file_name(self, row, extension=".json"):
        raise NotImplementedError("Child of this class must implement this method")

    @abc.abstractmethod
    def _build_list_uris(self, row):
        raise NotImplementedError("Child of this class must implement this method")

    @abc.abstractmethod
    def _invoke_extraction_function(self, extraction_function, html_content):
        raise NotImplementedError("Child of this class must implement this method")



    def _file_exists(self, row):
        print(">",row)
        file_name = self.__directory + self.get_file_name(row)
        return os.path.exists(file_name)

    def cache_html(self, html_content, row, section):
        if self.__debug_html:
            html_directory = self.__directory + self.get_file_name(row, extension="")
            os.makedirs(html_directory, exist_ok=True)
            debug_html_file = html_directory + "/" + self.get_file_name(row, extension= section+".html")
            with open(debug_html_file, "w+", encoding="utf-8") as f:
                f.write(html_content)

    def __save_results(self, row, merged, errors):
        file_name = self.__directory +self.get_file_name(row)
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=4)
        file_name = self.__directory +"/errors.csv"
        with open(file_name, "a", encoding="utf-8") as f:
            if str(errors) != "[]":
                json.dump(errors, f, ensure_ascii=False, indent=4)

    def new_tab_record_extraction(self, row):
        print("1")
        subject_code = str(row.subject_code)
        # DONE: cache, if file exists do not download it again
        if self._file_exists(row):
            return
        print("2")
        list_of_uris = self._build_list_uris(row)
        driver = self.login()
        merged = {'test': 'ok'}
        errors = []
        for section, elements in list_of_uris.items():

            uri = elements[0]
            extraction_function = elements[1]
            try:
                driver.get(uri)
                time.sleep(self.__tab_delay)
                html_content = driver.page_source

                self.cache_html(html_content, row, section)
                if extraction_function is not None:
                    result = self._invoke_extraction_function(extraction_function, html_content)
                    merged = {**result, **merged}

            except Exception as e:
                print(
                    "Exception occurred [section:" + section + "][" + subject_code + "][" + extraction_function + "]: ",
                    e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                errors.append(subject_code + " : " + str(e))

        self.__save_results(row, merged, errors)

    # Promote to abstract
    def extract_structured_json(self, local_index="../gauss-index.csv", years=None, study_plan_code=None, subject_code=None):
        if not local_index:
            print("Please first build the gauss index")
        else:
            df = pd.read_csv(local_index)
            if study_plan_code is not None:
                df = df.loc[df['study_plan_code'] == study_plan_code]
            if years is not None:
                df = df.loc[df['academic_year'] == years]
            if subject_code is not None:
                df = df.loc[df['subject_code'] == subject_code]
            with ThreadPoolExecutor(max_workers=self.__extractor_workers) as executor:
                executor.map(self.new_tab_record_extraction, df.itertuples(index=False))

if __name__ == "__main__":
    USERNAME = ""
    PASSWORD = ""
    scrapper = GaussLoginScrapper(USERNAME, PASSWORD)
    scrapper.login()