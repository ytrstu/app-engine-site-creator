from selenium import selenium
import unittest, time, re

class TestNo13(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://localhost:8080/")
        self.selenium.start()
    
    def test_no13(self):
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
        sel.type("id_title", "TestPageFillInText")
        sel.type("id_name", "TestPageFillInText")
        for i in range(60):
            try:
                if sel.is_element_present("//textarea[@name='editorHtml']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.type("//textarea[@name='editorHtml']", "Typing in this Editor Box! :P")
        sel.click("dijit_form_Button_0")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Main site")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Sign out")
        sel.wait_for_page_to_load("30000")
    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
