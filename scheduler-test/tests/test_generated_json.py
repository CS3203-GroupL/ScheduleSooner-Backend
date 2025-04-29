import os
import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # tests/
BASE_DIR = os.path.dirname(CURRENT_DIR)  # project root
OUTPUTS_DIR = os.path.join(BASE_DIR, 'outputs')

class TestGeneratedJSON(unittest.TestCase):
    def test_final_schedule_exists(self):
        filepath = os.path.join(OUTPUTS_DIR, 'final_schedule.json')
        self.assertTrue(os.path.exists(filepath), "final_schedule.json not found in outputs/!")

    def test_all_unique_courses_exists(self):
        filepath = os.path.join(OUTPUTS_DIR, 'all_unique_courses.json')
        self.assertTrue(os.path.exists(filepath), "all_unique_courses.json not found in outputs/!")

if __name__ == '__main__':
    unittest.main()
