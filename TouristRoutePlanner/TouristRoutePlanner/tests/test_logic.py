import unittest
import pandas as pd
from recommendation import parse_visit_duration, recommend_places
from route_optimizer import optimize_route

class PlannerLogicTests(unittest.TestCase):
    def test_parse_visit_duration(self):
        self.assertEqual(parse_visit_duration("1.5 hours"), 90)
        self.assertEqual(parse_visit_duration("Full day"), 480)
        self.assertEqual(parse_visit_duration("30 minutes"), 30)

    def test_all_areas_returns_candidates(self):
        df = recommend_places("tourist_places_cbe.csv", "All Areas", [], 1000, 6, 3, 5)
        self.assertEqual(len(df), 5)
        self.assertIn("recommendation_score", df.columns)

    def test_optimizer_respects_budget_and_time(self):
        candidates = pd.DataFrame({
            "name": ["A", "B"],
            "visit_duration": ["1 hour", "1 hour"],
            "entry_fee": [100, 200],
            "recommendation_score": [90, 80],
        })
        # Matrix index 0 is the source, indexes 1 and 2 are the two places.
        matrix = [
            [0, 600, 600],
            [600, 0, 300],
            [600, 300, 0],
        ]
        result = optimize_route(candidates, matrix, 3, 2, 250)
        self.assertIsNotNone(result)
        self.assertLessEqual(result["total_fee"], 250)
        self.assertLessEqual(result["total_time_minutes"], 180)
        self.assertEqual(len(result["route"]), 1)

if __name__ == "__main__":
    unittest.main()
