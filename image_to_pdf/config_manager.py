"""設定を管理するモジュール."""

import json
from pathlib import Path
from typing import Any

from .settings import PDF_FIT_PAGE_TO_IMAGE, PDF_GROUPING_PATTERN, SUPPORTED_IMAGE_EXTENSIONS


class ConfigManager:
    """アプリケーション設定を管理するクラス."""

    DEFAULT_CONFIG = {
        "supported_extensions": list(SUPPORTED_IMAGE_EXTENSIONS),
        "pdf_fit_page_to_image": PDF_FIT_PAGE_TO_IMAGE,
        "pdf_grouping_pattern": PDF_GROUPING_PATTERN,  # 後方互換性のため残す
        "pdf_grouping_patterns": [  # 複数パターン管理
            {
                "id": "default",
                "label": "default",
                "pattern": PDF_GROUPING_PATTERN,
                "description": "yyyy-mm-dd-TITLE-n の画像をTITLE.pdfにまとめる",
                "enabled": False,
            }
        ],
    }

    def __init__(self, config_path: str):
        """ConfigManagerの初期化.

        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = Path(config_path)
        self.config: dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """設定ファイルを読み込む."""
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    self.config = json.load(f)

                # 旧形式から新形式へのマイグレーション
                self._migrate_old_format()

                # デフォルト値でマージ（新しい設定項目が追加された場合に対応）
                for key, value in self.DEFAULT_CONFIG.items():
                    if key not in self.config:
                        self.config[key] = value
            except Exception:
                # 設定ファイルの読み込みに失敗した場合はデフォルト値を使用
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            # 設定ファイルが存在しない場合はデフォルト値を使用
            self.config = self.DEFAULT_CONFIG.copy()

    def _migrate_old_format(self) -> None:
        """旧形式の設定を新形式に移行する."""
        # pdf_grouping_patterns が存在しない場合、旧形式から移行
        if "pdf_grouping_patterns" not in self.config:
            # 旧形式の pdf_grouping_pattern から新形式に変換
            old_pattern = self.config.get("pdf_grouping_pattern", "")

            if old_pattern:
                # 旧パターンを新形式の最初のパターンとして追加
                self.config["pdf_grouping_patterns"] = [
                    {
                        "id": "migrated_default",
                        "label": "移行されたデフォルトパターン",
                        "pattern": old_pattern,
                        "description": "旧設定から移行されたパターン",
                        "enabled": True,
                    }
                ]
            else:
                # パターンがない場合はデフォルトを使用
                self.config["pdf_grouping_patterns"] = self.DEFAULT_CONFIG["pdf_grouping_patterns"].copy()

    def save_config(self) -> None:
        """設定ファイルを保存する."""
        try:
            # ディレクトリが存在しない場合は作成
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise RuntimeError(f"設定ファイルの保存に失敗しました: {str(e)}") from e

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得する.

        Args:
            key: 設定キー
            default: デフォルト値

        Returns:
            設定値
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """設定値を設定する.

        Args:
            key: 設定キー
            value: 設定値
        """
        self.config[key] = value

    def get_supported_extensions(self) -> set:
        """サポートする画像拡張子を取得する.

        Returns:
            画像拡張子のセット
        """
        return set(self.config.get("supported_extensions", self.DEFAULT_CONFIG["supported_extensions"]))

    def set_supported_extensions(self, extensions: set) -> None:
        """サポートする画像拡張子を設定する.

        Args:
            extensions: 画像拡張子のセット
        """
        self.config["supported_extensions"] = list(extensions)

    def get_pdf_fit_page_to_image(self) -> bool:
        """PDFページサイズを画像サイズに合わせるかどうかを取得する.

        Returns:
            True: 画像サイズに合わせる、False: 固定サイズ
        """
        return self.config.get("pdf_fit_page_to_image", self.DEFAULT_CONFIG["pdf_fit_page_to_image"])

    def set_pdf_fit_page_to_image(self, fit: bool) -> None:
        """PDFページサイズを画像サイズに合わせるかどうかを設定する.

        Args:
            fit: True: 画像サイズに合わせる、False: 固定サイズ
        """
        self.config["pdf_fit_page_to_image"] = fit

    def get_pdf_grouping_pattern(self) -> str:
        """PDFグループ化パターンを取得する（後方互換性のため残す）.

        Returns:
            正規表現パターン文字列（有効なパターンがない場合は空文字列）
        """
        # 新しい形式から有効なパターンを取得
        patterns = self.get_pdf_grouping_patterns()
        enabled_patterns = [p for p in patterns if p.get("enabled", False)]
        if enabled_patterns:
            return enabled_patterns[0]["pattern"]
        # 有効なパターンがない場合は空文字列を返す
        return ""

    def get_enabled_pdf_grouping_patterns(self) -> list[str]:
        """有効なPDFグループ化パターンのリストを取得する（優先順位順）.

        Returns:
            有効な正規表現パターン文字列のリスト（優先順位順）
        """
        patterns = self.get_pdf_grouping_patterns()
        enabled_patterns = [p["pattern"] for p in patterns if p.get("enabled", False)]
        return enabled_patterns

    def set_pdf_grouping_pattern(self, pattern: str) -> None:
        """PDFグループ化パターンを設定する（後方互換性のため残す）.

        Args:
            pattern: 正規表現パターン文字列
        """
        self.config["pdf_grouping_pattern"] = pattern

    def get_pdf_grouping_patterns(self) -> list[dict]:
        """PDFグループ化パターンのリストを取得する.

        Returns:
            パターン情報の辞書リスト
        """
        return self.config.get("pdf_grouping_patterns", self.DEFAULT_CONFIG["pdf_grouping_patterns"])

    def set_pdf_grouping_patterns(self, patterns: list[dict]) -> None:
        """PDFグループ化パターンのリストを設定する.

        Args:
            patterns: パターン情報の辞書リスト
        """
        self.config["pdf_grouping_patterns"] = patterns

    def add_pdf_grouping_pattern(self, label: str, pattern: str, description: str = "", enabled: bool = True) -> str:
        """PDFグループ化パターンを追加する.

        Args:
            label: パターンのラベル
            pattern: 正規表現パターン
            description: パターンの説明
            enabled: 有効フラグ

        Returns:
            追加されたパターンのID
        """
        import uuid

        patterns = self.get_pdf_grouping_patterns()
        pattern_id = str(uuid.uuid4())

        new_pattern = {
            "id": pattern_id,
            "label": label,
            "pattern": pattern,
            "description": description,
            "enabled": enabled,
        }

        patterns.append(new_pattern)
        self.set_pdf_grouping_patterns(patterns)

        return pattern_id

    def update_pdf_grouping_pattern(
        self, pattern_id: str, label: str = None, pattern: str = None, description: str = None, enabled: bool = None
    ) -> bool:
        """PDFグループ化パターンを更新する.

        Args:
            pattern_id: パターンのID
            label: パターンのラベル（省略時は更新しない）
            pattern: 正規表現パターン（省略時は更新しない）
            description: パターンの説明（省略時は更新しない）
            enabled: 有効フラグ（省略時は更新しない）

        Returns:
            更新成功の場合True
        """
        patterns = self.get_pdf_grouping_patterns()

        for p in patterns:
            if p["id"] == pattern_id:
                if label is not None:
                    p["label"] = label
                if pattern is not None:
                    p["pattern"] = pattern
                if description is not None:
                    p["description"] = description
                if enabled is not None:
                    p["enabled"] = enabled

                self.set_pdf_grouping_patterns(patterns)
                return True

        return False

    def remove_pdf_grouping_pattern(self, pattern_id: str) -> bool:
        """PDFグループ化パターンを削除する.

        Args:
            pattern_id: パターンのID

        Returns:
            削除成功の場合True
        """
        patterns = self.get_pdf_grouping_patterns()
        original_length = len(patterns)

        patterns = [p for p in patterns if p["id"] != pattern_id]

        if len(patterns) < original_length:
            self.set_pdf_grouping_patterns(patterns)
            return True

        return False

    def reset_to_defaults(self) -> None:
        """設定をデフォルト値にリセットする."""
        self.config = self.DEFAULT_CONFIG.copy()
