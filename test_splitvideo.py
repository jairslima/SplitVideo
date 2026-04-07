import unittest

from splitvideo import build_segments, normalize_cut_points, parse_time_value


class SplitVideoTests(unittest.TestCase):
    def test_parse_mm_ss(self) -> None:
        self.assertEqual(parse_time_value("16:47"), 1007)

    def test_parse_hh_mm_ss(self) -> None:
        self.assertEqual(parse_time_value("01:02:03"), 3723)

    def test_parse_dot_minutes_seconds(self) -> None:
        self.assertEqual(parse_time_value("1.10"), 70)

    def test_normalize_mixed_cuts(self) -> None:
        cuts = normalize_cut_points(["50%", "16:47", "16:47"], 3000)
        self.assertEqual(cuts, [1007.0, 1500.0])

    def test_build_segments(self) -> None:
        segments = build_segments(__import__("pathlib").Path("video.mp4"), [10.0, 20.0], 30.0)
        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0].start_seconds, 0.0)
        self.assertEqual(segments[2].end_seconds, 30.0)


if __name__ == "__main__":
    unittest.main()
