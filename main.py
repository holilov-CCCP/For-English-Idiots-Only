import json
import threading
import time
import pyautogui
import pyperclip
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from googletrans import Translator
import http.server
import socketserver
import os
from urllib.parse import urlparse, parse_qs
import tkinter as tk
from tkinter import ttk  # ttkモジュールをインポート
import queue
import sys

# Windowsの場合のみctypesをインポート（クリックスルー機能用）
if sys.platform == "win32":
    import ctypes

# 対応言語リスト (主要な25言語 + α)
# Googletransがサポートする言語コードに基づいています
LANGUAGES = {
    'Arabic': 'ar', 'Chinese (Simplified)': 'zh-cn', 'Chinese (Traditional)': 'zh-tw',
    'Czech': 'cs', 'Danish': 'da', 'Dutch': 'nl', 'English': 'en', 'Finnish': 'fi',
    'French': 'fr', 'German': 'de', 'Greek': 'el', 'Hindi': 'hi', 'Hungarian': 'hu',
    'Indonesian': 'id', 'Italian': 'it', 'Japanese': 'ja', 'Korean': 'ko',
    'Norwegian': 'no', 'Polish': 'pl', 'Portuguese': 'pt', 'Russian': 'ru',
    'Spanish': 'es', 'Swedish': 'sv', 'Thai': 'th', 'Turkish': 'tr', 'Vietnamese': 'vi'
}

# デフォルト設定
default_config = {
    "chrome_path": "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "source_language": "en",  # 翻訳元言語
    "target_language": "ja",  # 翻訳先言語
    "translation_retry": {
        "max_retries": 1,
        "retry_delay_seconds": 0.5
    },
    "interim_to_final_conditions": {
        "min_length": 2,
        "max_wait_time": 0.8,
        "sentence_break_threshold": 0.4
    },
    "update_interval": 0.1,
    "enable_periodic_update": False,
    "compact_mode": {
        "width": 400,
        "height": 300,
        "position_x": 0,
        "position_y": "center",
        "transparency": 0.7,
        "click_through": True,
        "display_source_in_compact": False
    }
}

# --- 設定GUIクラス ---
class SettingsGUI:
    """設定を編集するためのGUIウィンドウ"""
    def __init__(self, current_config):
        self.config = current_config
        self.root = tk.Tk()
        self.root.title("設定")

        # ウィンドウを中央に配置
        window_width = 450
        window_height = 420
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # タブ付きインターフェース
        notebook = ttk.Notebook(main_frame)
        notebook.pack(expand=True, fill=tk.BOTH, pady=5)

        # --- 言語設定タブ ---
        lang_frame = ttk.Frame(notebook, padding="10")
        notebook.add(lang_frame, text='言語設定')
        self.create_lang_tab(lang_frame)

        # --- コンパクトモード設定タブ ---
        compact_frame = ttk.Frame(notebook, padding="10")
        notebook.add(compact_frame, text='コンパクトモード設定')
        self.create_compact_tab(compact_frame)
        
        # 保存ボタン
        save_button = ttk.Button(main_frame, text="保存して開始", command=self.save_and_close)
        save_button.pack(pady=10)


    def create_lang_tab(self, parent_frame):
        # 翻訳元言語
        ttk.Label(parent_frame, text="話す言語（翻訳元）:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.source_lang_var = tk.StringVar()
        source_combo = ttk.Combobox(parent_frame, textvariable=self.source_lang_var, state="readonly")
        
        # 翻訳先言語
        ttk.Label(parent_frame, text="翻訳先の言語:").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.target_lang_var = tk.StringVar()
        target_combo = ttk.Combobox(parent_frame, textvariable=self.target_lang_var, state="readonly")

        # ドロップダウンリストの設定
        lang_names = list(LANGUAGES.keys())
        source_combo['values'] = lang_names
        target_combo['values'] = lang_names
        
        # 現在の設定値を表示
        try:
            current_source_name = list(LANGUAGES.keys())[list(LANGUAGES.values()).index(self.config["source_language"])]
            self.source_lang_var.set(current_source_name)
        except (ValueError, KeyError):
            self.source_lang_var.set('English')

        try:
            current_target_name = list(LANGUAGES.keys())[list(LANGUAGES.values()).index(self.config["target_language"])]
            self.target_lang_var.set(current_target_name)
        except (ValueError, KeyError):
            self.target_lang_var.set('Japanese')

        source_combo.grid(row=0, column=1, sticky=(tk.W, tk.E))
        target_combo.grid(row=1, column=1, sticky=(tk.W, tk.E))
        
        parent_frame.columnconfigure(1, weight=1)

    def _update_transparency_label(self, value):
        percent = int(float(value) * 100)
        self.transparency_label.config(text=f"{percent}%")

    def create_compact_tab(self, parent_frame):
        # compact_modeの設定が存在しない場合のフォールバック
        compact_conf = self.config.setdefault('compact_mode', default_config['compact_mode'])

        # 変数を初期化
        self.display_source_var = tk.BooleanVar(value=compact_conf.get('display_source_in_compact', False))
        self.width_var = tk.StringVar(value=str(compact_conf.get('width', 400)))
        self.height_var = tk.StringVar(value=str(compact_conf.get('height', 300)))
        self.transparency_var = tk.DoubleVar(value=compact_conf.get('transparency', 0.7))
        self.click_through_var = tk.BooleanVar(value=compact_conf.get('click_through', True))

        # UI要素を作成・配置
        ttk.Checkbutton(parent_frame, text="文字起こし(原文)も表示する", variable=self.display_source_var).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=8)
        
        ttk.Label(parent_frame, text="ウィンドウ幅:").grid(row=1, column=0, sticky=tk.W, pady=8)
        ttk.Entry(parent_frame, textvariable=self.width_var, width=10).grid(row=1, column=1, columnspan=2, sticky=tk.W)
        
        ttk.Label(parent_frame, text="ウィンドウ高さ:").grid(row=2, column=0, sticky=tk.W, pady=8)
        ttk.Entry(parent_frame, textvariable=self.height_var, width=10).grid(row=2, column=1, columnspan=2, sticky=tk.W)
        
        ttk.Label(parent_frame, text="透明度:").grid(row=3, column=0, sticky=tk.W, pady=8)
        transparency_frame = ttk.Frame(parent_frame)
        transparency_frame.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E))
        
        scale = ttk.Scale(transparency_frame, from_=0.1, to=1.0, orient=tk.HORIZONTAL, variable=self.transparency_var, command=self._update_transparency_label)
        scale.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.transparency_label = ttk.Label(transparency_frame, text=f"{int(self.transparency_var.get() * 100)}%", width=5)
        self.transparency_label.pack(side=tk.LEFT, padx=(5, 0))

        ttk.Checkbutton(parent_frame, text="クリックスルーを有効にする (Windowsのみ)", variable=self.click_through_var).grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=8)
        
        parent_frame.columnconfigure(1, weight=1)

    def save_and_close(self):
        # --- 言語設定の保存 ---
        source_lang_name = self.source_lang_var.get()
        target_lang_name = self.target_lang_var.get()

        if source_lang_name in LANGUAGES and target_lang_name in LANGUAGES:
            self.config["source_language"] = LANGUAGES[source_lang_name]
            self.config["target_language"] = LANGUAGES[target_lang_name]
        else:
            print("エラー: 無効な言語が選択されました。")
            return

        # --- コンパクトモード設定の保存 ---
        if 'compact_mode' not in self.config:
            self.config['compact_mode'] = {}
        
        self.config['compact_mode']['display_source_in_compact'] = self.display_source_var.get()
        try:
            self.config['compact_mode']['width'] = int(self.width_var.get())
            self.config['compact_mode']['height'] = int(self.height_var.get())
        except ValueError:
            print("警告: 幅と高さは整数で入力してください。デフォルト値を使用します。")
            # 不正な値の場合はデフォルト値に戻す
            self.config['compact_mode']['width'] = default_config['compact_mode']['width']
            self.config['compact_mode']['height'] = default_config['compact_mode']['height']
        self.config['compact_mode']['transparency'] = round(self.transparency_var.get(), 2)
        self.config['compact_mode']['click_through'] = self.click_through_var.get()
            
        # config.jsonに保存
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        
        print(f"設定を保存しました。")
        self.root.destroy()


    def run(self):
        self.root.mainloop()

# --- メインアプリケーションロジック ---

# 設定ファイルの読み込み（なければデフォルトを使用）
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    # 不足しているキーをデフォルト設定で再帰的に補完
    def merge_configs(default, current):
        for key, value in default.items():
            if key not in current:
                current[key] = value
            elif isinstance(value, dict):
                merge_configs(value, current.setdefault(key, {}))
    merge_configs(default_config, config)
except FileNotFoundError:
    config = default_config
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# --- 設定GUIを起動 ---
settings_gui = SettingsGUI(config)
settings_gui.run()
# GUIが閉じられた後、更新されたconfigが使われる

# 設定をグローバル変数に反映
chrome_path = config['chrome_path']
port = 7777
conditions = config['interim_to_final_conditions']
update_interval = config['update_interval']
enable_periodic_update = config['enable_periodic_update']
compact_config = config.get('compact_mode')
source_language = config['source_language']
target_language = config['target_language']
translation_retry_config = config.get('translation_retry')
max_retries = translation_retry_config.get('max_retries', 1)
retry_delay = translation_retry_config.get('retry_delay_seconds', 0.5)


# 翻訳器の初期化
translator = Translator()

# グローバル変数
confirmed_texts = []
translated_texts = []
current_interim = ""
last_final_text = ""
last_interim_time = 0
interim_history = []
driver = None # [変更] driverをグローバル変数として初期化

# コンパクトモード関連のグローバル変数
compact_window = None
is_compact_mode = False
text_queue = queue.Queue() # 翻訳テキストをTkinterスレッドに渡すキュー

class CompactWindow:
    """コンパクトモード用のオーバーレイウィンドウを管理するクラス"""
    def __init__(self, root):
        self.root = root
        self.click_through_applied = False
        self.setup_window()

    def setup_window(self):
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', compact_config.get('transparency', 0.7))
        self.root.configure(bg='black')

        self.text_widget = tk.Text(
            self.root, bg='black', fg='white', font=('Arial', 14),
            wrap=tk.WORD, borderwidth=0, highlightthickness=0, insertbackground='black'
        )
        self.text_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        self.text_widget.tag_configure("bold", font=('Arial', 14, 'bold'))
        self.text_widget.tag_configure("source", foreground="#999999", font=('Arial', 11))
        self.text_widget.tag_configure("bold_source", foreground="#cccccc", font=('Arial', 11, 'bold'))

        self.text_widget.config(state='disabled')
        self.position_window()
        self.hide()

    def position_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = compact_config.get('width', 400)
        height = compact_config.get('height', 300)
        pos_x_config = compact_config.get('position_x', 0)
        if isinstance(pos_x_config, str):
            if pos_x_config == 'left': x = 0
            elif pos_x_config == 'right': x = screen_width - width
            else: x = (screen_width - width) // 2
        else: x = pos_x_config
        pos_y_config = compact_config.get('position_y', 'center')
        if isinstance(pos_y_config, str):
            if pos_y_config == 'top': y = 0
            elif pos_y_config == 'bottom': y = screen_height - height
            else: y = (screen_height - height) // 2
        else: y = pos_y_config
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def set_click_through(self):
        if sys.platform != "win32":
            print("クリックスルーはWindowsでのみサポートされています。")
            return
        try:
            hwnd = int(self.root.wm_frame(), 16)
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            WS_EX_LAYERED = 0x00080000; WS_EX_TRANSPARENT = 0x00000020
            new_style = style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, new_style)
        except Exception as e:
            print(f"クリックスルー設定エラー: {e}")

    def update_text(self, source_texts, translated_texts):
        self.text_widget.config(state='normal')
        self.text_widget.delete('1.0', tk.END)

        display_source = compact_config.get('display_source_in_compact', False)
        num_items = len(translated_texts)

        if num_items == 0:
            self.text_widget.config(state='disabled')
            return

        # 表示件数を最後の5件に制限
        start_index = max(0, num_items - 5)
        display_sources = source_texts[start_index:]
        display_translations = translated_texts[start_index:]

        # 最後のペア以外を通常表示
        for i in range(len(display_translations) - 1):
            if display_source and i < len(display_sources):
                self.text_widget.insert(tk.END, f"{display_sources[i]}\n", "source")
            self.text_widget.insert(tk.END, f"{display_translations[i]}\n\n")

        # 最後のペアを太字で表示
        if display_translations:
            last_source = display_sources[-1] if display_sources and len(display_sources) == len(display_translations) else ""
            last_translation = display_translations[-1]
            if display_source and last_source:
                self.text_widget.insert(tk.END, f"{last_source}\n", ("source", "bold_source"))
            self.text_widget.insert(tk.END, last_translation, "bold")

        self.text_widget.see(tk.END)
        self.text_widget.config(state='disabled')

    def show(self):
        if not self.click_through_applied and compact_config.get('click_through', True):
            self.root.update_idletasks()
            self.set_click_through()
            self.click_through_applied = True
        self.root.deiconify()

    def hide(self):
        self.root.withdraw()

def run_tkinter():
    global compact_window
    root = tk.Tk()
    compact_window = CompactWindow(root)
    def check_queue():
        try:
            source_texts, translated_texts = text_queue.get_nowait()
            compact_window.update_text(source_texts, translated_texts)
        except queue.Empty:
            pass
        root.after(100, check_queue)
    check_queue()
    root.mainloop()

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global is_compact_mode, compact_window
        # [変更] 終了処理を即時実行するように修正
        if self.path == '/quit':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Application is shutting down.')
            print("終了リクエスト受信。アプリケーションを即時終了します。")
            
            def immediate_shutdown():
                global driver
                try:
                    if driver:
                        driver.quit()  # まずブラウザを閉じる
                except Exception as e:
                    print(f"ドライバーの終了中にエラーが発生: {e}")
                finally:
                    os._exit(0) # プロセスを強制終了
            
            # 終了処理を別スレッドで実行して、HTTPレスポンスを確実に返す
            threading.Thread(target=immediate_shutdown).start()
            return
            
        if self.path == '/toggle_compact_mode':
            is_compact_mode = not is_compact_mode
            if compact_window:
                if is_compact_mode:
                    compact_window.show(); print("コンパクトモード ON")
                else:
                    compact_window.hide(); print("コンパクトモード OFF")
            self.send_response(200); self.send_header('Content-type', 'text/plain'); self.end_headers(); self.wfile.write(b'OK')
            return
        if self.path.startswith('/update'):
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            if 'type' in params and 'text' in params:
                global current_interim, last_final_text, last_interim_time
                text = params['text'][0].strip()
                current_time = time.time()
                if params['type'][0] == 'final':
                    if text and text != last_final_text:
                        if text not in confirmed_texts[-5:]:
                            confirmed_texts.append(text)
                            last_final_text = text
                            print(f"新規確定: {text}")
                            translate_and_store(text)
                        current_interim = ""; last_interim_time = 0
                elif params['type'][0] == 'interim':
                    if text and text != last_final_text:
                        current_interim = text; last_interim_time = current_time
            self.send_response(200); self.send_header('Content-type', 'text/plain'); self.end_headers(); self.wfile.write(b'OK')
            return
        elif self.path.startswith('/get_translations'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response_data = {'translations': translated_texts}
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            return
        else:
            if self.path == '/':
                self.path = '/index.html'
            if self.path == '/index.html':
                 # HTMLコンテンツを動的に生成
                try:
                    source_lang_name = list(LANGUAGES.keys())[list(LANGUAGES.values()).index(source_language)]
                    target_lang_name = list(LANGUAGES.keys())[list(LANGUAGES.values()).index(target_language)]
                except ValueError:
                    source_lang_name = "Source"
                    target_lang_name = "Target"

                # プレースホルダーを置換
                final_html = html_content.replace("{{SOURCE_LANG_CODE}}", source_language)
                final_html = final_html.replace("{{SOURCE_LANG_NAME}}", source_lang_name)
                final_html = final_html.replace("{{TARGET_LANG_NAME}}", target_lang_name)
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(final_html.encode('utf-8'))
            else:
                super().do_GET() # 他のファイルは通常通り提供

    def log_message(self, format, *args):
        pass

def translate_and_store(text):
    """確定テキストを翻訳して保存し、コンパクトウィンドウに通知。エラー時はリトライする。"""
    for attempt in range(max_retries + 1):
        try:
            # 設定ファイルから読み込んだ言語コードを使用
            translated = translator.translate(text, src=source_language, dest=target_language)
            translated_texts.append(translated.text)
            print(f"翻訳完了: {text} -> {translated.text}")
            text_queue.put((list(confirmed_texts), list(translated_texts)))
            return
        except Exception as e:
            print(f"翻訳エラー (試行 {attempt + 1}/{max_retries + 1}): {e}")
            if attempt < max_retries:
                print(f"{retry_delay}秒後に再試行します...")
                time.sleep(retry_delay)
            else:
                # 最終試行でも失敗した場合
                error_msg = f"翻訳エラー: {str(e)}"
                translated_texts.append(error_msg)
                print(f"最終的な翻訳エラー: {text} -> {error_msg}")
                text_queue.put((list(confirmed_texts), list(translated_texts)))

def check_interim_conditions():
    """暫定テキストが古くなっていたらクリアする関数"""
    global current_interim, last_interim_time
    if current_interim and last_interim_time > 0:
        time_since_last_update = time.time() - last_interim_time
        if time_since_last_update > 1.5:
            print(f"古い暫定テキストをクリア: {current_interim}")
            current_interim = ""; last_interim_time = 0

def run_server():
    with socketserver.TCPServer(("", port), MyHttpRequestHandler) as httpd:
        print(f"サーバーをポート {port} で起動しました")
        httpd.serve_forever()

# HTMLコンテンツ
html_content = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Speech Recognition with Translation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #333; }
        .button-container { display: flex; justify-content: center; gap: 10px; margin: 20px 0; }
        .button-container button { padding: 15px 30px; font-size: 16px; color: white; border: none; border-radius: 5px; cursor: pointer; }
        #startButton { background: #007bff; } #startButton:hover { background: #0056b3; }
        #compactModeButton { background: #6c757d; } #compactModeButton:hover { background: #5a6268; }
        #quitButton { background: #dc3545; } #quitButton:hover { background: #c82333; }
        #status { text-align: center; margin: 10px 0; padding: 10px; border-radius: 5px; font-weight: bold; }
        .status-active { background: #d4edda; color: #155724; }
        .status-inactive { background: #f8d7da; color: #721c24; }
        .content-area { display: flex; gap: 20px; margin-top: 20px; }
        .text-box { flex: 1; padding: 15px; border: 1px solid #ddd; border-radius: 5px; min-height: 400px; background: #fafafa; }
        .text-box h3 { margin-top: 0; margin-bottom: 15px; color: #333; font-size: 18px; border-bottom: 2px solid #007bff; padding-bottom: 5px; }
        .interim-text { color: #dc3545; font-weight: bold; font-style: italic; margin-bottom: 10px; padding: 8px; background: #ffe6e6; border-left: 4px solid #dc3545; border-radius: 3px; }
        .final-text { color: #333; margin-bottom: 8px; padding: 8px; border-left: 4px solid #28a745; background: #f8fff8; border-radius: 3px; line-height: 1.4; }
        .translation-text { color: #333; margin-bottom: 8px; padding: 8px; border-left: 4px solid #17a2b8; background: #e6f9ff; border-radius: 3px; line-height: 1.4; font-family: 'Meiryo UI', 'Yu Gothic', sans-serif; }
    </style>
</head>
<body>
    <div class="container">
        <h1>音声認識・翻訳システム</h1>
        <div class="button-container">
            <button id="startButton">音声認識開始</button>
            <button id="compactModeButton">コンパクトモード</button>
            <button id="quitButton">アプリを終了</button>
        </div>
        <div id="status" class="status-inactive">状態: 停止中</div>
        <div class="content-area">
            <div class="text-box english-box">
                <h3>🗣️ {{SOURCE_LANG_NAME}} Text</h3>
                <div id="englishOutput"></div>
            </div>
            <div class="text-box japanese-box">
                <h3>🌐 {{TARGET_LANG_NAME}} Translation</h3>
                <div id="japaneseOutput"></div>
            </div>
        </div>
    </div>
    <script>
        const startButton = document.getElementById('startButton');
        const compactModeButton = document.getElementById('compactModeButton');
        const quitButton = document.getElementById('quitButton');
        const statusDiv = document.getElementById('status');
        const englishOutput = document.getElementById('englishOutput');
        const japaneseOutput = document.getElementById('japaneseOutput');
        let recognition;
        let isRecognizing = false;
        let lastFinalText = "";
        let finalTexts = [];
        let lastTranslationCount = 0;
        
        function updateEnglishDisplay(interimText, newFinalText) {
            let html = '';
            if (interimText) {
                html += `<div class="interim-text">📝 ${interimText}</div>`;
            }
            if (newFinalText && newFinalText !== lastFinalText) {
                finalTexts.unshift(newFinalText);
                lastFinalText = newFinalText;
                if (finalTexts.length > 15) {
                    finalTexts = finalTexts.slice(0, 15);
                }
            }
            finalTexts.forEach((text) => {
                if (text.trim()) { html += `<div class="final-text text-item">✅ ${text}</div>`; }
            });
            englishOutput.innerHTML = html;
        }
        
        function updateJapaneseDisplay() {
            fetch('/get_translations').then(response => response.json()).then(data => {
                if (data.translations && data.translations.length > lastTranslationCount) {
                    let html = '';
                    const reversedTranslations = [...data.translations].reverse();
                    reversedTranslations.forEach((translation) => {
                        if (translation.trim()) { html += `<div class="translation-text text-item">🈳 ${translation}</div>`; }
                    });
                    japaneseOutput.innerHTML = html;
                    lastTranslationCount = data.translations.length;
                }
            }).catch(err => console.error('翻訳取得エラー:', err));
        }
        
        if ('webkitSpeechRecognition' in window) {
            recognition = new webkitSpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = '{{SOURCE_LANG_CODE}}';
            
            recognition.onresult = function(event) {
                let interimText = ""; let finalText = "";
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript.trim();
                    if (event.results[i].isFinal) { finalText += transcript + " "; } else { interimText += transcript; }
                }
                finalText = finalText.trim(); interimText = interimText.trim();
                
                if (finalText && finalText !== lastFinalText) {
                    fetch('/update?type=final&text=' + encodeURIComponent(finalText))
                        .then(() => setTimeout(updateJapaneseDisplay, 100))
                        .catch(err => console.error('送信エラー:', err));
                }
                if (interimText) {
                    fetch('/update?type=interim&text=' + encodeURIComponent(interimText))
                        .catch(err => console.error('送信エラー:', err));
                }
                updateEnglishDisplay(interimText, finalText);
            };
            
            recognition.onerror = function(event) {
                console.error('音声認識エラー:', event.error);
                statusDiv.textContent = '状態: エラー - ' + event.error;
                statusDiv.className = 'status-inactive';
            };
            
            recognition.onend = function() { if (isRecognizing) { setTimeout(() => { if (isRecognizing) recognition.start(); }, 100); } };
            recognition.onstart = function() { statusDiv.textContent = '状態: 認識中'; statusDiv.className = 'status-active'; };
            setInterval(() => { if (isRecognizing) { updateJapaneseDisplay(); } }, 500);
            
            startButton.addEventListener('click', () => {
                if (!isRecognizing) {
                    recognition.start(); startButton.textContent = '認識停止'; isRecognizing = true;
                } else {
                    recognition.stop(); startButton.textContent = '音声認識開始';
                    statusDiv.textContent = '状態: 停止中'; statusDiv.className = 'status-inactive';
                    isRecognizing = false;
                }
            });

            compactModeButton.addEventListener('click', () => { fetch('/toggle_compact_mode').catch(err => console.error('コンパクトモード切替エラー:', err)); });
            
            quitButton.addEventListener('click', () => {
                fetch('/quit').catch(err => console.error('終了リクエストエラー:', err));
                quitButton.textContent = '終了中...';
                quitButton.disabled = true;
            });

        } else { englishOutput.innerHTML = 'お使いのブラウザは音声認識をサポートしていません'; }
    </script>
</body>
</html>"""

# --- Main execution part ---

# Tkinterスレッドを開始 (コンパクトウィンドウ用)
tkinter_thread = threading.Thread(target=run_tkinter, daemon=True)
tkinter_thread.start()

# Webサーバーと条件チェッカーのスレッドを開始
server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(1)

checker_thread = threading.Thread(target=check_interim_conditions, daemon=True)
checker_thread.start()

# SeleniumでChromeを起動
chrome_options = Options()
chrome_options.binary_location = chrome_path
chrome_options.add_argument(f"--app=http://localhost:{port}")
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

print("Chromeを起動します...")
try:
    # [変更] driverをグローバル変数に代入
    driver = webdriver.Chrome(options=chrome_options)
    print("Chrome起動完了")
except Exception as e:
    print(f"Chrome起動エラー: {e}")
    print("ChromeDriverが正しくインストールされているか確認してください")
    # driver起動に失敗したらスクリプトを終了
    sys.exit(1)

try:
    print("システム起動完了。GUIの終了ボタンでアプリを終了してください。")
    # os._exit() で終了するため、メインスレッドはここで待機
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    # Ctrl+Cで終了した場合の処理
    print("\nキーボード割り込みにより終了します...")
finally:
    try:
        if driver:
            driver.quit()
    except:
        pass
    print("アプリケーションを終了しました。")