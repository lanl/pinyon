import unittest

from pyramid import testing


class TutorialViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

        
class TutorialFunctionalTests(unittest.TestCase):
    def setUp(self):
        from pinyon.web import main
        app = main({})
        from webtest import TestApp

        self.testapp = TestApp(app)

    def test_home_page(self):
        res = self.testapp.get('/', status=200)
        self.assertIn(b'<h1>Welcome', res.body)
