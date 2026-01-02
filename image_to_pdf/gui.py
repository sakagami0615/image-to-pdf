"""FletによるGUIアプリケーション."""

import os
import traceback
from pathlib import Path

import flet as ft

from .config_manager import ConfigManager
from .image_scanner import ImageScanner
from .logger import setup_logger
from .pdf_converter import PDFConverter
from .settings import (
    PREVIEW_HEIGHT,
    PREVIEW_WIDTH,
    RESULTS_CONTAINER_HEIGHT,
    TOOL_CONFIG_FILE_PATH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from .settings_dialog import SettingsDialog


class ImageToPDFApp:
    """画像をPDFに変換するGUIアプリケーション."""

    def __init__(self, page: ft.Page):
        """アプリケーションの初期化.

        Args:
            page: Fletのページオブジェクト
        """
        self.page = page
        self.page.title = "Image to PDF Converter"
        self.page.window.width = WINDOW_WIDTH
        self.page.window.height = WINDOW_HEIGHT

        # ロガーをセットアップ
        self.logger = setup_logger()

        # 設定マネージャーを初期化
        self.config_manager = ConfigManager(TOOL_CONFIG_FILE_PATH)

        # 設定を反映してスキャナーとコンバーターを初期化
        self.scanner = ImageScanner(
            self.config_manager.get_supported_extensions(),
            self.config_manager.get_pdf_grouping_pattern(),
            self.config_manager.get_enabled_pdf_grouping_patterns(),
        )
        self.converter = PDFConverter(self.config_manager.get_pdf_fit_page_to_image())

        self.selected_folder = ""
        self.scan_results: dict[str, list[str]] = {}
        self.folder_selection: dict[str, bool] = {}
        self.folder_expanded: dict[str, bool] = {}  # フォルダの展開状態を保持
        self.last_moved_image: str | None = None  # 最後に移動した画像のパス

        # UIコンポーネント
        self.folder_path_field = ft.TextField(
            label="フォルダパス",
            hint_text="変換する画像が含まれるフォルダのパスを入力",
            expand=True,
        )

        self.pick_folder_button = ft.ElevatedButton(
            "フォルダを選択",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._pick_folder_clicked,
        )

        self.scan_button = ft.ElevatedButton(
            "検索",
            icon=ft.Icons.SEARCH,
            on_click=self._scan_clicked,
        )

        self.clear_button = ft.ElevatedButton(
            "クリア",
            icon=ft.Icons.CLEAR,
            on_click=self._clear_clicked,
            disabled=True,
        )

        self.settings_button = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            tooltip="設定",
            on_click=self._settings_clicked,
        )

        self.results_container = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.results_section = ft.Column(
            visible=False,
            spacing=10,
        )

        self.convert_button = ft.ElevatedButton(
            "PDFに変換",
            icon=ft.Icons.PICTURE_AS_PDF,
            on_click=self._convert_clicked,
            disabled=True,
        )

        self.delete_images_checkbox = ft.Checkbox(
            label="変換後に画像を削除する",
            value=True,
        )

        self.progress_bar = ft.ProgressBar(
            width=400,
            visible=False,
        )

        self.progress_text = ft.Text("")
        self.status_text = ft.Text(
            "",
            width=800,
            no_wrap=False,
        )

        self._build_ui()

    def _build_ui(self) -> None:
        """UIを構築する."""
        # 検索結果セクションの内容を構築
        self.results_section.controls = [
            ft.Text("検索結果:", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=self.results_container,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5,
                padding=10,
                height=RESULTS_CONTAINER_HEIGHT,  # 高さを制限してスクロール可能に
            ),
            ft.Divider(),
        ]

        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("Image to PDF Converter", size=24, weight=ft.FontWeight.BOLD),
                                ft.Container(expand=True),
                                self.settings_button,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Divider(),
                        ft.Row(
                            [
                                self.folder_path_field,
                                self.pick_folder_button,
                                self.scan_button,
                                self.clear_button,
                            ]
                        ),
                        ft.Divider(),
                        self.results_section,
                        ft.Row(
                            [
                                self.convert_button,
                                self.delete_images_checkbox,
                                self.progress_text,
                            ]
                        ),
                        self.progress_bar,
                        self.status_text,
                    ],
                    spacing=10,
                ),
                padding=20,
                expand=True,
            )
        )

    def _pick_folder_clicked(self, e) -> None:
        """フォルダ選択ボタンのクリックイベント.

        Args:
            e: イベントオブジェクト
        """

        def on_result(e: ft.FilePickerResultEvent):
            if e.path:
                self.folder_path_field.value = e.path
                self.selected_folder = e.path
                self.page.update()

        file_picker = ft.FilePicker(on_result=on_result)
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.get_directory_path(dialog_title="フォルダを選択")

    def _scan_clicked(self, e) -> None:
        """画像検索ボタンのクリックイベント.

        Args:
            e: イベントオブジェクト
        """
        folder_path = self.folder_path_field.value

        if not folder_path:
            self._show_error("フォルダパスを入力してください")
            return

        if not os.path.exists(folder_path):
            self._show_error("指定されたフォルダが存在しません")
            return

        try:
            self.logger.info(f"画像検索開始: {folder_path}")
            self.selected_folder = folder_path
            scan_results_raw = self.scanner.scan_directory(folder_path)

            if not scan_results_raw:
                self.logger.warning("画像ファイルが見つかりませんでした")
                self._show_error("画像ファイルが見つかりませんでした")
                return

            # グループ化パターンが設定されている場合は、画像をグループ化して表示
            self.scan_results = {}
            for folder_path_key, image_paths in scan_results_raw.items():
                folder_groups = self.scanner.group_images_by_pattern(folder_path_key, image_paths)
                self.scan_results.update(folder_groups)

            # すべてのグループを選択状態にする
            self.folder_selection = dict.fromkeys(self.scan_results.keys(), True)
            # すべてのグループを展開状態にする
            self.folder_expanded = dict.fromkeys(self.scan_results.keys(), False)

            self._display_results()
            self.results_section.visible = True
            self.convert_button.disabled = False
            self.clear_button.disabled = False
            self.status_text.value = f"{len(self.scan_results)}個のPDFグループに画像が見つかりました"
            self.status_text.color = ft.Colors.GREEN
            self.logger.info(f"画像検索完了: {len(self.scan_results)}個のPDFグループ")
            self.page.update()

        except Exception as ex:
            self.logger.error(f"画像検索エラー: {str(ex)}")
            self.logger.error(traceback.format_exc())
            self._show_error(f"エラーが発生しました: {str(ex)}")

    def _clear_clicked(self, e) -> None:
        """クリアボタンのクリックイベント.

        Args:
            e: イベントオブジェクト
        """
        self.scan_results = {}
        self.folder_selection = {}
        self.folder_expanded = {}
        self.results_container.controls.clear()
        self.results_section.visible = False
        self.convert_button.disabled = True
        self.clear_button.disabled = True
        self.status_text.value = ""
        self.progress_text.value = ""
        self.progress_bar.visible = False
        self.page.update()

    def _settings_clicked(self, e) -> None:
        """設定ボタンのクリックイベント.

        Args:
            e: イベントオブジェクト
        """

        def on_settings_changed():
            """設定が変更された時の処理."""
            # スキャナーとコンバーターを再初期化
            self.scanner = ImageScanner(
                self.config_manager.get_supported_extensions(),
                self.config_manager.get_pdf_grouping_pattern(),
                self.config_manager.get_enabled_pdf_grouping_patterns(),
            )
            self.converter = PDFConverter(self.config_manager.get_pdf_fit_page_to_image())
            self.logger.info("設定が更新されました")

        # 設定ダイアログを表示
        dialog = SettingsDialog(self.page, self.config_manager, on_settings_changed)
        dialog.show()

    def _display_results(self) -> None:
        """検索結果を表示する."""
        self.results_container.controls.clear()

        for folder_path, image_paths in self.scan_results.items():
            folder_item = self._create_folder_item(folder_path, image_paths)
            self.results_container.controls.append(folder_item)

        self.page.update()

    def _create_folder_item(self, folder_path: str, image_paths: list[str]) -> ft.ExpansionTile:
        """フォルダアイテムを作成する.

        Args:
            folder_path: フォルダパス（またはグループ名）
            image_paths: 画像パスのリスト

        Returns:
            フォルダアイテムのExpansionTile
        """
        # PDF名を生成（pdf_converter.pyと同じロジック）
        if folder_path.endswith("_other"):
            # 正規表現にマッチした画像がある場合のマッチしない画像グループ
            original_folder = folder_path[: -len("_other")]
            pdf_name = Path(original_folder).name + "_other.pdf"
        else:
            # folder_pathがそのままフォルダパスの場合、またはグループ名の場合
            pdf_name = Path(folder_path).name + ".pdf"

        def checkbox_changed(e):
            self.folder_selection[folder_path] = e.control.value
            self.page.update()

        def on_expansion_changed(e):
            """ExpansionTileの展開状態が変更された時の処理."""
            self.folder_expanded[folder_path] = e.data == "true"

        def move_image_up(image_path: str):
            """画像を上に移動する.

            Args:
                image_path: 移動する画像のパス
            """
            try:
                idx = image_paths.index(image_path)
                if idx > 0:
                    image_paths[idx], image_paths[idx - 1] = (
                        image_paths[idx - 1],
                        image_paths[idx],
                    )
                    # scan_resultsを直接更新（グループ化されているため）
                    self.scan_results[folder_path] = image_paths
                    self.last_moved_image = image_path  # 移動した画像を記録
                    self._display_results()
                    self.logger.info(f"画像並び替え: {idx} -> {idx - 1}")
            except Exception as ex:
                self.logger.error(f"画像移動エラー: {str(ex)}")
                self.logger.error(traceback.format_exc())

        def move_image_down(image_path: str):
            """画像を下に移動する.

            Args:
                image_path: 移動する画像のパス
            """
            try:
                idx = image_paths.index(image_path)
                if idx < len(image_paths) - 1:
                    image_paths[idx], image_paths[idx + 1] = (
                        image_paths[idx + 1],
                        image_paths[idx],
                    )
                    # scan_resultsを直接更新（グループ化されているため）
                    self.scan_results[folder_path] = image_paths
                    self.last_moved_image = image_path  # 移動した画像を記録
                    self._display_results()
                    self.logger.info(f"画像並び替え: {idx} -> {idx + 1}")
            except Exception as ex:
                self.logger.error(f"画像移動エラー: {str(ex)}")
                self.logger.error(traceback.format_exc())

        def show_image_preview(image_path: str):
            """画像のプレビューを表示する.

            Args:
                image_path: 表示する画像のパス
            """

            def close_preview(e):
                preview_dialog.open = False
                self.page.update()

            preview_dialog = ft.AlertDialog(
                title=ft.Text(Path(image_path).name),
                content=ft.Container(
                    content=ft.Image(
                        src=image_path,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    width=PREVIEW_WIDTH,
                    height=PREVIEW_HEIGHT,
                ),
                actions=[
                    ft.TextButton("閉じる", on_click=close_preview),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            self.page.overlay.append(preview_dialog)
            preview_dialog.open = True
            self.page.update()

        # 画像リストを作成
        image_list = []
        for idx, img_path in enumerate(image_paths):
            image_name = Path(img_path).name

            # 最後に移動した画像かどうかを判定
            is_moved = self.last_moved_image == img_path

            # 上下ボタン付きのアイテムを作成
            image_item = ft.Container(
                content=ft.Row(
                    [
                        ft.TextButton(
                            f"{idx + 1}. {image_name}",
                            on_click=lambda e, p=img_path: show_image_preview(p),
                            expand=True,
                            style=ft.ButtonStyle(
                                padding=ft.padding.only(left=0),
                                alignment=ft.alignment.center_left,
                            ),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ARROW_UPWARD,
                            tooltip="上に移動",
                            on_click=lambda e, p=img_path: move_image_up(p),
                            disabled=(idx == 0),
                            icon_size=20,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ARROW_DOWNWARD,
                            tooltip="下に移動",
                            on_click=lambda e, p=img_path: move_image_down(p),
                            disabled=(idx == len(image_paths) - 1),
                            icon_size=20,
                        ),
                    ],
                    spacing=5,
                ),
                bgcolor=ft.Colors.AMBER_100 if is_moved else None,  # 移動した画像は黄色でハイライト
                border=ft.border.all(2, ft.Colors.AMBER_700) if is_moved else ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5,
                padding=10,
            )
            image_list.append(image_item)

        checkbox = ft.Checkbox(
            value=self.folder_selection.get(folder_path, True),
            on_change=checkbox_changed,
        )

        # PDF出力先を取得
        if image_paths:
            actual_folder = Path(image_paths[0]).parent

            # folder_pathが "_other" で終わる場合は、親フォルダに出力
            # それ以外（正規表現にマッチした、またはマッチしない画像のみの場合）は、画像フォルダ内に出力
            if folder_path.endswith("_other"):
                # 正規表現にマッチしない画像（マッチした画像がある場合）
                # 親フォルダに出力
                pdf_output_folder = str(actual_folder.parent)
            else:
                # 正規表現にマッチした画像、またはマッチしない画像のみの場合
                # 画像フォルダ内に出力
                pdf_output_folder = str(actual_folder)
        else:
            pdf_output_folder = folder_path

        return ft.ExpansionTile(
            title=ft.Row(
                [
                    checkbox,
                    ft.Text(f"{pdf_name} ({len(image_paths)}枚)", weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
            ),
            subtitle=ft.Text(f"PDF出力先: {pdf_output_folder}", size=12),
            controls=image_list,
            initially_expanded=self.folder_expanded.get(folder_path, False),
            on_change=on_expansion_changed,
        )

    def _convert_clicked(self, e) -> None:
        """PDF変換ボタンのクリックイベント.

        Args:
            e: イベントオブジェクト
        """
        # 選択されたグループのみを変換対象とする（すでにグループ化済み）
        selected_groups = {
            group: images for group, images in self.scan_results.items() if self.folder_selection.get(group, True)
        }

        if not selected_groups:
            self._show_error("変換する対象が選択されていません")
            return

        # 画像フォルダに直接出力
        self._perform_conversion(selected_groups)

    def _perform_conversion(self, image_groups: dict[str, list[str]]) -> None:
        """PDF変換を実行する.

        Args:
            image_groups: 変換する画像グループ
        """
        self.convert_button.disabled = True
        self.progress_bar.visible = True
        self.progress_bar.value = 0
        self.progress_text.value = "変換中..."
        self.page.update()

        self.logger.info(f"PDF変換開始: {len(image_groups)}個のPDF")

        def progress_callback(current, total, pdf_path, error=None):
            progress_value = current / total
            self.progress_bar.value = progress_value
            if error:
                self.progress_text.value = f"{current}/{total} 完了 (エラーあり)"
                self.logger.error(f"PDF変換エラー: {error}")
            else:
                self.progress_text.value = f"{current}/{total} 完了"
                self.logger.info(f"PDF作成完了: {pdf_path}")
            self.page.update()

        try:
            # output_directoryにNoneを渡すことで、各画像フォルダに出力
            # 画像削除フラグを渡す
            delete_images = self.delete_images_checkbox.value
            created_pdfs = self.converter.batch_convert(
                image_groups, output_directory=None, progress_callback=progress_callback, delete_images=delete_images
            )

            self.status_text.value = f"変換完了: {len(created_pdfs)}個のPDFを作成しました"
            self.status_text.color = ft.Colors.GREEN
            self.logger.info(f"PDF変換完了: {len(created_pdfs)}個のPDF作成")

            # 変換完了ダイアログを表示
            self._show_conversion_result(created_pdfs)

        except Exception as ex:
            self.logger.error(f"PDF変換エラー: {str(ex)}")
            self.logger.error(traceback.format_exc())
            self._show_error(f"変換中にエラーが発生しました: {str(ex)}")

        finally:
            self.convert_button.disabled = False
            self.progress_text.value = ""
            self.progress_bar.visible = False
            self.page.update()

    def _show_conversion_result(self, created_pdfs: list[str]) -> None:
        """変換完了ダイアログを表示する.

        Args:
            created_pdfs: 作成されたPDFファイルのパスリスト
        """

        def close_and_clear(e):
            """ダイアログを閉じて検索結果をクリアする."""
            result_dialog.open = False
            self.page.update()
            # 検索結果をクリア
            self._clear_clicked(None)

        # PDFリストを作成
        pdf_list = []
        for pdf_path in created_pdfs:
            pdf_list.append(
                ft.Text(
                    f"• {pdf_path}",
                    size=12,
                    selectable=True,
                )
            )

        result_dialog = ft.AlertDialog(
            title=ft.Text("PDF変換完了", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"{len(created_pdfs)}個のPDFファイルを作成しました:",
                            size=14,
                        ),
                        ft.Divider(),
                        ft.Column(
                            pdf_list,
                            scroll=ft.ScrollMode.AUTO,
                            height=300,
                        ),
                    ],
                    tight=True,
                ),
                width=600,
            ),
            actions=[
                ft.TextButton("閉じる", on_click=close_and_clear),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(result_dialog)
        result_dialog.open = True
        self.page.update()

    def _show_error(self, message: str) -> None:
        """エラーメッセージを表示する.

        Args:
            message: エラーメッセージ
        """
        self.status_text.value = message
        self.status_text.color = ft.Colors.RED
        self.page.update()


def main(page: ft.Page) -> None:
    """アプリケーションのエントリポイント.

    Args:
        page: Fletのページオブジェクト
    """
    ImageToPDFApp(page)
