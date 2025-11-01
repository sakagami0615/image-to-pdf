"""設定ダイアログモジュール."""

import copy

import flet as ft

from .config_manager import ConfigManager


class SettingsDialog:
    """設定ダイアログクラス."""

    def __init__(self, page: ft.Page, config_manager: ConfigManager, on_settings_changed=None):
        """SettingsDialogの初期化.

        Args:
            page: Fletのページオブジェクト
            config_manager: 設定管理オブジェクト
            on_settings_changed: 設定変更時のコールバック関数
        """
        self.page = page
        self.config_manager = config_manager
        self.on_settings_changed = on_settings_changed

        # 設定ダイアログのコントロール
        self.extensions_list_view = None
        self.extensions_list_container = None  # 拡張子リストのコンテナ
        self.new_extension_field = None
        self.pdf_fit_switch = None
        self.grouping_pattern_field = None  # グループ化パターン入力フィールド（旧形式、非推奨）
        self.patterns_list_view = None  # パターンリストビュー
        self.patterns_list_container = None  # パターンリストコンテナ
        self.dialog = None
        self.extensions = []  # 現在の拡張子リスト
        self.patterns = []  # 現在のパターンリスト

    def show(self) -> None:
        """設定ダイアログを表示する."""
        # 現在の設定を取得
        supported_extensions = self.config_manager.get_supported_extensions()
        pdf_fit = self.config_manager.get_pdf_fit_page_to_image()
        grouping_pattern = self.config_manager.get_pdf_grouping_pattern()

        # 拡張子リストを初期化（ソート済み）
        # self.extensions = sorted(list(supported_extensions))
        self.extensions = sorted(supported_extensions)

        # パターンリストを初期化（ディープコピー）
        self.patterns = copy.deepcopy(self.config_manager.get_pdf_grouping_patterns())

        # 拡張子入力フィールド
        self.new_extension_field = ft.TextField(
            label="新しい拡張子を追加",
            hint_text="例: .svg",
            width=200,
            height=35,
            content_padding=8,
        )

        def add_extension(e):
            """拡張子を追加する."""
            ext = self.new_extension_field.value.strip()
            if not ext:
                self._show_error("拡張子を入力してください")
                return

            # ドットで始まっていなければ追加
            if not ext.startswith("."):
                ext = "." + ext

            # 小文字に変換
            ext = ext.lower()

            # すでに存在する場合はエラー
            if ext in self.extensions:
                self._show_error(f"{ext} はすでに追加されています")
                return

            # 拡張子を追加
            self.extensions.append(ext)
            self.extensions.sort()

            # UIを更新
            self._update_extensions_list()
            self.new_extension_field.value = ""
            self.page.update()

        def remove_extension(ext):
            """拡張子を削除する."""
            if ext in self.extensions:
                self.extensions.remove(ext)
                self._update_extensions_list()
                self.page.update()

        # 拡張子リストビュー
        self.extensions_list_view = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=1,
        )

        # 拡張子リストコンテナ（高さは動的に調整）
        self.extensions_list_container = ft.Container(
            content=self.extensions_list_view,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=5,
            padding=10,
            width=600,
            height=100,  # 初期値、後で調整される
        )

        self._update_extensions_list()

        # PDF設定チェックボックスを作成（Switchより小さい）
        self.pdf_fit_switch = ft.Checkbox(
            label="PDFページサイズを画像サイズに合わせる",
            value=pdf_fit,
        )

        # グループ化パターン入力フィールド（旧形式、非推奨）
        self.grouping_pattern_field = ft.TextField(
            label="PDFグループ化パターン（正規表現）",
            value=grouping_pattern,
            hint_text=r"例: ^(?P<name>[^_]+)_.*",
            width=550,
            multiline=False,
        )

        # パターンリストビュー
        self.patterns_list_view = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=5,
        )

        # パターンリストコンテナ（高さは動的に調整）
        self.patterns_list_container = ft.Container(
            content=self.patterns_list_view,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=5,
            padding=10,
            width=580,
            height=150,  # 初期値
        )

        self._update_patterns_list()

        def add_new_pattern(e):
            """新しいパターンを追加するダイアログを表示."""
            self._show_pattern_edit_dialog()

        def close_dialog(e):
            """ダイアログを閉じる."""
            self.dialog.open = False
            self.page.update()

        def save_settings(e):
            """設定を保存する."""
            # 最低1つは選択されている必要がある
            if not self.extensions:
                self._show_error("最低1つの画像拡張子を設定してください")
                return

            # 設定を保存
            self.config_manager.set_supported_extensions(set(self.extensions))
            self.config_manager.set_pdf_fit_page_to_image(self.pdf_fit_switch.value)
            self.config_manager.set_pdf_grouping_pattern(self.grouping_pattern_field.value)
            # 新しい形式のパターンリストを保存
            self.config_manager.set_pdf_grouping_patterns(self.patterns)

            try:
                self.config_manager.save_config()

                # 設定変更コールバックを呼び出す
                if self.on_settings_changed:
                    self.on_settings_changed()

                # 成功メッセージを表示
                self._show_success("設定を保存しました")

                # ダイアログを閉じる
                close_dialog(e)

            except Exception as ex:
                self._show_error(f"設定の保存に失敗しました: {str(ex)}")

        def reset_to_defaults(e):
            """設定をデフォルトに戻す."""
            self.config_manager.reset_to_defaults()

            # UIを更新
            default_extensions = self.config_manager.get_supported_extensions()
            self.extensions = sorted(default_extensions)
            self._update_extensions_list()

            self.pdf_fit_switch.value = self.config_manager.get_pdf_fit_page_to_image()
            self.grouping_pattern_field.value = self.config_manager.get_pdf_grouping_pattern()

            # パターンリストもリセット
            self.patterns = copy.deepcopy(self.config_manager.get_pdf_grouping_patterns())
            self._update_patterns_list()

            self.page.update()

        # ダイアログを作成
        self.dialog = ft.AlertDialog(
            title=ft.Text("設定", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "サポートする画像拡張子",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Divider(),
                        ft.Row(
                            [
                                self.new_extension_field,
                                ft.ElevatedButton(
                                    "追加",
                                    icon=ft.Icons.ADD,
                                    on_click=add_extension,
                                    height=25,
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Container(height=5),
                        self.extensions_list_container,
                        ft.Divider(),
                        ft.Text(
                            "PDF設定",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Divider(),
                        ft.Container(
                            content=ft.Column(
                                [
                                    self.pdf_fit_switch,
                                    ft.Text(
                                        "チェック: 画像サイズに合わせたページサイズ（余白なし）\n"
                                        "未チェック: 固定サイズ（A4）に合わせる（余白あり）",
                                        size=11,
                                        color=ft.Colors.GREY_700,
                                    ),
                                ],
                                spacing=3,
                            ),
                            padding=ft.padding.only(left=10),
                        ),
                        ft.Divider(),
                        ft.Text(
                            "PDFグループ化パターン",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Divider(),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(
                                                "画像ファイル名から正規表現でPDF名を抽出します",
                                                size=12,
                                                color=ft.Colors.GREY_700,
                                            ),
                                            ft.ElevatedButton(
                                                "新しいパターンを追加",
                                                icon=ft.Icons.ADD,
                                                on_click=add_new_pattern,
                                                height=30,
                                            ),
                                        ],
                                        spacing=10,
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    ),
                                    ft.Container(height=5),
                                    self.patterns_list_container,
                                    ft.Text(
                                        "※ 有効なパターンでファイル名をグループ化してPDFを作成します\n"
                                        "※ パターンが無効な場合は、フォルダ内の全画像を1つのPDFにまとめます",
                                        size=11,
                                        color=ft.Colors.GREY_700,
                                    ),
                                ],
                                spacing=5,
                            ),
                            padding=ft.padding.only(left=10),
                        ),
                    ],
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=600,
                height=700,
            ),
            actions=[
                ft.TextButton("デフォルトに戻す", on_click=reset_to_defaults),
                ft.TextButton("キャンセル", on_click=close_dialog),
                ft.ElevatedButton("保存", on_click=save_settings),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def _update_extensions_list(self):
        """拡張子リストを更新する."""
        self.extensions_list_view.controls.clear()

        if not self.extensions:
            self.extensions_list_view.controls.append(
                ft.Text("拡張子が設定されていません", color=ft.Colors.GREY_600, italic=True)
            )
            # 空の場合は小さい高さに設定
            if self.extensions_list_container:
                self.extensions_list_container.height = 40
        else:
            for ext in self.extensions:

                def create_remove_handler(extension):
                    return lambda e: self._remove_extension(extension)

                self.extensions_list_view.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(ext, size=12, expand=True),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color=ft.Colors.RED_400,
                                    tooltip="削除",
                                    on_click=create_remove_handler(ext),
                                    icon_size=16,
                                    padding=0,
                                ),
                            ],
                            spacing=0,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        border=ft.border.all(1, ft.Colors.OUTLINE),
                        border_radius=3,
                        padding=ft.padding.symmetric(horizontal=3, vertical=1),
                    )
                )

            # 拡張子の数に応じて高さを調整
            # 各アイテムの高さ: 約45px（テキスト12px + パディング + ボーダー）
            # パディング: 11px * 2 = 20px
            item_height = 45
            spacing_total = 0
            total_height = item_height * len(self.extensions) + spacing_total + 22

            # 最大400pxに制限
            calculated_height = max(0, min(400, total_height))

            if self.extensions_list_container:
                self.extensions_list_container.height = calculated_height

    def _remove_extension(self, ext):
        """拡張子を削除する.

        Args:
            ext: 削除する拡張子
        """
        if ext in self.extensions:
            self.extensions.remove(ext)
            self._update_extensions_list()
            self.page.update()

    def _show_error(self, message: str) -> None:
        """エラーメッセージを表示する.

        Args:
            message: エラーメッセージ
        """
        snack = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def _show_success(self, message: str) -> None:
        """成功メッセージを表示する.

        Args:
            message: 成功メッセージ
        """
        snack = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.GREEN,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def _update_patterns_list(self):
        """パターンリストを更新する."""
        if self.patterns_list_view is None:
            return

        self.patterns_list_view.controls.clear()

        if not self.patterns:
            self.patterns_list_view.controls.append(
                ft.Text("パターンが設定されていません", color=ft.Colors.GREY_600, italic=True)
            )
            # パターンがない場合は小さい高さに設定
            if self.patterns_list_container:
                self.patterns_list_container.height = 50
        else:
            for pattern in self.patterns:

                def create_toggle_handler(p):
                    return lambda e: self._toggle_pattern(p["id"], e.control.value)

                def create_edit_handler(p):
                    return lambda e: self._show_pattern_edit_dialog(p)

                def create_delete_handler(p):
                    return lambda e: self._delete_pattern(p["id"])

                # チェックボックス
                checkbox = ft.Checkbox(
                    value=pattern.get("enabled", False),
                    on_change=create_toggle_handler(pattern),
                )

                # パターン情報を表示
                pattern_info = ft.Column(
                    [
                        ft.Text(pattern.get("label", "無名パターン"), size=14, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            f"パターン: {pattern.get('pattern', '')}",
                            size=11,
                            color=ft.Colors.GREY_700,
                        ),
                        ft.Text(
                            f"説明: {pattern.get('description', '説明なし')}",
                            size=11,
                            color=ft.Colors.GREY_600,
                            italic=True,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                )

                # アクションボタン
                action_buttons = ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color=ft.Colors.BLUE_400,
                            tooltip="編集",
                            on_click=create_edit_handler(pattern),
                            icon_size=20,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ft.Colors.RED_400,
                            tooltip="削除",
                            on_click=create_delete_handler(pattern),
                            icon_size=20,
                        ),
                    ],
                    spacing=5,
                )

                # パターン行
                pattern_row = ft.Row(
                    [
                        checkbox,
                        pattern_info,
                        action_buttons,
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                )

                self.patterns_list_view.controls.append(
                    ft.Container(
                        content=pattern_row,
                        border=ft.border.all(1, ft.Colors.OUTLINE),
                        border_radius=5,
                        padding=10,
                        bgcolor=ft.Colors.GREEN_50 if pattern.get("enabled", False) else None,
                    )
                )

            # パターンの数に応じて高さを調整
            # 各パターンアイテムの高さ: 約80px（チェックボックス + テキスト3行 + パディング + ボーダー）
            item_height = 80
            spacing_total = 0
            spacing_total = (len(self.patterns) - 1) * 4  # spacing=4
            padding = 20  # コンテナのパディング
            total_height = item_height * len(self.patterns) + spacing_total + padding

            # 最小0px、最大400pxに制限
            calculated_height = max(0, min(400, total_height))

            if self.patterns_list_container:
                self.patterns_list_container.height = calculated_height

    def _toggle_pattern(self, pattern_id: str, enabled: bool):
        """パターンの有効/無効を切り替える.

        Args:
            pattern_id: パターンID
            enabled: 有効フラグ
        """
        for pattern in self.patterns:
            if pattern["id"] == pattern_id:
                pattern["enabled"] = enabled
                break

        self._update_patterns_list()
        self.page.update()

    def _delete_pattern(self, pattern_id: str):
        """パターンを削除する.

        Args:
            pattern_id: パターンID
        """
        self.patterns = [p for p in self.patterns if p["id"] != pattern_id]
        self._update_patterns_list()
        self.page.update()

    def _show_pattern_edit_dialog(self, pattern: dict = None):
        """パターン追加・編集ダイアログを表示する.

        Args:
            pattern: 編集するパターン（Noneの場合は新規追加）
        """
        import uuid

        is_edit = pattern is not None

        # 入力フィールド
        label_field = ft.TextField(
            label="ラベル",
            value=pattern.get("label", "") if is_edit else "",
            hint_text="例: 日付形式パターン",
            width=500,
        )

        pattern_field = ft.TextField(
            label="正規表現パターン",
            value=pattern.get("pattern", "") if is_edit else "",
            hint_text=r"例: ^(?P<name>[^_]+)_.*",
            width=500,
            multiline=False,
        )

        description_field = ft.TextField(
            label="説明",
            value=pattern.get("description", "") if is_edit else "",
            hint_text="例: アンダースコアで区切られた最初の部分をPDF名として使用",
            width=500,
            multiline=True,
            min_lines=2,
            max_lines=4,
        )

        enabled_checkbox = ft.Checkbox(
            label="有効にする",
            value=pattern.get("enabled", True) if is_edit else True,
        )

        def close_pattern_dialog(e):
            """パターンダイアログを閉じる."""
            pattern_dialog.open = False
            # ダイアログをオーバーレイから削除
            if pattern_dialog in self.page.overlay:
                self.page.overlay.remove(pattern_dialog)
            # メイン設定ダイアログを再表示
            if self.dialog:
                self.dialog.open = True
            self.page.update()

        def save_pattern(e):
            """パターンを保存する."""
            # バリデーション
            if not label_field.value or not label_field.value.strip():
                self._show_error("ラベルを入力してください")
                return

            if not pattern_field.value or not pattern_field.value.strip():
                self._show_error("正規表現パターンを入力してください")
                return

            # 正規表現の妥当性チェック
            import re

            try:
                re.compile(pattern_field.value)
            except re.error as ex:
                self._show_error(f"正規表現が不正です: {str(ex)}")
                return

            if is_edit:
                # 既存パターンを更新
                for p in self.patterns:
                    if p["id"] == pattern["id"]:
                        p["label"] = label_field.value.strip()
                        p["pattern"] = pattern_field.value.strip()
                        p["description"] = description_field.value.strip()
                        p["enabled"] = enabled_checkbox.value
                        break
            else:
                # 新規パターンを追加
                new_pattern = {
                    "id": str(uuid.uuid4()),
                    "label": label_field.value.strip(),
                    "pattern": pattern_field.value.strip(),
                    "description": description_field.value.strip(),
                    "enabled": enabled_checkbox.value,
                }
                self.patterns.append(new_pattern)

            self._update_patterns_list()
            close_pattern_dialog(e)

            # メイン設定ダイアログを前面に表示
            self.page.update()

        # パターンダイアログ
        pattern_dialog = ft.AlertDialog(
            title=ft.Text("パターンを編集" if is_edit else "新しいパターンを追加", size=18),
            content=ft.Container(
                content=ft.Column(
                    [
                        label_field,
                        pattern_field,
                        description_field,
                        ft.Container(height=10),
                        enabled_checkbox,
                        ft.Container(height=5),
                        ft.Text(
                            "※ パターンには (?P<name>...) で PDF 名を指定するグループが必要です\n"
                            '※ 例: ^(?P<name>[^_]+)_.* で "ABC_001.png" から "ABC.pdf" を生成',
                            size=11,
                            color=ft.Colors.GREY_700,
                        ),
                    ],
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=550,
                height=400,
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=close_pattern_dialog),
                ft.ElevatedButton("保存", on_click=save_pattern),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(pattern_dialog)
        pattern_dialog.open = True
        self.page.update()
