from pathlib import Path
import unittest
import shutil

from splitvideo import (
    build_segments,
    normalize_cut_points,
    parse_time_value,
    resolve_output_dir,
    sanitize_basename,
)


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

    def test_build_segments_verbose(self) -> None:
        segments = build_segments(
            selected_video=Path("video.mp4"),
            output_dir=Path("."),
            cut_points=[10.0, 20.0],
            duration_seconds=30.0,
            name_mode="verbose",
        )
        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0].start_seconds, 0.0)
        self.assertEqual(segments[2].end_seconds, 30.0)
        self.assertIn("00-00-10", segments[0].output_path.name)

    def test_build_segments_short(self) -> None:
        segments = build_segments(
            selected_video=Path("Meu video ｜ teste.mp4"),
            output_dir=Path("."),
            cut_points=[10.0],
            duration_seconds=20.0,
            name_mode="short",
        )
        self.assertTrue(segments[0].output_path.name.startswith("Meu_video_teste_001"))

    def test_resolve_output_dir_default(self) -> None:
        selected_video = Path(r"C:\videos\teste.mp4")
        self.assertEqual(resolve_output_dir(selected_video, None), selected_video.parent.resolve())

    def test_resolve_output_dir_explicit(self) -> None:
        tmp = Path("tmp_test_output")
        tmp.mkdir(exist_ok=True)
        try:
            result = resolve_output_dir(Path("video.mp4"), str(tmp))
            self.assertEqual(result, tmp.resolve())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_sanitize_basename(self) -> None:
        self.assertEqual(sanitize_basename("a ｜ b ✝ c"), "a_b_c")


if __name__ == "__main__":
    unittest.main()
