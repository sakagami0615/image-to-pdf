"""ConfigManagerのテスト."""

import tempfile
from pathlib import Path

import pytest

from image_to_pdf.config_manager import ConfigManager


class TestConfigManager:
    """ConfigManagerクラスのテスト."""

    @pytest.fixture
    def temp_config_file(self):
        """一時的な設定ファイルを作成するフィクスチャ."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_path = f.name
        yield config_path
        # クリーンアップ
        Path(config_path).unlink(missing_ok=True)

    def test_get_enabled_pdf_grouping_patterns_empty(self, temp_config_file):
        """有効なパターンがない場合、空リストを返すことをテスト."""
        config_manager = ConfigManager(temp_config_file)
        config_manager.set_pdf_grouping_patterns([
            {
                "id": "1",
                "label": "Test",
                "pattern": r"^(?P<name>.+)-\d+\.",
                "description": "Test pattern",
                "enabled": False,
            }
        ])

        result = config_manager.get_enabled_pdf_grouping_patterns()

        assert result == []

    def test_get_enabled_pdf_grouping_patterns_single(self, temp_config_file):
        """有効なパターンが1つの場合をテスト."""
        config_manager = ConfigManager(temp_config_file)
        config_manager.set_pdf_grouping_patterns([
            {
                "id": "1",
                "label": "Pattern1",
                "pattern": r"^(?P<name>.+)-\d+\.",
                "description": "Pattern 1",
                "enabled": True,
            },
            {
                "id": "2",
                "label": "Pattern2",
                "pattern": r"^\d{4}-(?P<name>.+)-\d+\.",
                "description": "Pattern 2",
                "enabled": False,
            }
        ])

        result = config_manager.get_enabled_pdf_grouping_patterns()

        assert len(result) == 1
        assert result[0] == r"^(?P<name>.+)-\d+\."

    def test_get_enabled_pdf_grouping_patterns_multiple(self, temp_config_file):
        """有効なパターンが複数の場合、優先順位順に返されることをテスト."""
        config_manager = ConfigManager(temp_config_file)
        config_manager.set_pdf_grouping_patterns([
            {
                "id": "1",
                "label": "Pattern1",
                "pattern": r"^PATTERN1-(?P<name>.+)-\d+\.",
                "description": "Pattern 1",
                "enabled": True,
            },
            {
                "id": "2",
                "label": "Pattern2",
                "pattern": r"^PATTERN2-(?P<name>.+)-\d+\.",
                "description": "Pattern 2",
                "enabled": True,
            },
            {
                "id": "3",
                "label": "Pattern3",
                "pattern": r"^PATTERN3-(?P<name>.+)-\d+\.",
                "description": "Pattern 3",
                "enabled": False,
            }
        ])

        result = config_manager.get_enabled_pdf_grouping_patterns()

        assert len(result) == 2
        assert result[0] == r"^PATTERN1-(?P<name>.+)-\d+\."
        assert result[1] == r"^PATTERN2-(?P<name>.+)-\d+\."

    def test_get_pdf_grouping_pattern_returns_first_enabled(self, temp_config_file):
        """get_pdf_grouping_pattern()が最初の有効なパターンを返すことをテスト."""
        config_manager = ConfigManager(temp_config_file)
        config_manager.set_pdf_grouping_patterns([
            {
                "id": "1",
                "label": "Pattern1",
                "pattern": r"^FIRST-(?P<name>.+)-\d+\.",
                "description": "First pattern",
                "enabled": True,
            },
            {
                "id": "2",
                "label": "Pattern2",
                "pattern": r"^SECOND-(?P<name>.+)-\d+\.",
                "description": "Second pattern",
                "enabled": True,
            }
        ])

        result = config_manager.get_pdf_grouping_pattern()

        assert result == r"^FIRST-(?P<name>.+)-\d+\."

    def test_get_pdf_grouping_pattern_returns_empty_when_none_enabled(self, temp_config_file):
        """有効なパターンがない場合、空文字列を返すことをテスト."""
        config_manager = ConfigManager(temp_config_file)
        config_manager.set_pdf_grouping_patterns([
            {
                "id": "1",
                "label": "Pattern1",
                "pattern": r"^(?P<name>.+)-\d+\.",
                "description": "Pattern 1",
                "enabled": False,
            }
        ])

        result = config_manager.get_pdf_grouping_pattern()

        assert result == ""

    def test_add_pdf_grouping_pattern(self, temp_config_file):
        """パターンを追加できることをテスト."""
        config_manager = ConfigManager(temp_config_file)

        pattern_id = config_manager.add_pdf_grouping_pattern(
            label="New Pattern",
            pattern=r"^NEW-(?P<name>.+)-\d+\.",
            description="New test pattern",
            enabled=True
        )

        patterns = config_manager.get_pdf_grouping_patterns()
        added_pattern = next(p for p in patterns if p["id"] == pattern_id)

        assert added_pattern["label"] == "New Pattern"
        assert added_pattern["pattern"] == r"^NEW-(?P<name>.+)-\d+\."
        assert added_pattern["description"] == "New test pattern"
        assert added_pattern["enabled"] is True

    def test_update_pdf_grouping_pattern(self, temp_config_file):
        """パターンを更新できることをテスト."""
        config_manager = ConfigManager(temp_config_file)
        config_manager.set_pdf_grouping_patterns([
            {
                "id": "test-id",
                "label": "Original",
                "pattern": r"^ORIGINAL-(?P<name>.+)-\d+\.",
                "description": "Original description",
                "enabled": False,
            }
        ])

        success = config_manager.update_pdf_grouping_pattern(
            pattern_id="test-id",
            label="Updated",
            pattern=r"^UPDATED-(?P<name>.+)-\d+\.",
            description="Updated description",
            enabled=True
        )

        assert success is True
        patterns = config_manager.get_pdf_grouping_patterns()
        updated_pattern = patterns[0]

        assert updated_pattern["label"] == "Updated"
        assert updated_pattern["pattern"] == r"^UPDATED-(?P<name>.+)-\d+\."
        assert updated_pattern["description"] == "Updated description"
        assert updated_pattern["enabled"] is True

    def test_remove_pdf_grouping_pattern(self, temp_config_file):
        """パターンを削除できることをテスト."""
        config_manager = ConfigManager(temp_config_file)
        config_manager.set_pdf_grouping_patterns([
            {
                "id": "keep-id",
                "label": "Keep",
                "pattern": r"^KEEP-(?P<name>.+)-\d+\.",
                "description": "Keep this",
                "enabled": True,
            },
            {
                "id": "remove-id",
                "label": "Remove",
                "pattern": r"^REMOVE-(?P<name>.+)-\d+\.",
                "description": "Remove this",
                "enabled": True,
            }
        ])

        success = config_manager.remove_pdf_grouping_pattern("remove-id")

        assert success is True
        patterns = config_manager.get_pdf_grouping_patterns()
        assert len(patterns) == 1
        assert patterns[0]["id"] == "keep-id"

    def test_migration_from_old_format(self, temp_config_file):
        """旧形式から新形式への移行をテスト."""
        # 旧形式の設定を手動で書き込む
        import json
        with open(temp_config_file, "w", encoding="utf-8") as f:
            json.dump({
                "supported_extensions": [".png", ".jpg"],
                "pdf_fit_page_to_image": True,
                "pdf_grouping_pattern": r"^OLD-(?P<name>.+)-\d+\.",
            }, f)

        config_manager = ConfigManager(temp_config_file)

        # 新形式に移行されているか確認
        patterns = config_manager.get_pdf_grouping_patterns()
        assert len(patterns) == 1
        assert patterns[0]["pattern"] == r"^OLD-(?P<name>.+)-\d+\."
        assert patterns[0]["enabled"] is True
        assert patterns[0]["id"] == "migrated_default"

    def test_save_and_load_patterns(self, temp_config_file):
        """パターンを保存して読み込めることをテスト."""
        config_manager = ConfigManager(temp_config_file)
        config_manager.set_pdf_grouping_patterns([
            {
                "id": "test1",
                "label": "Test Pattern 1",
                "pattern": r"^TEST1-(?P<name>.+)-\d+\.",
                "description": "First test pattern",
                "enabled": True,
            },
            {
                "id": "test2",
                "label": "Test Pattern 2",
                "pattern": r"^TEST2-(?P<name>.+)-\d+\.",
                "description": "Second test pattern",
                "enabled": False,
            }
        ])
        config_manager.save_config()

        # 新しいConfigManagerインスタンスで読み込み
        new_config_manager = ConfigManager(temp_config_file)
        patterns = new_config_manager.get_pdf_grouping_patterns()

        assert len(patterns) == 2
        assert patterns[0]["id"] == "test1"
        assert patterns[0]["enabled"] is True
        assert patterns[1]["id"] == "test2"
        assert patterns[1]["enabled"] is False
