#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ビルド前にモデルファイルとログファイルを一時的に移動するスクリプト
"""

import os
import shutil
import glob

def prepare_model_dir():
    """モデルディレクトリとログファイルを準備する"""
    # モデルディレクトリのパス
    model_dir = os.path.join(
        "translator_main", 
        "translator", 
        "server_client", 
        "model",
        "m2m100_418M"
    )
    
    # 一時保存用ディレクトリ
    temp_dir = "temp_model_backup"
    
    # モデルディレクトリが存在するか確認
    if os.path.exists(model_dir):
        print(f"モデルディレクトリが見つかりました: {model_dir}")
        
        # モデルファイルが存在するか確認
        model_files = glob.glob(os.path.join(model_dir, "*.*"))
        if model_files:
            print(f"{len(model_files)}個のモデルファイルが見つかりました")
            
            # 一時保存用ディレクトリを作成
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
                print(f"一時保存用ディレクトリを作成しました: {temp_dir}")
            
            # モデルファイルを一時保存用ディレクトリに移動
            for file_path in model_files:
                if os.path.basename(file_path) != "README.txt":
                    dest_path = os.path.join(temp_dir, os.path.basename(file_path))
                    shutil.move(file_path, dest_path)
                    print(f"ファイルを移動しました: {file_path} -> {dest_path}")
        else:
            print("モデルファイルは見つかりませんでした")
    
    # モデルディレクトリが存在しない場合は作成
    if not os.path.exists(model_dir):
        os.makedirs(model_dir, exist_ok=True)
        print(f"モデルディレクトリを作成しました: {model_dir}")
    
    # README.txtファイルを作成
    readme_path = os.path.join(model_dir, "README.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("このディレクトリには初回起動時に翻訳モデルがダウンロードされます。\n")
        f.write("This directory will be populated with translation model files on first launch.\n")
    
    print(f"README.txtファイルを作成しました: {readme_path}")
    
    # 翻訳ログファイルの処理
    handle_translation_logs(temp_dir)
    
    print("ビルド準備が完了しました")

def handle_translation_logs(temp_dir):
    """翻訳ログファイルを一時的に移動する"""
    logs_file = "translation_logs.json"
    
    # 翻訳ログファイルが存在するか確認
    if os.path.exists(logs_file):
        print(f"翻訳ログファイルが見つかりました: {logs_file}")
        
        # 一時保存用ディレクトリを作成（まだ存在しない場合）
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            print(f"一時保存用ディレクトリを作成しました: {temp_dir}")
        
        # ログファイルを一時保存用ディレクトリに移動
        dest_path = os.path.join(temp_dir, logs_file)
        shutil.move(logs_file, dest_path)
        print(f"ログファイルを移動しました: {logs_file} -> {dest_path}")
    else:
        print("翻訳ログファイルは見つかりませんでした")

def restore_model_files():
    """モデルファイルとログファイルを元に戻す"""
    # モデルディレクトリのパス
    model_dir = os.path.join(
        "translator_main", 
        "translator", 
        "server_client", 
        "model",
        "m2m100_418M"
    )
    
    # 一時保存用ディレクトリ
    temp_dir = "temp_model_backup"
    
    # 一時保存用ディレクトリが存在するか確認
    if os.path.exists(temp_dir):
        print(f"一時保存用ディレクトリが見つかりました: {temp_dir}")
        
        # 一時保存されたファイルが存在するか確認
        backup_files = glob.glob(os.path.join(temp_dir, "*.*"))
        if backup_files:
            print(f"{len(backup_files)}個のバックアップファイルが見つかりました")
            
            # モデルディレクトリが存在しない場合は作成
            if not os.path.exists(model_dir):
                os.makedirs(model_dir, exist_ok=True)
                print(f"モデルディレクトリを作成しました: {model_dir}")
            
            # バックアップファイルをモデルディレクトリに戻す
            for file_path in backup_files:
                base_name = os.path.basename(file_path)
                if base_name == "translation_logs.json":
                    # ログファイルはルートディレクトリに戻す
                    dest_path = base_name
                else:
                    # モデルファイルはモデルディレクトリに戻す
                    dest_path = os.path.join(model_dir, base_name)
                shutil.move(file_path, dest_path)
                print(f"ファイルを戻しました: {file_path} -> {dest_path}")
            
            # 一時保存用ディレクトリを削除
            shutil.rmtree(temp_dir)
            print(f"一時保存用ディレクトリを削除しました: {temp_dir}")
        else:
            print("バックアップファイルは見つかりませんでした")
    else:
        print("一時保存用ディレクトリが見つかりませんでした")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--restore":
        restore_model_files()
    else:
        prepare_model_dir()
