"""ImageScannerのテスト."""

import pytest

from image_to_pdf.image_scanner import ImageScanner


class TestImageScanner:
    """ImageScannerクラスのテスト."""

    def test_group_by_single_pattern(self):
        """単一パターンでのグループ化テスト."""
        scanner = ImageScanner(
            grouping_pattern=r"^(?P<name>.+)-\d+\."
        )

        folder_path = "test_folder"
        image_paths = [
            "test_folder/Title1-1.png",
            "test_folder/Title1-2.png",
            "test_folder/Title2-1.png",
            "test_folder/Title2-2.png",
        ]

        result = scanner.group_images_by_pattern(folder_path, image_paths)

        assert len(result) == 2
        assert "Title1" in result
        assert "Title2" in result
        assert len(result["Title1"]) == 2
        assert len(result["Title2"]) == 2

    def test_group_by_multiple_patterns_priority(self):
        """複数パターンでの優先順位テスト."""
        scanner = ImageScanner(
            grouping_patterns=[
                r"^\d{4}-\d{2}-\d{2}-(?P<name>.+)-\d+\.",  # パターン1（優先度高）
                r"^(?P<name>.+)-\d+\.",  # パターン2（優先度低）
            ]
        )

        folder_path = "test_folder"
        image_paths = [
            "test_folder/2024-01-01-Title1-1.png",  # パターン1にマッチ
            "test_folder/2024-01-01-Title1-2.png",  # パターン1にマッチ
            "test_folder/Title2-1.png",  # パターン2にマッチ
            "test_folder/Title2-2.png",  # パターン2にマッチ
        ]

        result = scanner.group_images_by_pattern(folder_path, image_paths)

        assert len(result) == 2
        assert "Title1" in result
        assert "Title2" in result
        assert len(result["Title1"]) == 2
        assert len(result["Title2"]) == 2

    def test_group_by_multiple_patterns_first_match_wins(self):
        """複数パターンで最初にマッチしたパターンが優先されることをテスト."""
        scanner = ImageScanner(
            grouping_patterns=[
                r"^(?P<name>.+)-\d+\.",  # パターン1（より広い）
                r"^\d{4}-(?P<name>.+)-\d+\.",  # パターン2（より狭い）
            ]
        )

        folder_path = "test_folder"
        image_paths = [
            "test_folder/2024-Title1-1.png",  # 両方にマッチするが、パターン1が優先
        ]

        result = scanner.group_images_by_pattern(folder_path, image_paths)

        # パターン1で "2024-Title1" がマッチ
        assert "2024-Title1" in result
        assert len(result["2024-Title1"]) == 1

    def test_group_with_unmatched_images(self):
        """マッチしない画像がある場合のテスト."""
        scanner = ImageScanner(
            grouping_patterns=[
                r"^\d{4}-\d{2}-\d{2}-(?P<name>.+)-\d+\.",
            ]
        )

        folder_path = "test_folder"
        image_paths = [
            "test_folder/2024-01-01-Title1-1.png",  # マッチ
            "test_folder/2024-01-01-Title1-2.png",  # マッチ
            "test_folder/random_image.png",  # マッチしない
            "test_folder/another_image.png",  # マッチしない
        ]

        result = scanner.group_images_by_pattern(folder_path, image_paths)

        assert len(result) == 2
        assert "Title1" in result
        assert f"{folder_path}_other" in result
        assert len(result["Title1"]) == 2
        assert len(result[f"{folder_path}_other"]) == 2

    def test_all_images_unmatched(self):
        """全ての画像がマッチしない場合のテスト."""
        scanner = ImageScanner(
            grouping_patterns=[
                r"^\d{4}-\d{2}-\d{2}-(?P<name>.+)-\d+\.",
            ]
        )

        folder_path = "test_folder"
        image_paths = [
            "test_folder/random_image1.png",
            "test_folder/random_image2.png",
        ]

        result = scanner.group_images_by_pattern(folder_path, image_paths)

        # 全てマッチしない場合は folder_path のみがキーになる
        assert len(result) == 1
        assert folder_path in result
        assert len(result[folder_path]) == 2

    def test_no_pattern_all_images_in_one_group(self):
        """パターンがない場合、全画像が1グループになることをテスト."""
        scanner = ImageScanner()

        folder_path = "test_folder"
        image_paths = [
            "test_folder/image1.png",
            "test_folder/image2.png",
            "test_folder/image3.png",
        ]

        result = scanner.group_images_by_pattern(folder_path, image_paths)

        assert len(result) == 1
        assert folder_path in result
        assert len(result[folder_path]) == 3

    def test_multiple_patterns_with_multiple_groups(self):
        """複数パターンで複数グループができることをテスト."""
        scanner = ImageScanner(
            grouping_patterns=[
                r"^\d{4}-\d{2}-\d{2}-(?P<name>.+)-\d+\.",  # 日付付き
                r"^(?P<name>[A-Z]+)-\d+\.",  # 大文字のみ
            ]
        )

        folder_path = "test_folder"
        image_paths = [
            "test_folder/2024-01-01-Title1-1.png",  # パターン1
            "test_folder/2024-01-01-Title1-2.png",  # パターン1
            "test_folder/ABC-1.png",  # パターン2
            "test_folder/ABC-2.png",  # パターン2
            "test_folder/random.png",  # マッチしない
        ]

        result = scanner.group_images_by_pattern(folder_path, image_paths)

        assert len(result) == 3
        assert "Title1" in result
        assert "ABC" in result
        assert f"{folder_path}_other" in result
        assert len(result["Title1"]) == 2
        assert len(result["ABC"]) == 2
        assert len(result[f"{folder_path}_other"]) == 1

    def test_natural_sort_order(self):
        """画像が自然順ソートされることをテスト."""
        scanner = ImageScanner(
            grouping_patterns=[
                r"^(?P<name>.+)-\d+\.",
            ]
        )

        folder_path = "test_folder"
        image_paths = [
            "test_folder/Title-10.png",
            "test_folder/Title-2.png",
            "test_folder/Title-1.png",
            "test_folder/Title-20.png",
        ]

        result = scanner.group_images_by_pattern(folder_path, image_paths)

        assert len(result) == 1
        assert "Title" in result
        # 自然順ソートで 1, 2, 10, 20 の順になる
        assert result["Title"][0].endswith("Title-1.png")
        assert result["Title"][1].endswith("Title-2.png")
        assert result["Title"][2].endswith("Title-10.png")
        assert result["Title"][3].endswith("Title-20.png")

    def test_backward_compatibility_single_pattern(self):
        """後方互換性：単一パターン（grouping_pattern）が動作することをテスト."""
        scanner = ImageScanner(
            grouping_pattern=r"^(?P<name>.+)-\d+\."
        )

        folder_path = "test_folder"
        image_paths = [
            "test_folder/Title1-1.png",
            "test_folder/Title1-2.png",
        ]

        result = scanner.group_images_by_pattern(folder_path, image_paths)

        assert len(result) == 1
        assert "Title1" in result
        assert len(result["Title1"]) == 2

    def test_multiple_patterns_override_single_pattern(self):
        """複数パターンが設定されている場合、単一パターンより優先されることをテスト."""
        scanner = ImageScanner(
            grouping_pattern=r"^OLD-(?P<name>.+)-\d+\.",  # 使われない
            grouping_patterns=[
                r"^NEW-(?P<name>.+)-\d+\.",  # こちらが使われる
            ]
        )

        folder_path = "test_folder"
        image_paths = [
            "test_folder/NEW-Title1-1.png",
            "test_folder/OLD-Title2-1.png",  # マッチしない
        ]

        result = scanner.group_images_by_pattern(folder_path, image_paths)

        assert len(result) == 2
        assert "Title1" in result
        assert f"{folder_path}_other" in result
        assert len(result["Title1"]) == 1
        assert len(result[f"{folder_path}_other"]) == 1
