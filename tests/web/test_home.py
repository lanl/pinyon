import unittest

from pyramid import testing


class TutorialViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_home(self):
        from powerwall.web.home import home

        request = testing.DummyRequest()
        response = home(request)
        self.assertEqual('Home View', response['name'])

        
class TutorialFunctionalTests(unittest.TestCase):
    def setUp(self):
        from powerwall.web import main
        app = main({})
        from webtest import TestApp

        self.testapp = TestApp(app)

    def test_home_page(self):
        res = self.testapp.get('/', status=200)
        self.assertIn(b'Hi Home View', res.body)
