from selenium import selenium
import unittest, time, re

class TestNo50(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://change-this-to-the-site-you-are-testing/")
        self.selenium.start()
    
    def test_no50(self):
        sel = self.selenium
        sel.click("link=Sign in")
        sel.wait_for_page_to_load("30000")
        sel.click("submit-login")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Edit site")
        sel.wait_for_page_to_load("30000")
        sel.context_menu("//div[@id='dijit__TreeNode_0']/div[1]")
        sel.click("dijit_MenuItem_3_text")
        sel.click("dijit_form_Button_1")
        sel.click("link=Sign out")
        sel.wait_for_page_to_load("30000")
    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
