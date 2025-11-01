"""画像をPDFに変換するモジュール."""

import os
from pathlib import Path

from PIL import Image
from reportlab.pdfgen import canvas

from .settings import PDF_FIT_PAGE_TO_IMAGE, PDF_INCLUDE_ROOT_FOLDER_NAME, PDF_PAGE_SIZE


class PDFConverter:
    """画像をPDFに変換するクラス."""

    def __init__(self):
        """PDFConverterの初期化."""
        pass

    def convert_images_to_pdf(self, image_paths: list[str], output_path: str, fit_to_page: bool = True) -> None:
        """複数の画像を1つのPDFファイルに変換する.

        Args:
            image_paths: 画像ファイルパスのリスト
            output_path: 出力するPDFファイルのパス
            fit_to_page: 画像をページサイズに合わせるかどうか

        Raises:
            ValueError: 画像リストが空の場合
            FileNotFoundError: 画像ファイルが見つからない場合
        """
        if not image_paths:
            raise ValueError("画像リストが空です")

        # 出力ディレクトリが存在しない場合は作成
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # PDFキャンバスを作成（初期サイズ、後で各ページごとに変更可能）
        c = canvas.Canvas(str(output_path), pagesize=PDF_PAGE_SIZE)

        for image_path in image_paths:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"画像ファイルが見つかりません: {image_path}")

            try:
                # 画像を読み込み
                with Image.open(image_path) as img:
                    # RGB形式に変換（PDFに埋め込むため）
                    if img.mode not in ("RGB", "L"):
                        img = img.convert("RGB")

                    img_width, img_height = img.size

                    # ページサイズを画像に合わせるかどうか
                    if PDF_FIT_PAGE_TO_IMAGE:
                        # 画像サイズに合わせたページサイズ（余白なし）
                        page_width = img_width
                        page_height = img_height
                        c.setPageSize((page_width, page_height))
                        draw_width = img_width
                        draw_height = img_height
                        x = 0
                        y = 0
                    else:
                        # 固定ページサイズに合わせる
                        page_width, page_height = PDF_PAGE_SIZE

                        if fit_to_page:
                            # 画像のアスペクト比を維持しながらページに収める
                            aspect_ratio = img_width / img_height
                            page_aspect_ratio = page_width / page_height

                            if aspect_ratio > page_aspect_ratio:
                                # 幅に合わせる
                                draw_width = page_width
                                draw_height = page_width / aspect_ratio
                            else:
                                # 高さに合わせる
                                draw_height = page_height
                                draw_width = page_height * aspect_ratio

                            # 中央に配置
                            x = (page_width - draw_width) / 2
                            y = (page_height - draw_height) / 2
                        else:
                            # 元のサイズで配置（ポイント単位）
                            draw_width = img_width
                            draw_height = img_height
                            x = 0
                            y = page_height - draw_height

                    # 画像をPDFに描画
                    c.drawImage(
                        image_path,
                        x,
                        y,
                        width=draw_width,
                        height=draw_height,
                        preserveAspectRatio=True,
                    )

                    # 次のページを追加
                    c.showPage()

            except Exception as e:
                raise RuntimeError(f"画像の処理中にエラーが発生しました: {image_path}\n{str(e)}") from e

        # PDFを保存
        c.save()

    def batch_convert(
        self,
        image_groups: dict,
        output_directory: str = None,
        progress_callback=None,
        delete_images: bool = True,
    ) -> list[str]:
        """複数のフォルダの画像をバッチ変換する.

        Args:
            image_groups: フォルダパスをキー、画像パスリストを値とする辞書
            output_directory: 出力先ディレクトリ（Noneの場合は各画像フォルダに出力）
            progress_callback: 進捗を通知するコールバック関数
            delete_images: 変換後に画像を削除するかどうか（デフォルト: True）

        Returns:
            生成されたPDFファイルのパスリスト

        Raises:
            ValueError: image_groupsが空の場合
        """
        if not image_groups:
            raise ValueError("変換する画像グループが指定されていません")

        created_pdfs = []
        total = len(image_groups)

        for index, (folder_name, image_paths) in enumerate(image_groups.items(), 1):
            if not image_paths:
                continue

            # PDF名を生成（フォルダ名を使用）
            folder_parts = Path(folder_name).parts
            if PDF_INCLUDE_ROOT_FOLDER_NAME:
                # ルートフォルダ名を含める（全パスを連結）
                pdf_name = "-".join(folder_parts) + ".pdf"
            else:
                # 画像フォルダ名のみ使用（最後のパーツのみ）
                pdf_name = folder_parts[-1] + ".pdf"

            # 出力先を決定
            if output_directory:
                # 指定されたディレクトリに出力
                output_dir = Path(output_directory)
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / pdf_name
            else:
                # 画像フォルダと並列に出力（画像ファイルのパスから実際のフォルダを取得）
                if image_paths:
                    actual_folder = Path(image_paths[0]).parent
                    # 親フォルダ（画像フォルダと並列になる場所）に出力
                    parent_folder = actual_folder.parent
                    output_path = parent_folder / pdf_name
                else:
                    # 画像がない場合はスキップ
                    continue

            try:
                self.convert_images_to_pdf(image_paths, str(output_path))
                created_pdfs.append(str(output_path))

                # PDF変換に成功したら画像を削除（delete_imagesがTrueの場合のみ）
                if delete_images:
                    for image_path in image_paths:
                        try:
                            Path(image_path).unlink()
                        except Exception as del_error:
                            print(f"警告: 画像の削除に失敗しました - {image_path}: {str(del_error)}")

                    # フォルダが空になったら削除
                    if image_paths:
                        folder_to_check = Path(image_paths[0]).parent
                        try:
                            # フォルダが空かチェック
                            if folder_to_check.exists() and not any(folder_to_check.iterdir()):
                                folder_to_check.rmdir()
                        except Exception as dir_error:
                            print(f"警告: フォルダの削除に失敗しました - {folder_to_check}: {str(dir_error)}")

                if progress_callback:
                    progress_callback(index, total, str(output_path))

            except Exception as e:
                print(f"エラー: {folder_name} の変換に失敗しました - {str(e)}")
                if progress_callback:
                    progress_callback(index, total, None, error=str(e))

        return created_pdfs
