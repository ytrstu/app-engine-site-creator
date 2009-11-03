from selenium import selenium
import unittest, time, re

class TestNo60(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://change-this-to-the-site-you-are-testing/")
        self.selenium.start()
    
    def test_no60(self):
        sel = self.selenium
        sel.open("/")
        sel.click("link=Sign in")
        sel.wait_for_page_to_load("30000")
        sel.click("admin")
        sel.click("submit-login")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Edit site")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Create page")
        sel.wait_for_page_to_load("30000")
        sel.type("id_title", "Test Page")
        sel.type("id_name", "Test")
        sel.type("id_title", "TestPage")
        sel.type("id_name", "TestPage")
        sel.click("dijit_form_Button_0")
        sel.wait_for_page_to_load("30000")
        sel.click("msgChangesSaved")
        sel.click("link=Main site")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Sign out")
        sel.wait_for_page_to_load("30000")
    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
