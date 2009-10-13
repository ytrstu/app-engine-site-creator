from selenium import selenium
import unittest, time, re

class TestNo7(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://localhost:8080/")
        self.selenium.start()
    
    def test_no7(self):
        sel = self.selenium
        sel.open("/")
        sel.click("link=Sign in")
        sel.wait_for_page_to_load("30000")
        sel.click("admin")
        sel.click("submit-login")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Edit site")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Help")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Sitemap")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Recently modified")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Create page")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Edit sidebar")
        sel.wait_for_page_to_load("30000")
        sel.click("link=List users")
        sel.wait_for_page_to_load("30000")
        sel.click("link=List groups")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Find user")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Bulk edit users")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Sign out")
    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
