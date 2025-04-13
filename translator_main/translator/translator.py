import cv2
import numpy as np
import pytesseract
import os
import json
from PIL import ImageGrab
import threading
import tkinter as tk
from pynput import keyboard, mouse
from pynput.mouse import Controller as MouseController
import sys
import time
from server_client.translate_client import TranslateClient  # 翻訳クライアントをインポート

# グローバル変数
is_shift_pressed = False
is_alt_pressed = False
is_win_pressed = False
capture_count = 0  # OCR キャプチャの連番
capture_hotkey_active = False
capture_hotkey_start = None
mouse_controller = MouseController()
config = None  # 設定ファイルの内容を保持

# Tkinter ウィンドウ（OCR 結果表示用）
root = tk.Tk()
root.title("お手軽翻訳ツール")
root.geometry("400x500")  # 縦長に変更
root.attributes("-topmost", True)
text_widget = tk.Text(root, wrap="word")
text_widget.pack(expand=True, fill="both")

# 設定ファイルを読み込む関数
def load_config():
    global config
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("設定ファイルを読み込みました")
            return config
        else:
            print(f"設定ファイルが見つかりません: {config_path}")
            # デフォルト設定を使用
            config = {
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
                    "window_width": 400,
                    "window_height": 500,
                    "always_on_top": True
                },
                "ocr": {
                    "languages": "eng+jpn",
                    "psm": 6
                }
            }
            return config
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
            }
        }

# 固定見出しの挿入
def update_heading():
    global config
    hotkey_text = ""
    if config and "hotkeys" in config and "capture" in config["hotkeys"]:
        capture_hotkey = config["hotkeys"]["capture"]
        modifiers = []
        if capture_hotkey.get("win", False):
            modifiers.append("Windows")
        if capture_hotkey.get("alt", False):
            modifiers.append("Alt")
        if capture_hotkey.get("shift", False):
            modifiers.append("Shift")
        key = capture_hotkey.get("key", "z").upper()
        hotkey_text = "+".join(modifiers) + "+" + key
    else:
        hotkey_text = "Windows+Alt+X"
    
    heading = (
        "【操作方法】\n"
        f"{hotkey_text} を押すと、現在のマウス座標を始点として記録し、\n"
        "キーを離すとその時点のマウス座標を対角線の終点として四角い範囲でキャプチャします。\n\n"
    )
    text_widget.delete("1.0", tk.END)
    text_widget.insert("1.0", heading)

def setup_tesseract_path(tesseract_path=None):
    global config
    if config and "tesseract" in config and "path" in config["tesseract"]:
        default_path = config["tesseract"]["path"]
    else:
        default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    tesseract_exe = tesseract_path or os.environ.get("TESSERACT_PATH", default_path)
    tesseract_exe = tesseract_exe.strip()
    if "esseract.exe" in tesseract_exe and "tesseract.exe" not in tesseract_exe:
        tesseract_exe = tesseract_exe.replace("esseract.exe", "tesseract.exe")
    if not os.path.exists(tesseract_exe):
        print(f"警告: Tesseract実行ファイルが見つかりません: {tesseract_exe}")
        print("Tesseract OCR をインストールしてください: https://github.com/UB-Mannheim/tesseract/wiki")
        alternative_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Tesseract-OCR\tesseract.exe",
        ]
        for alt_path in alternative_paths:
            if os.path.exists(alt_path):
                tesseract_exe = alt_path
                print(f"代替パスが見つかりました: {tesseract_exe}")
                break
    pytesseract.pytesseract.tesseract_cmd = tesseract_exe
    print(f"Tesseractパスを設定しました: {tesseract_exe}")
    try:
        test_img = np.zeros((50, 100), dtype=np.uint8)
        test_img.fill(255)
        pytesseract.image_to_string(test_img)
        print("Tesseract OCR が正常に動作しています")
    except Exception as e:
        print(f"Tesseract OCR のテストに失敗しました: {e}")
        print("アプリケーションは OCR 機能なしで動作します")

def preprocess_image(image):
    try:
        # ① アップスケーリング: 画像を 2 倍に拡大
        scale_factor = 2
        upscaled = cv2.resize(image, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
        
        # ② ノイズ除去: カラー画像に対して高速NlMeans ノイズ除去を適用
        denoised = cv2.fastNlMeansDenoisingColored(upscaled, None, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21)
        
        # ③ グレースケール変換
        gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
        
        # ④ AdaptiveThreshold による二値化
        processed = cv2.adaptiveThreshold(gray, 255,
                                          cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY, 11, 2)
        return processed
    except Exception as e:
        print("画像の前処理中にエラーが発生しました:", e)
        # エラー発生時は元の画像をそのまま返す（または None を返すなど）
        return image


def process_capture(x1, y1, x2, y2):
    global capture_count, config
    xmin, ymin = min(x1, x2), min(y1, y2)
    xmax, ymax = max(x1, x2), max(y1, y2)
    # キャプチャ範囲の画像を取得
    cap_img = ImageGrab.grab(bbox=(xmin, ymin, xmax, ymax))
    cap_img = np.array(cap_img)
    # 前処理実行
    processed = preprocess_image(cap_img)
    # OCR 実行
    ocr_config = f'--psm {config["ocr"]["psm"]}' if config and "ocr" in config and "psm" in config["ocr"] else '--psm 6'
    ocr_langs = config["ocr"]["languages"] if config and "ocr" in config and "languages" in config["ocr"] else 'eng+jpn'
    ocr_text = pytesseract.image_to_string(processed, lang=ocr_langs, config=ocr_config).strip()
    # 翻訳実行（TranslateClient を使用）
    client = TranslateClient()
    translated_text = client.translate(ocr_text)
    capture_count += 1
    result_text = (
        f"{capture_count}:\n【OCR結果】\n{ocr_text}\n\n【翻訳結果】\n{translated_text}\n\n"
    )
    root.after(0, update_text_widget, result_text)
    print(result_text)

def update_text_widget(text):
    text_widget.insert(tk.END, text)
    text_widget.see(tk.END)

def on_key_press(key):
    global is_shift_pressed, is_alt_pressed, is_win_pressed, capture_hotkey_active, capture_hotkey_start, config
    try:
        if key in [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r]:
            is_shift_pressed = True
        if key in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r]:
            is_alt_pressed = True
        if key == keyboard.Key.cmd:  # Windows/Super キー
            is_win_pressed = True
            
        # 設定ファイルからホットキー情報を取得
        capture_key = 'x'  # デフォルト
        need_shift = False
        need_alt = True
        need_win = True
        
        if config and "hotkeys" in config and "capture" in config["hotkeys"]:
            capture_hotkey = config["hotkeys"]["capture"]
            capture_key = capture_hotkey.get("key", "x").lower()
            need_shift = capture_hotkey.get("shift", False)
            need_alt = capture_hotkey.get("alt", True)
            need_win = capture_hotkey.get("win", True)
        
        # キーが設定されたキャプチャキーと一致するか確認
        if hasattr(key, 'char') and key.char is not None and key.char.lower() == capture_key:
            # 必要なモディファイアキーが押されているか確認
            if ((not need_shift or is_shift_pressed) and 
                (not need_alt or is_alt_pressed) and 
                (not need_win or is_win_pressed) and 
                not capture_hotkey_active):
                capture_hotkey_active = True
                capture_hotkey_start = mouse_controller.position
                print(f"Hotkey開始：始点 = {capture_hotkey_start}")
    except Exception as e:
        print(f"キー押下処理中にエラーが発生しました: {e}")

def on_key_release(key):
    global is_shift_pressed, is_alt_pressed, is_win_pressed, capture_hotkey_active, capture_hotkey_start, config
    try:
        if key in [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r]:
            is_shift_pressed = False
        if key in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r]:
            is_alt_pressed = False
        if key == keyboard.Key.cmd:  # Windows/Super キー
            is_win_pressed = False
            
        # 設定ファイルからホットキー情報を取得
        capture_key = 'x'  # デフォルト
        if config and "hotkeys" in config and "capture" in config["hotkeys"]:
            capture_key = config["hotkeys"]["capture"].get("key", "x").lower()
            
        if hasattr(key, 'char') and key.char is not None and key.char.lower() == capture_key:
            if capture_hotkey_active:
                capture_hotkey_active = False
                capture_end = mouse_controller.position
                print(f"Hotkey終了：終点 = {capture_end}")
                threading.Thread(target=process_capture, args=(
                    capture_hotkey_start[0], capture_hotkey_start[1],
                    capture_end[0], capture_end[1]), daemon=True).start()
    except Exception as e:
        print(f"キー解放処理中にエラーが発生しました: {e}")

def on_move(x, y):
    # この例ではホットキーの開始・終了のみでキャプチャするので、動的な描画は行いません。
    pass

def on_click(x, y, button, pressed):
    # ホットキー方式のため、クリックイベントは使用しません
    pass

def start_listeners():
    kb_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
    kb_listener.start()
    mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click)
    mouse_listener.start()

def main():
    global config
    config = load_config()
    setup_tesseract_path()
    update_heading()
    start_listeners()
    
    # UI設定を適用
    if config and "ui" in config:
        ui_config = config["ui"]
        if "window_width" in ui_config and "window_height" in ui_config:
            root.geometry(f"{ui_config['window_width']}x{ui_config['window_height']}")
        if "always_on_top" in ui_config:
            root.attributes("-topmost", ui_config["always_on_top"])
            
    root.mainloop()

if __name__ == "__main__":
    main()
