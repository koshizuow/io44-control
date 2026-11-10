io44-control（Windows）
========================

PreSonus Revelator io44 的控制程式，取代 Universal Control：混音、麥克風處理（Low Cut、EQ、Gate、
Compressor、Limiter、聲音效果）、reverb、取樣率，
io44 一接上就把你的設定寫回去，常駐在時鐘旁的通知區域。

開始使用
1. 把整個資料夾解壓縮到固定的位置，例如「文件\io44-control」。
2. 雙擊 io44-control.cmd。圖示會出現在右下角時鐘旁（Windows 11 會先收在 ^ 裡，可以拖到工作列上）。
3. 一次只能有一個程式控制 io44：在圖示上按右鍵，選「停用 Universal Control 的服務」，
   Windows 會詢問系統管理員權限。
4. 在圖示上按左鍵，開啟控制頁面（http://127.0.0.1:8794/）。第一次使用時從中性的設定開始
   （增益和監聽比例照 io44 現在的值，不開任何處理），再依需要調整。
5. 想要開機就常駐：在圖示上按右鍵，勾「開機時自動啟動」。

改回 Universal Control
- 在圖示上按右鍵，選「恢復 Universal Control 的服務」，再選「結束 io44-control」。
- 注意：Universal Control 的服務在某些重新啟動後會讓所有混音沒有聲音（它送出錯誤的 reverb 係數）。
  遇到時重開電腦，再在 Universal Control 切換一次取樣率。

安全
- 48V 幻象電源只在你在頁面上打開時送出，每次都會先問。鋁帶麥克風和真空管麥克風不要開 48V。
- io44-control 送出前會檢查每個數值，不會送出無效的數值。

其他
- 設定存在 %APPDATA%\io44-control（state.json），記錄檔 io44-control.log 也在那裡。
- 取樣率透過 io44 的驅動程式設定，需要裝過 Universal Control（驅動程式隨它安裝）。
- 授權：licenses 資料夾（libusb：LGPL-2.1，未修改；Python：PSF License）。


io44-control (Windows), in short
--------------------------------
1. Unzip the folder somewhere to keep, double-click io44-control.cmd: the icon goes next to the clock (under ^ on
   Windows 11 at first).
2. Right-click it, "停用 Universal Control 的服務" (stop Universal Control's service; an administrator prompt):
   only one program can control the io44.
3. Left-click it for the page (http://127.0.0.1:8794/); the settings start neutral (the gains and the blend as the
   io44 has them, no processing).
4. Right-click, "開機時自動啟動" to start with Windows. To go back: "恢復 Universal Control 的服務", then quit.
48V is sent only when you turn it on in the page (asked each time): not for ribbon or tube mics.
