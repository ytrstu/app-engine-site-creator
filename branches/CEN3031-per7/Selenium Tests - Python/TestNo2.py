from selenium import selenium
import unittest, time, re

class TestNo2(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://change-this-to-the-site-you-are-testing/")
        self.selenium.start()
    
    def test_no2(self):
        sel = self.selenium
        sel.open("/")
        sel.click("link=Sign in")
        sel.wait_for_page_to_load("30000")
        sel.type("email", "testToFail")
        sel.click("submit-login")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Sign out")
        sel.wait_for_page_to_load("30000")
    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
