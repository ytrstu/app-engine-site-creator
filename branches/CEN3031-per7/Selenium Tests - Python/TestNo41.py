from selenium import selenium
import unittest, time, re

class TestNo41Evo0(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://change-this-to-the-site-you-are-testing/")
        self.selenium.start()
    
    def test_no41_evo0(self):
        sel = self.selenium
        sel.open("/")
        sel.click("link=Sign in")
        sel.wait_for_page_to_load("30000")
        sel.click("admin")
        sel.click("submit-login")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Edit page")
        sel.wait_for_page_to_load("30000")
        sel.click("dijit_layout__TabButton_1")
        sel.type("attachment", "C:\\Users\\Jesu\\Pictures\\picture.jpg")
        sel.click("//input[@value='Upload']")
        sel.wait_for_page_to_load("30000")
        sel.click("link=View page")
        sel.wait_for_page_to_load("30000")
        sel.click("link=picture.jpg")
        sel.wait_for_page_to_load("30000")
    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
