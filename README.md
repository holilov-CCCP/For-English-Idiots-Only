# For-English-Idiots-Only
英語ができないバカ(私を含む)用に作成された、完全ソースコード公開の無料のゲームに特化したボイスチャット翻訳ツール

# 概要
「日本語以外が全く分からない!! だけど、過疎った日本サーバーから逃げて海外サーバーでボイスチャットをしながらゲームをしたい!!」

という、傲慢で腹立たしい勉強をする気もないアホ(私を含む)の同志のために作成されたボイスチャット翻訳ツールです。

全然言葉はわからなくて聞き取れないのに意味はわかるという不思議な現象を体験できます。

これを使えば海外の知らないSquadプレイヤーから「指示したんだからさっさと動けよ。mother f**k!」と言われることも無くなります。多分

要約すると、"海外プレイヤーからのボイスチャットを文字起こしし、それを日本語に翻訳してゲームの画面に表示させるツール"です。(最初からそう言えよ)

# 機能

- Chromeを使った高精度な音声認識/文字起こし
- Google翻訳を使用した即時の翻訳
- 主要25言語に対応
- ゲーム画面の好きなところに翻訳結果と英文を表示
- 多様な設定項目
- わかりやすいGUI
- 自分の言葉を翻訳して音声で相手に伝える

その他いっぱい(?)...

# スクリーンショット

設定画面1 

![alt text](1.png)


設定画面2 

![alt text](2.png)


操作GUI 

![alt text](3.png)

コンパクトモードのGUI 

![alt text](4.png)

# 使用方法

以下の前提要件をクリア後、基本的には`main.exe`を実行すればokです。「これウイルスだろw」とかいう用心深い天才さんはmain.pyを使ってください。機能は同じです

# 前提要件

- Windows (必須?)
> Linux,MACでの動作確認はしておりません。MAC民は滅べ

- 2つ以上の仮想オーディオケーブルがある (必須)
> 私は "VB-Audio Cable" と "YAMAHA SYNC ROOM2" という2つの無料ツールを使用しています。

- "Google Chrome"インストール済 (必須)
> 音声認識を使用するためにGoogleChromeが必要です

- "Microsoft Edge"インストール済 (必須)
> 普通のwindowsなら標準で入ってます

- "Voice Meeter BANANA"をインストール済(推奨)
> ほぼ必須です。無くてもいいですが、ここではインストール済を仮定して説明します。

DLリンク: 
VB-Audio Cable      https://vb-audio.com/Cable/
YAMAHA SYNC ROOM2   https://syncroom.yamaha.com/v2/play/dl/
Voice Meeter BANANA https://vb-audio.com/Voicemeeter/banana.htm
Microsoft edge      https://www.microsoft.com/ja-jp/edge/download
Google Chrome       https://www.google.com/intl/ja/chrome/


# 初期設定

1.サウンド設定を変更する
> "設定">"サウンド設定">"サウンドの詳細設定"を開きます。
> "再生"タブに行き、"Voice Meeter input"を"通信の既定値/オーディオの既定値"に設定します。音が聞こえなくなりますが、正常なので安心してください。
> "録音"タブに行き、普段使っているマイクを"通信の既定値/オーディオの既定値"に設定します。
> 設定したら"OK"を押して閉じてください。

2.Voice Meeter BANANAを設定する
> "VoiceMeeter BANANA x64"というアプリを開いてください。
> 左の"HARDWARE OUT"というところの、"A1"という所をクリックし、"WDM"から普段使っている出力デバイスを選択してください。設定したら閉じてください。
> "A1"の隣の"A2"をクリックし、"WDM"から"VB-Audio Cable"を選択してください。設定したら閉じてください。
> "VIRTUAL INPUT" というところの右下にあるところから、"A1","A2"を選択してくだい。これで音声を聞くことができます。

3.Chromeの設定を変更する
> Chromeを開き、"設定">"プライバシーとセキュリティ">"サイトの設定">"マイク"から、"CABLE Output (VB-Audio Virtual Cable)"を選択してください。設定したら閉じてください。

4.Edgeの設定を変更する
> マイクの設定をあなたの普段使っているマイクに変更してください。

5.ゲーム側(DiscordやFPSゲームなど)の設定
> マイク設定でマイクを"ライン (Yamaha SYNCROOM Driver)"に設定してください。これで、相手にあなたの言語を翻訳したメッセージが伝わります。

6.main.exe(main.py)の設定を変更する
> main.exe(main.py)を開き、設定GUIから"音声設定"を開き、"出力先1"に普段使っている出力デバイスを、"出力先2"に"ライン (Yamaha SYNC Driver)"を設定して、横の"有効"にチェックを入れてください。
> "GUI1 言語設定"というタブに行き、"話す言語 (翻訳元) - GUI1"に相手ユーザーが話す言語を設定してください。"翻訳先言語 - GUI1"に、あなたの理解できる言語を設定してください。
> "GUI2 言語設定"というタブに行き、"話す言語 (翻訳元) - GUI2"にあなたの話す言語を設定してください。"翻訳先の言語 - GUI2"に相手ユーザーの理解できる言語を設定してください。

```
1:   Desktop(他)   →   【既定値】Voicemeeter Input(出)   →   VB-Audio Cable(出)   →   VB-Audio Cable(入)   →   Chrome(他)                 → GUI表示
2:   Desktop(他)   →   【既定値】Voicemeeter Input(出)   →   Headphone(出),Speaker(出)
3:   Voice(他)     →   【既定値】Microphone(入)          →   edge(他)             →   Python Script(他)    →   Yamaha SYNCROOM Driver(出) → Yamaha SYNCROOM Driver(入)   → Voice chat
4:   Voice(他)     →   【既定値】Microphone(入)          →   edge(他)             →   Python Script(他)    →   Headphone(出),Speaker(出)
```

これで初期設定は終了です。いろいろいじって使ってみてください。
