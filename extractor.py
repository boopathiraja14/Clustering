from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select
import time
import pandas as pd

BOM_CLIMATE_DATA = 'http://www.bom.gov.au/climate/data/'
SLEEP_SECS = 3


class HTMLExtractor:

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(BOM_CLIMATE_DATA)
        self.rain_fall_df = pd.DataFrame()
        self.max_temp_df = pd.DataFrame()
        self.min_temp_df = pd.DataFrame()


    def _pass_location(self, location):
        loc = self.driver.find_element_by_id('p_locSearch')
        loc.clear()
        loc.send_keys(location)
        self.driver.find_element_by_id('text').click()
        time.sleep(SLEEP_SECS)
        Select(self.driver.find_element_by_id('matchList')).select_by_index(0)
        time.sleep(SLEEP_SECS)
        Select(self.driver.find_element_by_id('nearest10')).select_by_index(0)
        time.sleep(SLEEP_SECS)


    def _collect_data(self):
        out_df = pd.DataFrame()
        self.driver.find_element_by_id('getData').click()
        self.driver.switch_to.window(self.driver.window_handles[-1])
        table = self.driver.find_element_by_xpath('//table[@id="dataTable"]')

        table = BeautifulSoup(table.get_attribute('innerHTML'), 'lxml')

        for table_row in table.findAll('tr'):
            columns = table_row.findAll('td')
            output_row = []
            for column in columns:
                if column.text is not None:
                    output_row.append(column.text)
            # print(output_row)
            out_df = out_df.append([output_row])
        return out_df


    def get_rainfall_data(self, year, location):
        rain_fall = self.driver.find_element_by_id('ncc_obs_code_group')
        Select(rain_fall).select_by_value('2')
        self.driver.find_element_by_id('dt1').click()

        self._pass_location(location)

        year_index = 0 if (year == 2019) else 1
        Select(self.driver.find_element_by_id('year_select')).select_by_index(year_index)

        self.rain_fall_df = self._collect_data()

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])


    def get_temperature_data(self, year, location):
        max_temp = self.driver.find_element_by_id('ncc_obs_code_group')
        Select(max_temp).select_by_value('3')
        Select(self.driver.find_element_by_id('elementSubSelect')).select_by_value('122')
        self.driver.find_element_by_id('dt1').click()

        self._pass_location(location)
        year_index = 0 if (year == 2019) else 1
        Select(self.driver.find_element_by_id('year_select')).select_by_index(year_index)

        self.max_temp_df = self._collect_data()

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

        min_temp = self.driver.find_element_by_id('ncc_obs_code_group')
        Select(min_temp).select_by_value('3')
        Select(self.driver.find_element_by_id('elementSubSelect')).select_by_value('123')
        self.driver.find_element_by_id('dt1').click()

        self._pass_location(location)
        Select(self.driver.find_element_by_id('year_select')).select_by_index(year_index)

        self.min_temp_df = self._collect_data()

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])


    def get_rain_temp_data(self, year, location):
        self.get_rainfall_data(year, location)
        self.get_temperature_data(year, location)
        self.driver.quit()



###### main

ex = HTMLExtractor()
# (ex.get_rainfall_data(2018, 'hawker'))
# ex.get_temperature_data(2018, 'hawker')
ex.get_rain_temp_data(2018, 'hawker')
print(ex.rain_fall_df.head())
print(ex.min_temp_df.head())
print(ex.max_temp_df.head())