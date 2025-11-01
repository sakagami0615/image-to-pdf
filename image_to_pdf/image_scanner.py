"""画像ファイルの検索と解析を行うモジュール."""

import re
from pathlib import Path

from .settings import SUPPORTED_IMAGE_EXTENSIONS


def natural_sort_key(text: str) -> list:
    """自然順ソート用のキーを生成する.

    Args:
        text: ソート対象の文字列

    Returns:
        自然順ソート用のキーリスト
    """
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", text)]


class ImageScanner:
    """画像ファイルをスキャンして整理するクラス."""

    def __init__(
        self,
        supported_extensions: set[str] | None = None,
        grouping_pattern: str | None = None,
        grouping_patterns: list[str] | None = None,
    ):
        """ImageScannerの初期化.

        Args:
            supported_extensions: サポートする画像拡張子のセット（省略時はデフォルト値）
            grouping_pattern: PDFグループ化パターン（正規表現、省略時はNone、後方互換性のため残す）
            grouping_patterns: PDFグループ化パターンのリスト（優先順位順、省略時はNone）
        """
        self.scan_results = {}
        # サポートする画像拡張子
        self.supported_extensions = supported_extensions if supported_extensions else SUPPORTED_IMAGE_EXTENSIONS
        # PDFグループ化パターン（後方互換性のため残す）
        self.grouping_pattern = grouping_pattern
        # PDFグループ化パターンのリスト（優先順位順）
        self.grouping_patterns = grouping_patterns if grouping_patterns else []

    def scan_directory(self, root_path: str) -> dict[str, list[str]]:
        """指定されたディレクトリをスキャンして画像を検索する.

        Args:
            root_path: スキャンするルートディレクトリのパス

        Returns:
            フォルダパスをキー、画像ファイルパスのリストを値とする辞書

        Raises:
            ValueError: 指定されたパスが存在しない、またはディレクトリでない場合
        """
        root = Path(root_path)

        if not root.exists():
            raise ValueError(f"指定されたパスが存在しません: {root_path}")

        if not root.is_dir():
            raise ValueError(f"指定されたパスはディレクトリではありません: {root_path}")

        self.scan_results = {}
        self._scan_recursive(root, root)

        # 画像が見つからなかったフォルダを除外
        self.scan_results = {folder: images for folder, images in self.scan_results.items() if images}

        return self.scan_results

    def _scan_recursive(self, current_path: Path, root_path: Path) -> None:
        """再帰的にディレクトリをスキャンする.

        Args:
            current_path: 現在スキャンしているパス
            root_path: スキャンのルートパス
        """
        images_in_current_dir = []

        # 自然順ソートでファイル・ディレクトリを処理
        for item in sorted(current_path.iterdir(), key=lambda p: natural_sort_key(p.name)):
            if item.is_file():
                if item.suffix.lower() in self.supported_extensions:
                    images_in_current_dir.append(str(item))
            elif item.is_dir():
                # サブディレクトリを再帰的にスキャン
                self._scan_recursive(item, root_path)

        if images_in_current_dir:
            # 相対パスをキーとして使用
            relative_path = str(current_path.relative_to(root_path.parent))
            # 画像リストも自然順ソート
            self.scan_results[relative_path] = sorted(images_in_current_dir, key=natural_sort_key)

    def get_pdf_name(self, folder_path: str, root_path: str) -> str:
        """フォルダパスからPDFファイル名を生成する.

        Args:
            folder_path: フォルダの相対パス
            root_path: ルートディレクトリのパス

        Returns:
            生成されたPDFファイル名（拡張子付き）
        """
        folder = Path(folder_path)
        root = Path(root_path)

        # ルートディレクトリからの相対パスを取得
        try:
            relative = folder.relative_to(root)
            # 画像フォルダ名のみ使用（最後のパーツのみ）
            if str(relative) == ".":
                # ルートディレクトリ自体の場合
                pdf_name = folder.name
            else:
                # サブディレクトリの場合
                parts = relative.parts
                pdf_name = parts[-1]
        except ValueError:
            # 相対パスが取得できない場合は単純にフォルダ名を使用
            pdf_name = folder.name

        return f"{pdf_name}.pdf"

    def reorder_images(self, folder_path: str, new_order: list[str]) -> None:
        """指定されたフォルダ内の画像の順序を変更する.

        Args:
            folder_path: フォルダパス
            new_order: 新しい順序の画像パスリスト

        Raises:
            KeyError: 指定されたフォルダパスが見つからない場合
            ValueError: 画像リストの内容が一致しない場合
        """
        if folder_path not in self.scan_results:
            raise KeyError(f"フォルダが見つかりません: {folder_path}")

        current_images = set(self.scan_results[folder_path])
        new_images = set(new_order)

        if current_images != new_images:
            raise ValueError("画像リストの内容が一致しません")

        self.scan_results[folder_path] = new_order

    def group_images_by_pattern(self, folder_path: str, image_paths: list[str]) -> dict[str, list[str]]:
        """画像をパターンに基づいてグループ化する.

        Args:
            folder_path: フォルダパス
            image_paths: 画像パスのリスト

        Returns:
            グループ名をキー、画像パスのリストを値とする辞書
            パターンが設定されていない場合は、フォルダ名をキーとして全画像を返す
        """
        # 新しい形式の複数パターンを使用
        if self.grouping_patterns:
            return self._group_by_multiple_patterns(folder_path, image_paths, self.grouping_patterns)

        # 後方互換性: 古い形式の単一パターンを使用
        if self.grouping_pattern:
            return self._group_by_single_pattern(folder_path, image_paths, self.grouping_pattern)

        # パターンが設定されていない場合は、全画像を1グループにまとめる
        return {folder_path: image_paths}

    def _group_by_single_pattern(
        self, folder_path: str, image_paths: list[str], pattern_str: str
    ) -> dict[str, list[str]]:
        """単一パターンで画像をグループ化する（後方互換性のため）.

        Args:
            folder_path: フォルダパス
            image_paths: 画像パスのリスト
            pattern_str: 正規表現パターン文字列

        Returns:
            グループ名をキー、画像パスのリストを値とする辞書
        """
        groups = {}
        pattern = re.compile(pattern_str)
        has_matched = False  # 正規表現にマッチした画像があるかのフラグ

        for image_path in image_paths:
            filename = Path(image_path).name
            match = pattern.match(filename)

            if match:
                has_matched = True
                # 名前付きグループ 'name' からPDF名を抽出
                try:
                    group_name = match.group("name")
                except IndexError:
                    # 名前付きグループがない場合はフォルダ名を使用
                    group_name = folder_path
            else:
                # パターンにマッチしない場合
                # マッチした画像がある場合は、フォルダ名_otherグループに入れる
                # マッチした画像がない場合は、後で判定するためにotherグループに一時的に入れる
                group_name = f"{folder_path}_other"

            if group_name not in groups:
                groups[group_name] = []

            groups[group_name].append(image_path)

        # 正規表現にマッチした画像がない場合、otherグループをフォルダ名に変更
        if not has_matched and f"{folder_path}_other" in groups:
            groups[folder_path] = groups.pop(f"{folder_path}_other")

        # 各グループ内の画像を自然順ソート
        for group_name in groups:
            groups[group_name] = sorted(groups[group_name], key=natural_sort_key)

        return groups

    def _group_by_multiple_patterns(
        self, folder_path: str, image_paths: list[str], patterns: list[str]
    ) -> dict[str, list[str]]:
        """複数パターンで画像をグループ化する（優先順位順に処理）.

        Args:
            folder_path: フォルダパス
            image_paths: 画像パスのリスト
            patterns: 正規表現パターン文字列のリスト（優先順位順）

        Returns:
            グループ名をキー、画像パスのリストを値とする辞書
        """
        groups = {}
        has_matched = False  # どれかのパターンにマッチした画像があるかのフラグ
        unmatched_images = []  # どのパターンにもマッチしなかった画像

        # 各画像について、優先順位順にパターンを試す
        for image_path in image_paths:
            filename = Path(image_path).name
            matched = False

            # 優先順位順にパターンを試す
            for pattern_str in patterns:
                pattern = re.compile(pattern_str)
                match = pattern.match(filename)

                if match:
                    has_matched = True
                    matched = True
                    # 名前付きグループ 'name' からPDF名を抽出
                    try:
                        group_name = match.group("name")
                    except IndexError:
                        # 名前付きグループがない場合はフォルダ名を使用
                        group_name = folder_path

                    if group_name not in groups:
                        groups[group_name] = []

                    groups[group_name].append(image_path)
                    break  # マッチしたら次の画像へ

            # どのパターンにもマッチしなかった場合
            if not matched:
                unmatched_images.append(image_path)

        # マッチしなかった画像の処理
        if unmatched_images:
            if has_matched:
                # 一部の画像がマッチした場合は、_otherグループに入れる
                groups[f"{folder_path}_other"] = unmatched_images
            else:
                # 全ての画像がマッチしなかった場合は、フォルダ名グループに入れる
                groups[folder_path] = unmatched_images

        # 各グループ内の画像を自然順ソート
        for group_name in groups:
            groups[group_name] = sorted(groups[group_name], key=natural_sort_key)

        return groups
