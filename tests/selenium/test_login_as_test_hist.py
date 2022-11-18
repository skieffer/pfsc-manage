# --------------------------------------------------------------------------- #
#   Proofscape Manage                                                         #
#                                                                             #
#   Copyright (c) 2021-2022 Proofscape contributors                           #
#                                                                             #
#   Licensed under the Apache License, Version 2.0 (the "License");           #
#   you may not use this file except in compliance with the License.          #
#   You may obtain a copy of the License at                                   #
#                                                                             #
#       http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                             #
#   Unless required by applicable law or agreed to in writing, software       #
#   distributed under the License is distributed on an "AS IS" BASIS,         #
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#   See the License for the specific language governing permissions and       #
#   limitations under the License.                                            #
# --------------------------------------------------------------------------- #

# Generated by Selenium IDE

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from tests.selenium.util import (
    make_driver, dismiss_cookie_notice, login_as_test_user,
)


class Test_Login_as_test_hist():
    def setup_method(self, method):
        self.driver = make_driver()
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_login_as_test_hist(self, pise_url):
        self.driver.get(pise_url)
        self.driver.set_window_size(1920, 1057)
        dismiss_cookie_notice(self.driver)
        login_as_test_user(self.driver, 'hist')
        # We're logged in if our username replaces the text on the user menu
        WebDriverWait(self.driver, 3).until(expected_conditions.text_to_be_present_in_element((By.ID, "dijit_PopupMenuBarItem_8_text"), "test.hist"))
        assert self.driver.find_element(By.ID, "dijit_PopupMenuBarItem_8_text").text == "test.hist"
