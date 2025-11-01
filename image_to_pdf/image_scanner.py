"""画像ファイルの検索と解析を行うモジュール."""

from pathlib import Path

from .settings import PDF_INCLUDE_ROOT_FOLDER_NAME, SUPPORTED_IMAGE_EXTENSIONS


class ImageScanner:
    """画像ファイルをスキャンして整理するクラス."""

    # サポートする画像拡張子
    SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS

    def __init__(self):
        """ImageScannerの初期化."""
        self.scan_results: dict[str, list[str]] = {}

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

        for item in sorted(current_path.iterdir()):
            if item.is_file():
                if item.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    images_in_current_dir.append(str(item))
            elif item.is_dir():
                # サブディレクトリを再帰的にスキャン
                self._scan_recursive(item, root_path)

        if images_in_current_dir:
            # 相対パスをキーとして使用
            relative_path = str(current_path.relative_to(root_path.parent))
            self.scan_results[relative_path] = images_in_current_dir

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
            # パーツをハイフンで連結
            if str(relative) == ".":
                # ルートディレクトリ自体の場合
                pdf_name = folder.name
            else:
                # サブディレクトリの場合
                parts = relative.parts

                if PDF_INCLUDE_ROOT_FOLDER_NAME:
                    # ルートフォルダ名を含める（全パスを連結）
                    pdf_name = "-".join(parts)
                else:
                    # 画像フォルダ名のみ使用（最後のパーツのみ）
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
