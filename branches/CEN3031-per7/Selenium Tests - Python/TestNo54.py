from selenium import selenium
import unittest, time, re

class TestNo54Evo0(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://change-this-to-the-site-you-are-testing/")
        self.selenium.start()
    
    def test_no54_evo0(self):
        sel = self.selenium
        sel.open("/")
        sel.click("link=Sign in")
        sel.wait_for_page_to_load("30000")
        sel.click("admin")
        sel.click("submit-login")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Edit site")
        sel.wait_for_page_to_load("30000")
        sel.click("link=List groups")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Create a new group")
        sel.wait_for_page_to_load("30000")
        sel.type("id_name", "C")
        sel.type("id_description", "To Be Deleted")
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        sel.click("//div[@id='content']/ul/li[3]/a")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Delete Group")
        sel.wait_for_page_to_load("30000")
    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
