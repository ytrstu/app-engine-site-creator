from selenium import selenium
import unittest, time, re

class TestNo31(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://change-this-to-the-site-you-are-testing/")
        self.selenium.start()
    
    def test_no31(self):
        sel = self.selenium
        sel.click("link=Sign in")
        sel.wait_for_page_to_load("30000")
        sel.click("submit-login")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Edit page")
        sel.wait_for_page_to_load("30000")
        sel.click("//td[@id='xToolbar']/table[4]/tbody/tr/td[2]/div/img")
        sel.click("//td[@id='xToolbar']/table[4]/tbody/tr/td[2]/div/img")
        sel.click("link=Sign out")
        sel.wait_for_page_to_load("30000")
    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
