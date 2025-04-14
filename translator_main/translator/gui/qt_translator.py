#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyQt5ベースの翻訳ツールGUI

このモジュールは翻訳ツールのGUIをPyQt5で実装します。
"""

import sys
import os
import threading
import time
import subprocess
import io
import cv2
import numpy as np
import pytesseract
from PIL import ImageGrab, Image  # PIL関連のインポートを追加
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, 
                            QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton,
                            QStatusBar, QAction, QMenu, QToolBar, QFileDialog, QMessageBox,
                            QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings, QPoint, QMetaObject, pyqtSlot, QEvent
from PyQt5.QtGui import QIcon, QFont, QTextCursor, QColor, QPalette, QMouseEvent
from pynput import keyboard
import json
from datetime import datetime

# 相対インポート
import os
import sys
# 親ディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 翻訳クライアントをインポート
from server_client.translate_client import TranslateClient

# カスタムイベント定義
class QCaptureEvent(QEvent):
    """キャプチャ開始用カスタムイベント"""
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())
    
    def __init__(self):
        super().__init__(self.EVENT_TYPE)

class ClipboardMonitorThread(QThread):
    """クリップボードを監視するスレッド"""
    image_captured = pyqtSignal(object)
    status_update = pyqtSignal(str)  # ステータス更新用シグナル
    request_clear_clipboard = pyqtSignal()  # クリップボードクリアリクエスト用シグナル
    request_launch_snipping_tool = pyqtSignal()  # スニッピングツール起動リクエスト用シグナル
    request_get_clipboard_image = pyqtSignal()  # クリップボード画像取得リクエスト用シグナル
    clipboard_image_result = pyqtSignal(object)  # クリップボード画像結果用シグナル
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.clipboard_image = None
        
    def run(self):
        self.running = True
        # スニッピングツールの起動をメインスレッドにリクエスト
        self.request_launch_snipping_tool.emit()
        # スニッピングツールが起動するまで少し待つ
        time.sleep(0.5)
        self.check_clipboard()
        
    def stop(self):
        self.running = False
        
    def launch_snipping_tool(self):
        """Windowsスニッピングツールを起動する"""
        try:
            # Windowsスクリーンクリップを直接起動（範囲選択モード）
            subprocess.Popen(["explorer", "ms-screenclip:"])
            self.status_update.emit("スニッピングツールを起動しました")
            print("スニッピングツールを起動しました")
        except Exception as e:
            error_msg = f"スニッピングツール起動エラー: {e}"
            self.status_update.emit(error_msg)
            print(error_msg)
            try:
                # 代替方法としてスニッピングツールを起動
                subprocess.Popen(["snippingtool.exe"])
                self.status_update.emit("代替方法でスニッピングツールを起動しました")
                print("代替方法でスニッピングツールを起動しました")
            except Exception as e2:
                error_msg2 = f"代替スニッピングツール起動エラー: {e2}"
                self.status_update.emit(error_msg2)
                print(error_msg2)
            
    def check_clipboard(self):
        """クリップボードを監視して画像が追加されたら処理する"""
        try:
            max_attempts = 20  # 最大試行回数
            attempt = 0
            
            # キャプチャ開始時のクリップボード内容を取得（比較用）
            # メインスレッドに画像取得をリクエスト
            self.request_get_clipboard_image.emit()
            time.sleep(0.1)  # 少し待ってメインスレッドの処理を待つ
            initial_img = self.clipboard_image
            
            while self.running and attempt < max_attempts:
                try:
                    # 現在のクリップボード内容を取得
                    # メインスレッドに画像取得をリクエスト
                    self.request_get_clipboard_image.emit()
                    time.sleep(0.1)  # 少し待ってメインスレッドの処理を待つ
                    current_img = self.clipboard_image
                    
                    # 画像が取得できて、かつ初期状態と異なる場合
                    if current_img is not None:
                        if initial_img is None:
                            # 初期状態が空だった場合
                            self.status_update.emit("新しい画像を検出しました")
                            self.image_captured.emit(current_img)
                            # メインスレッドにクリップボードクリアをリクエスト
                            self.request_clear_clipboard.emit()
                            break
                        else:
                            # 初期状態と現在の状態を比較
                            try:
                                initial_data = initial_img.tobytes()
                                current_data = current_img.tobytes()
                                
                                if initial_data != current_data:
                                    # 異なる画像が検出された
                                    self.status_update.emit("新しい画像を検出しました")
                                    self.image_captured.emit(current_img)
                                    # メインスレッドにクリップボードクリアをリクエスト
                                    self.request_clear_clipboard.emit()
                                    break
                            except Exception as e:
                                error_msg = f"画像比較エラー: {e}"
                                self.status_update.emit(error_msg)
                                print(error_msg)
                except Exception as e:
                    error_msg = f"クリップボード監視中のエラー: {e}"
                    self.status_update.emit(error_msg)
                    print(error_msg)
                
                attempt += 1
                time.sleep(0.5)  # 0.5秒ごとにチェック
                
            if attempt >= max_attempts:
                self.status_update.emit("クリップボード監視がタイムアウトしました")
                
        except Exception as e:
            error_msg = f"クリップボード監視スレッドエラー: {e}"
            self.status_update.emit(error_msg)
            print(error_msg)
    
    def clear_clipboard(self):
        """クリップボードの内容をクリアする"""
        # メインスレッドにクリップボードクリアをリクエスト
        self.request_clear_clipboard.emit()
        
    def get_clipboard_image(self):
        """クリップボードから画像を取得する"""
        # この関数はもう直接使用しない
        # 代わりにメインスレッドに画像取得をリクエストし、シグナルで結果を受け取る
        return self.clipboard_image


class CustomTitleBar(QFrame):
    """カスタムタイトルバー"""
    
    def __init__(self, parent=None, hotkey_text=""):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(25)  # タイトルバーの高さを25pxに調整
        self.setStyleSheet("""
            CustomTitleBar {
                background-color: rgba(44, 62, 80, 180);  /* 透明度を統一 */
                color: white;
                border: none;
            }
            QPushButton {
                background-color: transparent;  /* 完全に透明 */
                color: white;
                border: none;
                padding: 3px;
                font-size: 11px;
                min-width: 20px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 120);  /* ホバー時は少し色付け */
            }
            QPushButton#close_button:hover {
                background-color: rgba(231, 76, 60, 120);  /* ホバー時は少し色付け */
            }
            QLabel {
                color: white;
                font-size: 10px;
                background-color: transparent;  /* ラベルの背景を透明に */
            }
        """)
        
        # レイアウト
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(3, 0, 3, 0)
        self.layout.setSpacing(3)  # ボタン間のスペースを調整
        
        # タイトルラベル
        self.title_label = QLabel("翻訳")
        self.title_label.setFont(QFont("Yu Gothic UI", 10, QFont.Bold))
        self.layout.addWidget(self.title_label)
        
        # ホットキー表示
        if hotkey_text:
            self.hotkey_label = QLabel(f"[{hotkey_text}]")
            self.hotkey_label.setFont(QFont("Yu Gothic UI", 9))
            self.layout.addWidget(self.hotkey_label)
        
        # スペーサー
        self.layout.addStretch()
        
        # ファイルボタン
        self.file_button = QPushButton("F")
        self.file_button.setToolTip("ファイルメニュー")
        self.file_button.clicked.connect(self.show_file_menu)
        self.layout.addWidget(self.file_button)
        
        # ハイライトボタン
        self.highlight_button = QPushButton("H")
        self.highlight_button.setToolTip("背景をハイライト")
        self.highlight_button.setCheckable(True)
        self.highlight_button.clicked.connect(lambda checked: self.parent.toggle_highlight(checked))
        self.layout.addWidget(self.highlight_button)
        
        # クリアボタン
        self.clear_button = QPushButton("C")
        self.clear_button.setToolTip("テキストをクリア")
        self.clear_button.clicked.connect(lambda: self.parent.clear_text())
        self.layout.addWidget(self.clear_button)
        
        # 前の翻訳ボタン
        self.prev_button = QPushButton("←")
        self.prev_button.setToolTip("前の翻訳")
        self.prev_button.clicked.connect(lambda: self.parent.show_prev_translation())
        self.layout.addWidget(self.prev_button)
        
        # 次の翻訳ボタン
        self.next_button = QPushButton("→")
        self.next_button.setToolTip("次の翻訳")
        self.next_button.clicked.connect(lambda: self.parent.show_next_translation())
        self.layout.addWidget(self.next_button)
        
        # 閉じるボタン
        self.close_button = QPushButton("×")
        self.close_button.setObjectName("close_button")
        self.close_button.setToolTip("閉じる")
        self.close_button.clicked.connect(lambda: self.parent.close())
        self.layout.addWidget(self.close_button)
        
        # ドラッグ用の変数
        self.dragging = False
        self.drag_position = QPoint()
        
    def show_file_menu(self):
        """ファイルメニューを表示"""
        menu = QMenu(self)
        
        # 設定ファイルを開くアクション
        open_config_action = QAction("設定ファイルを開く", self)
        open_config_action.triggered.connect(lambda: self.parent.open_config_file())
        menu.addAction(open_config_action)
        
        # 翻訳結果をコピーするアクション
        copy_translation_action = QAction("翻訳結果をコピー", self)
        copy_translation_action.triggered.connect(lambda: self.parent.copy_translation_to_clipboard())
        menu.addAction(copy_translation_action)
        
        # エクスポートアクション
        export_action = QAction("テキストをエクスポート", self)
        export_action.triggered.connect(lambda: self.parent.export_text())
        menu.addAction(export_action)
        
        # 翻訳履歴クリアアクション
        clear_history_action = QAction("翻訳履歴をクリア", self)
        clear_history_action.triggered.connect(lambda: self.parent.clear_translation_history())
        menu.addAction(clear_history_action)
        
        # 常に最前面表示アクション
        topmost_action = QAction("常に最前面に表示", self)
        topmost_action.setCheckable(True)
        topmost_action.setChecked(self.parent.is_always_on_top)
        topmost_action.triggered.connect(lambda checked: self.parent.toggle_always_on_top(checked))
        menu.addAction(topmost_action)
        
        # 終了アクション
        exit_action = QAction("終了", self)
        exit_action.triggered.connect(lambda: self.parent.close())
        menu.addAction(exit_action)
        
        # メニューを表示
        menu.exec_(self.file_button.mapToGlobal(QPoint(0, self.file_button.height())))
        
    def update_navigation_buttons(self, prev_enabled, next_enabled):
        """ナビゲーションボタンの状態を更新"""
        self.prev_button.setEnabled(prev_enabled)
        self.next_button.setEnabled(next_enabled)
        
    def mousePressEvent(self, event):
        """マウスプレスイベント（ドラッグ開始）"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.parent.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """マウスムーブイベント（ドラッグ中）"""
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.parent.move(event.globalPos() - self.drag_position)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        """マウスリリースイベント（ドラッグ終了）"""
        self.dragging = False
        event.accept()


class TranslatorWindow(QMainWindow):
    """翻訳ツールのメインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        
        # 設定の読み込み
        self.config = self.load_config()
        
        # 翻訳ログの読み込み
        self.translation_logs = self.load_translation_logs()
        # 初期表示は空にする（-1に設定）
        self.current_log_index = -1
        
        # クリップボードスレッドの初期化
        self.clipboard_thread = None
        
        # ハイライト状態の初期化
        self.is_highlighted = False
        
        # ウィンドウの設定
        self.resize(
            self.config.get("ui", {}).get("window_width", 500),
            self.config.get("ui", {}).get("window_height", 600)
        )
        
        # タイトルバーを削除してカスタムタイトルバーを使用
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.is_always_on_top = self.config.get("ui", {}).get("always_on_top", True)
        if self.is_always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # 背景を透過
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 中央ウィジェットの設定
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)  # 余白をなくす
        
        # ホットキーテキストを取得
        hotkey_text = self.get_hotkey_text()
        
        # カスタムタイトルバー
        self.title_bar = CustomTitleBar(self, hotkey_text)
        self.layout.addWidget(self.title_bar)
        
        # メインコンテンツ用のコンテナ
        self.content_widget = QWidget()
        self.content_widget.setObjectName("content_widget")  # IDを設定
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        
        # テキスト表示エリア
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)  # 読み取り専用
        
        # 設定ファイルからフォント設定を読み込む
        font_family = self.config.get("ui", {}).get("text", {}).get("font_family", "Yu Gothic UI")
        font_size = self.config.get("ui", {}).get("text", {}).get("font_size", 10)
        self.text_edit.setFont(QFont(font_family, font_size))
        
        self.content_layout.addWidget(self.text_edit)
        
        # ログ情報ラベルを削除
        # self.log_info_label = QLabel("翻訳履歴: 0/0")
        # self.log_info_label.setAlignment(Qt.AlignCenter)
        # self.content_layout.addWidget(self.log_info_label)
        
        # メインレイアウトに追加
        self.layout.addWidget(self.content_widget)
        
        # ハイライト状態を適用
        self.apply_highlight()
        
        # ステータスバー
        self.status_bar = QStatusBar()
        self.status_bar.setObjectName("status_bar")  # IDを設定
        self.setStatusBar(self.status_bar)
        
        # ステータスバーのフォントサイズを小さく
        status_font = QFont("Yu Gothic UI", 8)
        self.status_bar.setFont(status_font)
        
        self.status_bar.showMessage("準備完了")
        
        # キーボードリスナーの設定
        self.is_shift_pressed = False
        self.is_alt_pressed = False
        self.is_win_pressed = False
        self.capture_count = 0
        
        # キーボードリスナーの開始
        self.start_keyboard_listener()
        
        # Tesseractのパス設定
        self.setup_tesseract_path()
        
        # 翻訳クライアント
        self.translate_client = TranslateClient()
        
        # スレッドセーフなクリップボード操作のためのタイマー
        self.clipboard_timer = None
        
        # 翻訳ログの表示を更新
        self.update_log_navigation()
        
        # ダークテーマを適用
        self.apply_dark_theme()
        
    def load_config(self):
        """設定ファイルを読み込む"""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 
                "config.json"
            )
            if os.path.exists(config_path):
                import json
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print("設定ファイルを読み込みました")
                return config
            else:
                print(f"設定ファイルが見つかりません: {config_path}")
                # デフォルト設定を使用
                return {
                    "hotkeys": {
                        "capture": {
                            "win": True,
                            "alt": True,
                            "shift": False,
                            "key": "x"
                        }
                    },
                    "tesseract": {
                        "path": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
                    },
                    "ui": {
                        "window_width": 500,
                        "window_height": 600,
                        "always_on_top": True
                    },
                    "ocr": {
                        "languages": "eng+jpn",
                        "psm": 6
                    }
                }
        except Exception as e:
            print(f"設定ファイルの読み込み中にエラーが発生しました: {e}")
            # デフォルト設定を返す
            return {
                "hotkeys": {
                    "capture": {
                        "win": True,
                        "alt": True,
                        "shift": False,
                        "key": "x"
                    }
                },
                "ui": {
                    "window_width": 500,
                "window_height": 600,
                    "always_on_top": True
                },
                "ocr": {
                    "languages": "eng+jpn",
                    "psm": 6
                }
            }
            
    def load_translation_logs(self):
        """翻訳ログを読み込む"""
        try:
            log_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 
                "translation_logs.json"
            )
            if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
                with open(log_path, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                print(f"翻訳ログを読み込みました: {len(logs)}件")
                return logs
            else:
                print("翻訳ログが見つからないか空です。新規作成します。")
                return []
        except Exception as e:
            print(f"翻訳ログの読み込み中にエラーが発生しました: {e}")
            return []
            
    def save_translation_logs(self):
        """翻訳ログを保存する"""
        try:
            log_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 
                "translation_logs.json"
            )
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(self.translation_logs, f, ensure_ascii=False, indent=2)
            print(f"翻訳ログを保存しました: {len(self.translation_logs)}件")
        except Exception as e:
            print(f"翻訳ログの保存中にエラーが発生しました: {e}")
            
    def get_instruction_text(self):
        """操作説明テキストを取得"""
        hotkey_text = ""
        if self.config and "hotkeys" in self.config and "capture" in self.config["hotkeys"]:
            capture_hotkey = self.config["hotkeys"]["capture"]
            modifiers = []
            if capture_hotkey.get("win", False):
                modifiers.append("Windows")
            if capture_hotkey.get("alt", False):
                modifiers.append("Alt")
            if capture_hotkey.get("shift", False):
                modifiers.append("Shift")
            key = capture_hotkey.get("key", "x").upper()
            hotkey_text = "+".join(modifiers) + "+" + key
        else:
            hotkey_text = "Windows+Alt+X"
        
        return (
            "【操作方法】\n"
            f"{hotkey_text} を押すと、自動的に以下の処理が実行されます：\n"
            f"1. Windowsスニッピングツールが起動\n"
            f"2. 範囲選択後、自動的に画像を読み取り\n"
            f"3. OCR処理と翻訳を実行"
        )
        
    def setup_tesseract_path(self):
        """Tesseractのパスを設定"""
        if self.config and "tesseract" in self.config and "path" in self.config["tesseract"]:
            default_path = self.config["tesseract"]["path"]
        else:
            default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        
        tesseract_exe = os.environ.get("TESSERACT_PATH", default_path)
        tesseract_exe = tesseract_exe.strip()
        
        # パスが存在するか確認
        if os.path.exists(tesseract_exe):
            pytesseract.pytesseract.tesseract_cmd = tesseract_exe
            print(f"Tesseractパスを設定しました: {tesseract_exe}")
        else:
            print(f"警告: Tesseractが見つかりません: {tesseract_exe}")
            self.status_bar.showMessage("警告: Tesseractが見つかりません", 5000)
            
    def start_keyboard_listener(self):
        """キーボードリスナーを開始"""
        self.kb_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.kb_listener.start()
        
    def on_key_press(self, key):
        """キー押下イベント処理"""
        try:
            if key in [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r]:
                self.is_shift_pressed = True
            if key in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r]:
                self.is_alt_pressed = True
            if key == keyboard.Key.cmd:  # Windows/Super キー
                self.is_win_pressed = True
                
            # 設定ファイルからホットキー情報を取得
            capture_key = 'x'  # デフォルト
            need_shift = False
            need_alt = True
            need_win = True
            
            if self.config and "hotkeys" in self.config and "capture" in self.config["hotkeys"]:
                capture_hotkey = self.config["hotkeys"]["capture"]
                capture_key = capture_hotkey.get("key", "x").lower()
                need_shift = capture_hotkey.get("shift", False)
                need_alt = capture_hotkey.get("alt", True)
                need_win = capture_hotkey.get("win", True)
            
            # キーが設定されたキャプチャキーと一致するか確認
            if hasattr(key, 'char') and key.char is not None and key.char.lower() == capture_key:
                # 必要なモディファイアキーが押されているか確認
                if ((not need_shift or self.is_shift_pressed) and 
                    (not need_alt or self.is_alt_pressed) and 
                    (not need_win or self.is_win_pressed)):
                    print("ホットキーが押されました - キャプチャを開始します")
                    # メインスレッドで直接実行（QMetaObjectは使わない）
                    # 代わりにQtのシグナル/スロットを使用
                    QApplication.instance().postEvent(self, QCaptureEvent())
        except Exception as e:
            print(f"キー押下処理中にエラーが発生しました: {e}")
            
    def on_key_release(self, key):
        """キー解放イベント処理"""
        try:
            if key in [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r]:
                self.is_shift_pressed = False
            if key in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r]:
                self.is_alt_pressed = False
            if key == keyboard.Key.cmd:  # Windows/Super キー
                self.is_win_pressed = False
        except Exception as e:
            print(f"キー解放処理中にエラーが発生しました: {e}")
            
    def event(self, event):
        """イベント処理"""
        if event.type() == QCaptureEvent.EVENT_TYPE:
            # キャプチャイベントを処理
            self.start_capture()
            return True
        return super().event(event)

    @pyqtSlot()
    def start_capture(self):
        """キャプチャ処理を開始"""
        self.status_bar.showMessage("キャプチャを開始しています...")
        
        # 既存のスレッドがあれば停止
        if hasattr(self, 'clipboard_thread') and self.clipboard_thread and self.clipboard_thread.isRunning():
            self.clipboard_thread.stop()
            self.clipboard_thread.wait()
            self.clipboard_thread = None
        
        # スレッドセーフなクリップボード操作のためにクリップボードをクリア
        self.clear_clipboard()
        
        # QApplicationの処理を一時的に進める（イベントループを回す）
        QApplication.processEvents()
        
        # 新しいスレッドを開始
        self.clipboard_thread = ClipboardMonitorThread(self)
        self.clipboard_thread.image_captured.connect(self.process_image)
        self.clipboard_thread.status_update.connect(self.update_status)
        self.clipboard_thread.request_clear_clipboard.connect(self.clear_clipboard)
        self.clipboard_thread.request_launch_snipping_tool.connect(self.launch_snipping_tool)
        self.clipboard_thread.request_get_clipboard_image.connect(self.get_clipboard_image_for_thread)
        self.clipboard_thread.start()
        
    def clear_clipboard(self):
        """メインスレッドからクリップボードをクリアする"""
        try:
            # PyQtのクリップボードAPIを使用
            clipboard = QApplication.clipboard()
            clipboard.clear()
            print("メインスレッドからクリップボードをクリアしました")
        except Exception as e:
            print(f"メインスレッドからのクリップボードクリアエラー: {e}")

    def get_clipboard_image_for_thread(self):
        """スレッド用にクリップボードから画像を取得してシグナルで返す"""
        try:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            
            if mime_data.hasImage():
                # クリップボードから画像を取得
                image = clipboard.image()
                if not image.isNull():
                    # QImageをnumpy配列に変換
                    width, height = image.width(), image.height()
                    ptr = image.constBits()
                    ptr.setsize(image.byteCount())
                    arr = np.array(ptr).reshape(height, width, 4)  # RGBA
                    # RGBAからBGRに変換
                    img = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
                    
                    # 結果をシグナルで返す
                    if hasattr(self, 'clipboard_thread') and self.clipboard_thread:
                        self.clipboard_thread.clipboard_image = img
                        self.clipboard_thread.clipboard_image_result.emit(img)
                    return
        except Exception as e:
            print(f"クリップボード画像取得エラー: {e}")
        
        # 画像が取得できなかった場合はNoneを返す
        if hasattr(self, 'clipboard_thread') and self.clipboard_thread:
            self.clipboard_thread.clipboard_image = None
            self.clipboard_thread.clipboard_image_result.emit(None)
            
    def process_image(self, img):
        """画像を処理してOCRと翻訳を実行"""
        if img is None:
            self.status_bar.showMessage("画像の取得に失敗しました", 3000)
            return
            
        self.status_bar.showMessage("画像処理中...")
        
        try:
            # 画像の前処理
            processed_img = self.preprocess_image(img)
            
            # OCR実行
            ocr_config = f'--psm {self.config["ocr"]["psm"]}' if self.config and "ocr" in self.config and "psm" in self.config["ocr"] else '--psm 6'
            ocr_langs = self.config["ocr"]["languages"] if self.config and "ocr" in self.config and "languages" in self.config["ocr"] else 'eng+jpn'
            ocr_text = pytesseract.image_to_string(processed_img, lang=ocr_langs, config=ocr_config).strip()
            
            # 翻訳実行
            translated_text = self.translate_client.translate(ocr_text)
            
            # 翻訳ログに追加
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = {
                "timestamp": timestamp,
                "ocr_text": ocr_text,
                "translated_text": translated_text
            }
            self.translation_logs.append(log_entry)
            self.save_translation_logs()
            
            # 最新の翻訳を表示
            self.current_log_index = len(self.translation_logs) - 1
            self.show_current_translation()
            
            # ナビゲーションボタンの状態を更新
            self.update_log_navigation()
            
            self.status_bar.showMessage("処理完了", 3000)
            
        except Exception as e:
            print(f"画像処理中にエラーが発生しました: {e}")
            self.status_bar.showMessage(f"エラー: {str(e)}", 5000)
            
    def preprocess_image(self, image):
        """画像の前処理を行う"""
        # PILイメージをOpenCV形式に変換
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # グレースケールに変換
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # ノイズ除去（オプション）
        # gray = cv2.medianBlur(gray, 3)
        
        # コントラスト調整（オプション）
        # gray = cv2.equalizeHist(gray)
        
        # 二値化（オプション）
        # _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 処理済み画像を返す
        return gray
        
    def append_text(self, text):
        """テキストエリアにテキストを追加"""
        self.text_edit.moveCursor(QTextCursor.End)
        self.text_edit.insertPlainText(text)
        self.text_edit.moveCursor(QTextCursor.End)
        
    def clear_text(self):
        """テキストエリアをクリア"""
        # 既存のスレッドがあれば停止して確実に終了させる
        if hasattr(self, 'clipboard_thread') and self.clipboard_thread and self.clipboard_thread.isRunning():
            self.clipboard_thread.stop()
            self.clipboard_thread.wait()
            self.clipboard_thread = None
        
        self.text_edit.clear()
        # current_log_indexを-1に設定して初期状態に戻す
        self.current_log_index = -1
        # ナビゲーションボタンの状態を更新
        self.update_log_navigation()
        self.capture_count = 0
        self.status_bar.showMessage("テキストをクリアしました", 3000)
        
    def export_text(self):
        """テキストをファイルにエクスポート"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "テキストをエクスポート", "", "テキストファイル (*.txt);;すべてのファイル (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text_edit.toPlainText())
                self.status_bar.showMessage(f"テキストを {file_path} にエクスポートしました", 3000)
            except Exception as e:
                print(f"テキストエクスポート中にエラーが発生しました: {e}")
                self.status_bar.showMessage(f"エクスポートエラー: {str(e)}", 5000)
                
    def update_status(self, message):
        """ステータスバーを更新（スレッドからのシグナルで呼ばれる）"""
        self.status_bar.showMessage(message)
        
    def toggle_always_on_top(self, checked):
        """常に最前面に表示する設定を切り替え"""
        self.is_always_on_top = checked
        flags = self.windowFlags()
        if checked:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
        self.show()  # ウィンドウを再表示
        
        # 設定を更新
        if "ui" not in self.config:
            self.config["ui"] = {}
        self.config["ui"]["always_on_top"] = checked
        
    def closeEvent(self, event):
        """ウィンドウが閉じられるときの処理"""
        # キーボードリスナーを停止
        if hasattr(self, 'kb_listener'):
            self.kb_listener.stop()
            
        # クリップボードスレッドを停止
        if self.clipboard_thread and self.clipboard_thread.isRunning():
            self.clipboard_thread.stop()
            self.clipboard_thread.wait()
            
        # 親クラスのcloseEventを呼び出す
        super().closeEvent(event)
        
    def get_hotkey_text(self):
        """ホットキーテキストを取得（短い形式）"""
        if self.config and "hotkeys" in self.config and "capture" in self.config["hotkeys"]:
            capture_hotkey = self.config["hotkeys"]["capture"]
            modifiers = []
            if capture_hotkey.get("win", False):
                modifiers.append("Win")
            if capture_hotkey.get("alt", False):
                modifiers.append("Alt")
            if capture_hotkey.get("shift", False):
                modifiers.append("Shift")
            key = capture_hotkey.get("key", "x").upper()
            return "+".join(modifiers) + "+" + key
        else:
            return "Win+Alt+X"
        
    def update_log_navigation(self):
        """ナビゲーションボタンの状態を更新"""
        total_logs = len(self.translation_logs)
        
        if total_logs > 0:
            # 前へボタンの有効/無効
            # 初期状態（-1）の場合でも、履歴があれば左ボタンを有効にする
            prev_enabled = self.current_log_index > 0 or self.current_log_index == -1
            
            # 次へボタンの有効/無効
            # 初期状態（-1）の場合は右ボタンを無効にする
            next_enabled = self.current_log_index >= 0 and self.current_log_index < total_logs - 1
            
            # タイトルバーのナビゲーションボタンも更新
            self.title_bar.update_navigation_buttons(prev_enabled, next_enabled)
        else:
            self.title_bar.update_navigation_buttons(False, False)
            
    def show_current_translation(self):
        """現在選択されている翻訳を表示"""
        if 0 <= self.current_log_index < len(self.translation_logs):
            log = self.translation_logs[self.current_log_index]
            ocr_text = log.get("ocr_text", "")
            translated_text = log.get("translated_text", "")
            
            # 設定ファイルから色を読み込む
            ocr_color = self.config.get("ui", {}).get("text", {}).get("ocr_color", "#CCCCCC")
            translation_color = self.config.get("ui", {}).get("text", {}).get("translation_color", "#FFFFFF")
            
            # 改行をHTMLの<br>タグに変換
            ocr_text_html = ocr_text.replace("\n", "<br>")
            translated_text_html = translated_text.replace("\n", "<br>")
            
            # HTMLフォーマットでテキストを作成
            result_html = f"""
            <div style="color: {ocr_color};">{ocr_text_html}</div>
            <div style="margin: 10px;"></div>
            <div style="color: {translation_color};">【翻訳結果】</div>
            <div style="color: {translation_color}; font-weight: bold;">{translated_text_html}</div>
            """
            
            self.text_edit.clear()
            self.text_edit.setHtml(result_html)
            self.text_edit.moveCursor(QTextCursor.Start)
        else:
            self.text_edit.clear()
            self.text_edit.setPlainText("翻訳履歴がありません")
    
    def show_prev_translation(self):
        """前の翻訳を表示"""
        # 翻訳履歴がある場合
        if len(self.translation_logs) > 0:
            # 現在のインデックスが-1（初期状態）の場合は最新の翻訳を表示
            if self.current_log_index == -1:
                self.current_log_index = len(self.translation_logs) - 1
                self.show_current_translation()
                self.update_log_navigation()
            # それ以外の場合は前の翻訳を表示
            elif self.current_log_index > 0:
                self.current_log_index -= 1
                self.show_current_translation()
                self.update_log_navigation()
    
    def show_next_translation(self):
        """次の翻訳を表示"""
        if self.current_log_index < len(self.translation_logs) - 1:
            self.current_log_index += 1
            self.show_current_translation()
            self.update_log_navigation()
    
    def clear_translation_history(self):
        """翻訳履歴をクリア"""
        reply = QMessageBox.question(
            self, 
            "翻訳履歴のクリア", 
            "すべての翻訳履歴をクリアしますか？\nこの操作は元に戻せません。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.translation_logs = []
            self.save_translation_logs()
            self.current_log_index = -1
            self.update_log_navigation()
            self.text_edit.clear()
            self.status_bar.showMessage("翻訳履歴をクリアしました", 3000)
            
    def open_config_file(self):
        """設定ファイルを開く"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 
            "config.json"
        )
        if os.path.exists(config_path):
            os.startfile(config_path)
            self.status_bar.showMessage("設定ファイルを開きました", 3000)
        else:
            self.status_bar.showMessage("設定ファイルが見つかりません", 3000)
            
    def apply_dark_theme(self):
        """ダークテーマを適用"""
        palette = QPalette()
        
        # ウィンドウの背景色を透明に
        palette.setColor(QPalette.Window, QColor(0, 0, 0, 0))
        
        # ウィジェットの背景色
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(0, 0, 0, 0))  # 完全透明
        palette.setColor(QPalette.AlternateBase, QColor(0, 0, 0, 0))  # 完全透明
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        
        # テキストカラー
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53, 0))  # 透明
        palette.setColor(QPalette.ButtonText, Qt.white)
        
        # リンクカラー
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218, 128))  # 半透明
        palette.setColor(QPalette.HighlightedText, Qt.white)
        
        # アプリケーションに適用
        self.setPalette(palette)
        
        # スタイルシートも適用
        self.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: #ffffff;
                border: none;
            }
            /* スクロールバーのスタイル設定 */
            QScrollBar:vertical {
                background-color: transparent;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(100, 100, 100, 120);  /* 半透明のハンドル */
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
            /* ステータスバー設定 */
            QStatusBar {
                background-color: transparent;  /* 完全に透明 */
                color: rgba(255, 255, 255, 120);  /* テキストは少し透過 */
                font-size: 8px;  /* 文字サイズを小さく */
            }
            QStatusBar::item {
                border: none;  /* 境界線を削除 */
            }
            QLabel {
                color: #ffffff;
            }
            QWidget#content_widget {
                background-color: transparent;
            }
            /* サイズ変更ハンドルは透過しない */
            QSizeGrip {
                background-color: rgba(44, 62, 80, 180);  /* 透過しない */
                width: 16px;
                height: 16px;
            }
        """)
        
    def toggle_highlight(self, checked):
        """背景のハイライト表示を切り替え"""
        self.is_highlighted = checked
        self.apply_highlight()
        
    def apply_highlight(self):
        """ハイライト表示を適用"""
        if self.is_highlighted:
            # 半透明の黒背景を適用（透過率を下げて不透明度を上げる）
            self.content_widget.setStyleSheet("""
                QWidget#content_widget {
                    background-color: rgba(0, 0, 0, 200);
                    border-radius: 5px;
                }
            """)
        else:
            # 透明背景を適用
            self.content_widget.setStyleSheet("""
                QWidget#content_widget {
                    background-color: transparent;
                }
            """)
            
    def launch_snipping_tool(self):
        """Windowsスニッピングツールを起動する"""
        try:
            # Windowsスクリーンクリップを直接起動（範囲選択モード）
            subprocess.Popen(["explorer", "ms-screenclip:"])
            self.status_bar.showMessage("スニッピングツールを起動しました")
            print("スニッピングツールを起動しました")
        except Exception as e:
            error_msg = f"スニッピングツール起動エラー: {e}"
            self.status_bar.showMessage(error_msg)
            print(error_msg)
            try:
                # 代替方法としてスニッピングツールを起動
                subprocess.Popen(["snippingtool.exe"])
                self.status_bar.showMessage("代替方法でスニッピングツールを起動しました")
                print("代替方法でスニッピングツールを起動しました")
            except Exception as e2:
                error_msg2 = f"代替スニッピングツール起動エラー: {e2}"
                self.status_bar.showMessage(error_msg2)
                print(error_msg2)
                
    def copy_translation_to_clipboard(self):
        """翻訳結果をクリップボードにコピー"""
        if 0 <= self.current_log_index < len(self.translation_logs):
            log = self.translation_logs[self.current_log_index]
            translated_text = log.get("translated_text", "")
            
            # PyQtのクリップボードAPIを使用
            clipboard = QApplication.clipboard()
            clipboard.setText(translated_text)
            self.status_bar.showMessage("翻訳結果をクリップボードにコピーしました", 3000)
        else:
            self.status_bar.showMessage("翻訳結果がありません", 3000)


def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # モダンなスタイルを適用
    
    window = TranslatorWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
