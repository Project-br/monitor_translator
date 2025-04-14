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
import win32clipboard
from PIL import Image, ImageGrab
import cv2
import numpy as np
import pytesseract
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, 
                            QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton,
                            QStatusBar, QAction, QMenu, QToolBar, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QFont, QTextCursor
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

class ClipboardMonitorThread(QThread):
    """クリップボードを監視するスレッド"""
    image_captured = pyqtSignal(object)
    status_update = pyqtSignal(str)  # ステータス更新用シグナル
    request_clear_clipboard = pyqtSignal()  # クリップボードクリアリクエスト用シグナル
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        
    def run(self):
        self.running = True
        self.launch_snipping_tool()
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
            initial_img = self.get_clipboard_image()
            
            while self.running and attempt < max_attempts:
                try:
                    # 現在のクリップボード内容を取得
                    current_img = self.get_clipboard_image()
                    
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
        try:
            # スレッドからクリップボードを操作するとエラーになる場合があるため、
            # エラーをキャッチして無視する
            try:
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.CloseClipboard()
                print("クリップボードをクリアしました")
            except Exception as e:
                error_msg = f"クリップボードクリアエラー: {e}"
                print(error_msg)
                # エラーメッセージをシグナルで送信
                self.status_update.emit(error_msg)
        except Exception:
            # 最後のエラーハンドリング
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
    
    def get_clipboard_image(self):
        """クリップボードから画像を取得する"""
        try:
            # PIL.ImageGrabを使用する方法を試す（より信頼性が高い）
            try:
                img = ImageGrab.grabclipboard()
                if isinstance(img, Image.Image):
                    return img
            except Exception as e:
                error_msg = f"ImageGrabでのクリップボード取得に失敗: {e}"
                self.status_update.emit(error_msg)
                print(error_msg)
            
            # win32clipboardを使用する方法を試す
            win32clipboard.OpenClipboard()
            
            # クリップボードにビットマップがあるか確認
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                # ビットマップデータを取得
                data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
                win32clipboard.CloseClipboard()
                
                # ビットマップデータをPIL Imageに変換
                try:
                    # メモリストリームを作成
                    stream = io.BytesIO()
                    
                    # BMP形式のヘッダーを追加
                    bmp_header = bytes([
                        0x42, 0x4D,           # 'BM' ヘッダー
                        0x00, 0x00, 0x00, 0x00,  # ファイルサイズ (後で埋める)
                        0x00, 0x00,           # 予約済み
                        0x00, 0x00,           # 予約済み
                        0x36, 0x00, 0x00, 0x00   # ピクセルデータまでのオフセット
                    ])
                    stream.write(bmp_header)
                    
                    # DIBデータを書き込む
                    stream.write(data)
                    
                    # ストリームの先頭に戻る
                    stream.seek(0)
                    
                    # PIL Imageとして開く
                    img = Image.open(stream)
                    return img
                    
                except Exception as e:
                    error_msg = f"ビットマップ変換エラー: {e}"
                    self.status_update.emit(error_msg)
                    print(error_msg)
                    return None
            else:
                win32clipboard.CloseClipboard()
                return None
                
        except Exception as e:
            error_msg = f"クリップボード読み取りエラー: {e}"
            self.status_update.emit(error_msg)
            print(error_msg)
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            return None


class TranslatorWindow(QMainWindow):
    """翻訳ツールのメインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        
        # 設定の読み込み
        self.config = self.load_config()
        
        # 翻訳ログの読み込み
        self.translation_logs = self.load_translation_logs()
        self.current_log_index = -1  # 現在表示中のログインデックス
        
        # ウィンドウの設定
        self.setWindowTitle("お手軽翻訳ツール")
        self.resize(
            self.config.get("ui", {}).get("window_width", 500),
            self.config.get("ui", {}).get("window_height", 600)
        )
        
        # 常に最前面に表示
        if self.config.get("ui", {}).get("always_on_top", True):
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # 中央ウィジェットの設定
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # 操作説明ラベル
        self.instruction_label = QLabel(self.get_instruction_text())
        self.instruction_label.setWordWrap(True)
        self.layout.addWidget(self.instruction_label)
        
        # テキスト表示エリア
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)  # 読み取り専用
        self.text_edit.setFont(QFont("Yu Gothic UI", 10))
        self.layout.addWidget(self.text_edit)
        
        # ナビゲーションボタン（前後の翻訳に移動）
        self.nav_layout = QHBoxLayout()
        
        # 前の翻訳ボタン
        self.prev_button = QPushButton("← 前の翻訳")
        self.prev_button.clicked.connect(self.show_prev_translation)
        self.prev_button.setEnabled(False)  # 初期状態では無効
        self.nav_layout.addWidget(self.prev_button)
        
        # ログ情報ラベル
        self.log_info_label = QLabel("翻訳履歴: 0/0")
        self.log_info_label.setAlignment(Qt.AlignCenter)
        self.nav_layout.addWidget(self.log_info_label)
        
        # 次の翻訳ボタン
        self.next_button = QPushButton("次の翻訳 →")
        self.next_button.clicked.connect(self.show_next_translation)
        self.next_button.setEnabled(False)  # 初期状態では無効
        self.nav_layout.addWidget(self.next_button)
        
        self.layout.addLayout(self.nav_layout)
        
        # ステータスバー
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備完了")
        
        # ツールバーの設定
        self.setup_toolbar()
        
        # メニューバーの設定
        self.setup_menu()
        
        # キーボードリスナーの設定
        self.is_shift_pressed = False
        self.is_alt_pressed = False
        self.is_win_pressed = False
        self.capture_count = 0
        
        # クリップボードモニタースレッド
        self.clipboard_thread = None
        
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
                    self.start_capture()
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
            
    def start_capture(self):
        """キャプチャ処理を開始"""
        self.status_bar.showMessage("キャプチャを開始しています...")
        
        # 既存のスレッドがあれば停止
        if self.clipboard_thread and self.clipboard_thread.isRunning():
            self.clipboard_thread.stop()
            self.clipboard_thread.wait()
            
        # スレッドセーフなクリップボード操作のためにクリップボードをクリア
        self.clear_clipboard()
        
        # 新しいスレッドを開始
        self.clipboard_thread = ClipboardMonitorThread(self)
        self.clipboard_thread.image_captured.connect(self.process_image)
        self.clipboard_thread.status_update.connect(self.update_status)
        self.clipboard_thread.request_clear_clipboard.connect(self.clear_clipboard)
        self.clipboard_thread.start()
        
    def clear_clipboard(self):
        """メインスレッドからクリップボードをクリアする"""
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()
            print("メインスレッドからクリップボードをクリアしました")
        except Exception as e:
            print(f"メインスレッドからのクリップボードクリアエラー: {e}")
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
        
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
        self.text_edit.clear()
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
        
    def setup_toolbar(self):
        """ツールバーの設定"""
        toolbar = QToolBar("メインツールバー")
        self.addToolBar(toolbar)
        
        # キャプチャボタン
        capture_action = QAction(QIcon(), "キャプチャ", self)
        capture_action.triggered.connect(self.start_capture)
        toolbar.addAction(capture_action)
        
        # クリアボタン
        clear_action = QAction(QIcon(), "クリア", self)
        clear_action.triggered.connect(self.clear_text)
        toolbar.addAction(clear_action)
        
    def setup_menu(self):
        """メニューバーの設定"""
        menu_bar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menu_bar.addMenu("ファイル")
        
        # エクスポートアクション
        export_action = QAction("テキストをエクスポート", self)
        export_action.triggered.connect(self.export_text)
        file_menu.addAction(export_action)
        
        # 翻訳履歴クリアアクション
        clear_history_action = QAction("翻訳履歴をクリア", self)
        clear_history_action.triggered.connect(self.clear_translation_history)
        file_menu.addAction(clear_history_action)
        
        # 終了アクション
        exit_action = QAction("終了", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 設定メニュー
        settings_menu = menu_bar.addMenu("設定")
        
        # 常に最前面表示アクション
        topmost_action = QAction("常に最前面に表示", self)
        topmost_action.setCheckable(True)
        topmost_action.setChecked(self.config.get("ui", {}).get("always_on_top", True))
        topmost_action.triggered.connect(self.toggle_always_on_top)
        settings_menu.addAction(topmost_action)
        
    def show_current_translation(self):
        """現在選択されている翻訳を表示"""
        if 0 <= self.current_log_index < len(self.translation_logs):
            log = self.translation_logs[self.current_log_index]
            timestamp = log.get("timestamp", "不明")
            ocr_text = log.get("ocr_text", "")
            translated_text = log.get("translated_text", "")
            
            result_text = (
                f"【日時】{timestamp}\n\n"
                f"【OCR結果】\n{ocr_text}\n\n"
                f"【翻訳結果】\n{translated_text}\n\n"
            )
            
            self.text_edit.clear()
            self.text_edit.insertPlainText(result_text)
            self.text_edit.moveCursor(QTextCursor.Start)
        else:
            self.text_edit.clear()
            self.text_edit.insertPlainText("翻訳履歴がありません")
    
    def show_prev_translation(self):
        """前の翻訳を表示"""
        if self.current_log_index > 0:
            self.current_log_index -= 1
            self.show_current_translation()
            self.update_log_navigation()
    
    def show_next_translation(self):
        """次の翻訳を表示"""
        if self.current_log_index < len(self.translation_logs) - 1:
            self.current_log_index += 1
            self.show_current_translation()
            self.update_log_navigation()
    
    def update_log_navigation(self):
        """ナビゲーションボタンの状態とログ情報を更新"""
        total_logs = len(self.translation_logs)
        
        if total_logs > 0:
            current_index = self.current_log_index + 1  # 1-based for display
            self.log_info_label.setText(f"翻訳履歴: {current_index}/{total_logs}")
            
            # 前へボタンの有効/無効
            self.prev_button.setEnabled(self.current_log_index > 0)
            
            # 次へボタンの有効/無効
            self.next_button.setEnabled(self.current_log_index < total_logs - 1)
        else:
            self.log_info_label.setText("翻訳履歴: 0/0")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            
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


def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # モダンなスタイルを適用
    
    window = TranslatorWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
