# sban-midi-tool
 
暗号をMIDIに変換したり、MIDIを暗号に変換したりできるツール


## SBANMidi
このパッケージ用のMIDIオブジェクト。
通常のMIDIでは「ノートの始まり」や「ノートの終わり」を1メッセージとするが、
このオブジェクトではノートを1メッセージとする。
また、テンポやトラック名などの細かい機能を廃止している。

## メソッド
### save
MIDIファイルとして保存する。
### to_morse
SBANMidiをモールス信号に変換(つまり解読)
### to_image
SBANMidiを画像に変換して出力する。
ファイル名は日付になる。
### to_gif
SBAMidiをGIFに変換して出力する。
100BPM固定。
### reverse
MIDIを破壊的に反転する。

## 関数
### from_number
数字をSBANMidiに変換する。
### from_morse
モールス文をSBANMidiに変換する。
### from_tenji
点字テキストをSBANMidiに変換する。