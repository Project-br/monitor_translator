import cv2
import numpy as np
import pytesseract
import os
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
capture_count = 0  # OCR キャプチャの連番
capture_hotkey_active = False
capture_hotkey_start = None
mouse_controller = MouseController()

# Tkinter ウィンドウ（OCR 結果表示用）
root = tk.Tk()
root.title("お手軽翻訳ツール")
root.geometry("400x500")  # 縦長に変更
root.attributes("-topmost", True)
text_widget = tk.Text(root, wrap="word")
text_widget.pack(expand=True, fill="both")

# 固定見出しの挿入
heading = (
    "【操作方法】\n"
    "Shift+Alt+Z を押すと、現在のマウス座標を始点として記録し、\n"
    "キーを離すとその時点のマウス座標を対角線の終点として四角い範囲でキャプチャします。\n\n"
)
text_widget.insert("1.0", heading)

def setup_tesseract_path(tesseract_path=None):
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
    global capture_count
    xmin, ymin = min(x1, x2), min(y1, y2)
    xmax, ymax = max(x1, x2), max(y1, y2)
    # キャプチャ範囲の画像を取得
    cap_img = ImageGrab.grab(bbox=(xmin, ymin, xmax, ymax))
    cap_img = np.array(cap_img)
    # 前処理実行
    processed = preprocess_image(cap_img)
    # OCR 実行
    config = '--psm 6'
    ocr_text = pytesseract.image_to_string(processed, lang='eng+jpn', config=config).strip()
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
    global is_shift_pressed, is_alt_pressed, capture_hotkey_active, capture_hotkey_start
    try:
        if key in [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r]:
            is_shift_pressed = True
        if key in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r]:
            is_alt_pressed = True
        # キーが 'z'（大文字小文字問わず）ならキャプチャ開始
        if hasattr(key, 'char') and key.char is not None and key.char.lower() == 'z':
            if is_shift_pressed and is_alt_pressed and not capture_hotkey_active:
                capture_hotkey_active = True
                capture_hotkey_start = mouse_controller.position
                print(f"Hotkey開始：始点 = {capture_hotkey_start}")
    except Exception:
        pass

def on_key_release(key):
    global is_shift_pressed, is_alt_pressed, capture_hotkey_active, capture_hotkey_start
    try:
        if key in [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r]:
            is_shift_pressed = False
        if key in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r]:
            is_alt_pressed = False
        if hasattr(key, 'char') and key.char is not None and key.char.lower() == 'z':
            if capture_hotkey_active:
                capture_hotkey_active = False
                capture_end = mouse_controller.position
                print(f"Hotkey終了：終点 = {capture_end}")
                threading.Thread(target=process_capture, args=(
                    capture_hotkey_start[0], capture_hotkey_start[1],
                    capture_end[0], capture_end[1]), daemon=True).start()
    except Exception:
        pass

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
    setup_tesseract_path()
    start_listeners()
    root.mainloop()

if __name__ == "__main__":
    main()
