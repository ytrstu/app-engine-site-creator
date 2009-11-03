from selenium import selenium
import unittest, time, re

class TestNo63(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://change-this-to-the-site-you-are-testing/")
        self.selenium.start()
    
    def test_no63(self):
        sel = self.selenium
        sel.open("/")
        sel.click("link=Sign in")
        sel.wait_for_page_to_load("30000")
        sel.click("admin")
        sel.click("submit-login")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Edit site")
        sel.wait_for_page_to_load("30000")
        for i in range(60):
            try:
                if sel.is_element_present("//div[@id='dijit__TreeNode_1']/div[1]"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.context_menu("//div[@id='dijit__TreeNode_1']/div[1]")
        sel.click("dijit_MenuItem_1_text")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Add page to sidebar")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Sign out")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Sign in")
        sel.wait_for_page_to_load("30000")
        sel.click("admin")
        sel.click("submit-login")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Edit site")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Edit sidebar")
        sel.wait_for_page_to_load("30000")
        for i in range(60):
            try:
                if sel.is_element_present("yaml"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.type("yaml", "heading: ' '\npages:\n-{id: 18, title: AddChild}\n-{id: 25, title: TestPageCompleteFromTitle}")
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Sign out")
        sel.wait_for_page_to_load("30000")
    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
