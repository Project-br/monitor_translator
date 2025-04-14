#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
翻訳ツール起動スクリプト

このスクリプトは翻訳サーバーを別プロセスで起動し、
その後にモニター翻訳ツールを起動します。
"""

import os
import sys
import subprocess
import time
import signal
import atexit
import platform
import requests

# グローバル変数として翻訳サーバープロセスを保持
server_process = None

def get_project_root():
    """
    プロジェクトのルートディレクトリを取得します。
    """
    # このスクリプトの場所を基準にルートディレクトリを特定
    return os.path.dirname(os.path.abspath(__file__))

def get_python_executable():
    """
    適切なPython実行ファイルを取得します。
    仮想環境内で実行されている場合はその環境のPythonを使用します。
    """
    # 仮想環境内で実行されている場合
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        if platform.system() == 'Windows':
            return os.path.join(sys.prefix, 'Scripts', 'python.exe')
        else:
            return os.path.join(sys.prefix, 'bin', 'python')
    else:
        # 仮想環境外の場合は現在のPython実行ファイルを使用
        return sys.executable

def cleanup_server():
    """
    翻訳サーバープロセスをクリーンアップする関数
    """
    global server_process
    if server_process:
        print("翻訳サーバーを終了しています...")
        try:
            if platform.system() == 'Windows':
                # Windowsの場合はTASKKILLを使用
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(server_process.pid)], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Unix系の場合はシグナルを送信
                os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
                server_process.wait(timeout=5)  # 最大5秒待機
        except Exception as e:
            print(f"サーバー終了中にエラーが発生しました: {e}")
        finally:
            server_process = None
            print("翻訳サーバーを終了しました")

def start_translation_server():
    """
    翻訳サーバーを起動する関数
    
    戻り値:
        subprocess.Popen: 起動したサーバープロセス
    """
    global server_process
    
    # 既存のサーバープロセスをクリーンアップ
    cleanup_server()
    
    print("翻訳サーバーを起動しています...")
    
    # 現在の実行ファイルのディレクトリを取得
    current_dir = get_project_root()
    
    # PyInstallerでパッケージ化されているかどうかを確認
    is_packaged = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
    
    # 翻訳サーバースクリプトのパスを構築
    if is_packaged:
        # パッケージ化されている場合は、_MEIPASSディレクトリからの相対パスを使用
        base_dir = sys._MEIPASS
        server_script = os.path.join(
            base_dir, 
            "translator_main", 
            "translator", 
            "server_client", 
            "translate_server_run.py"
        )
    else:
        # 通常実行の場合
        server_script = os.path.join(
            current_dir, 
            "translator_main", 
            "translator", 
            "server_client", 
            "translate_server_run.py"
        )
    
    # スクリプトが存在するか確認
    if not os.path.exists(server_script):
        print(f"エラー: 翻訳サーバースクリプトが見つかりません: {server_script}")
        return None
    
    # Pythonインタープリターのパスを取得
    python_exe = get_python_executable()
    
    # サーバーをバックグラウンドで起動
    try:
        # パッケージ化されている場合
        if is_packaged:
            # 現在の実行ファイル自体をサーバーモードで起動
            exe_path = sys.executable
            
            # 環境変数を設定してサーバーモードで起動
            env = os.environ.copy()
            env['ENJAPP_SERVER_MODE'] = '1'
            
            if platform.system() == 'Windows':
                server_process = subprocess.Popen(
                    [exe_path, "--server"],
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            else:
                # Unix系OSの場合
                server_process = subprocess.Popen(
                    [exe_path, "--server"],
                    preexec_fn=os.setsid,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
        else:
            # 通常の実行（パッケージ化されていない場合）
            # 新しいプロセスグループで起動（Windows対応）
            if platform.system() == 'Windows':
                server_process = subprocess.Popen(
                    [python_exe, server_script],
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            else:
                # Unix系OSの場合
                server_process = subprocess.Popen(
                    [python_exe, server_script],
                    preexec_fn=os.setsid,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
        
        # サーバーの起動を確認するために待機
        print("サーバーの起動を確認しています...")
        max_retries = 60  # 無制限に近い値に設定（60回のリトライ）
        retry_interval = 2  # 秒
        server_ready = False
        
        for i in range(max_retries):
            # プロセスが終了していないか確認
            if server_process.poll() is not None:
                print("エラー: 翻訳サーバーの起動に失敗しました")
                return None
                
            # サーバーが応答するか確認
            try:
                response = requests.get("http://127.0.0.1:11451/docs", timeout=5)  # タイムアウトを5秒に増加
                if response.status_code == 200:
                    server_ready = True
                    break
            except requests.RequestException:
                pass
                
            print(f"サーバー起動待機中... ({i+1}/{max_retries})")
            time.sleep(retry_interval)
            
        if not server_ready:
            print("警告: サーバーの応答を確認できませんでしたが、プロセスは実行中です")
        
        print(f"翻訳サーバープロセスが開始されました (PID: {server_process.pid})")
        
        # プログラム終了時にサーバーをクリーンアップするように登録
        atexit.register(cleanup_server)
        
        return server_process
        
    except Exception as e:
        print(f"サーバー起動中にエラーが発生しました: {e}")
        return None

def start_monitor_translator():
    """
    モニター翻訳ツールを起動する関数
    
    戻り値:
        int: 終了コード
    """
    print("モニター翻訳ツールを起動しています...")
    
    # PyInstallerでパッケージ化されているかどうかを確認
    is_packaged = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
    
    # 現在の実行ファイルのディレクトリを取得
    current_dir = get_project_root()
    
    # 翻訳モニタースクリプトのパスを構築
    # PyQt5版のGUIを使用する場合
    use_pyqt = True  # PyQt5版を使用するフラグ
    
    if is_packaged:
        # パッケージ化されている場合は、直接モジュールをインポートして実行
        try:
            print("パッケージ化された環境でGUIを起動します...")
            from translator_main.translator.gui.qt_translator import main as qt_main
            # GUIをメインスレッドで実行
            return qt_main()
        except ImportError as e:
            print(f"GUIモジュールのインポートに失敗しました: {e}")
            # パスを調整して再試行
            base_dir = sys._MEIPASS
            sys.path.append(base_dir)
            try:
                from translator_main.translator.gui.qt_translator import main as qt_main
                return qt_main()
            except ImportError as e2:
                print(f"調整後もGUIモジュールのインポートに失敗しました: {e2}")
                return 1
        except Exception as e:
            print(f"GUI起動中に予期しないエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            return 1
    else:
        # 通常実行の場合
        if use_pyqt:
            translator_script = os.path.join(
                current_dir, 
                "translator_main", 
                "translator", 
                "gui",
                "qt_translator.py"
            )
        else:
            # 従来のtkinter版
            translator_script = os.path.join(
                current_dir, 
                "translator_main", 
                "translator", 
                "translator.py"
            )
        
        # スクリプトが存在するか確認
        if not os.path.exists(translator_script):
            print(f"エラー: 翻訳モニタースクリプトが見つかりません: {translator_script}")
            return 1
        
        # 翻訳モニターを現在のプロセスで実行（制御を移す）
        translator_process = subprocess.run([sys.executable, translator_script])
        
        return translator_process.returncode

def main():
    """
    メイン実行関数
    """
    # コマンドライン引数を解析
    import argparse
    parser = argparse.ArgumentParser(description='ENJAPP 翻訳ツール')
    parser.add_argument('--server', action='store_true', help='サーバーモードで起動')
    args = parser.parse_args()
    
    # サーバーモードで起動する場合
    if args.server or os.environ.get('ENJAPP_SERVER_MODE') == '1':
        print("サーバーモードで起動します...")
        try:
            from translator_main.translator.server_client.translate_server_run import start_server
            start_server()
        except ImportError as e:
            print(f"サーバーモジュールのインポートに失敗しました: {e}")
            # パッケージ化されている場合のパスを調整
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                base_dir = sys._MEIPASS
                sys.path.append(base_dir)
                try:
                    from translator_main.translator.server_client.translate_server_run import start_server
                    start_server()
                except ImportError as e2:
                    print(f"調整後もサーバーモジュールのインポートに失敗しました: {e2}")
                    sys.exit(1)
            else:
                sys.exit(1)
        except Exception as e:
            print(f"サーバー起動中に予期しないエラーが発生しました: {e}")
            sys.exit(1)
        return
    
    try:
        # 翻訳サーバーをバックグラウンドで起動
        server_proc = start_translation_server()
        
        # サーバーが起動に失敗した場合
        if server_proc is None:
            print("エラー: 翻訳サーバーの起動に失敗しました")
            sys.exit(1)
            
        print("翻訳サーバーが起動しました。モニター翻訳ツールを起動します...")
        
        # モニター翻訳ツールを起動
        exit_code = start_monitor_translator()
        
        # 翻訳モニターの終了コードを返す
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nプログラムが中断されました")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 明示的にサーバープロセスをクリーンアップ
        cleanup_server()

if __name__ == "__main__":
    main()