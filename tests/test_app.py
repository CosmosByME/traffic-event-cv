import unittest
from streamlit.testing.v1 import AppTest

class AppSmokeTest(unittest.TestCase):
    def test_initial_render_and_bad_configuration(self):
        app = AppTest.from_file('app.py', default_timeout=20).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.title[0].value, 'RoadLens')
        app.text_area[0].set_value('{ invalid json').run()
        self.assertEqual(len(app.exception), 0)
        self.assertGreater(len(app.error), 0)

if __name__ == '__main__': unittest.main()
