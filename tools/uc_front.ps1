# Desktop session: Universal Control's window to the front, then the screen to uccap\front.png; with -Click X,Y
# (screen pixels) a left click there first (a double click with -Double), a second shot after
param([string]$Click = '', [switch]$Double, [int]$Wait = 2)
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class U { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint x, uint y, uint d, IntPtr e); }
'@
[U]::SetProcessDPIAware() | Out-Null
$p = Get-Process 'Universal Control'
if ($p.MainWindowHandle -ne 0) { [U]::ShowWindow($p.MainWindowHandle, 9) | Out-Null; [U]::SetForegroundWindow($p.MainWindowHandle) | Out-Null }
Start-Sleep 1
function Shot($n) { $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
  $g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
  $bmp.Save("$env:USERPROFILE\uccap\$n.png"); $g.Dispose(); $bmp.Dispose() }
if ($Click) {
  $x, $y = $Click.Split(',') | % { [int]$_ }
  [U]::SetCursorPos($x, $y); Start-Sleep -Milliseconds 200
  $n = if ($Double) { 2 } else { 1 }
  for ($i = 0; $i -lt $n; $i++) { [U]::mouse_event(2, 0, 0, 0, [IntPtr]::Zero); [U]::mouse_event(4, 0, 0, 0, [IntPtr]::Zero); Start-Sleep -Milliseconds 80 }
  Start-Sleep $Wait
}
Shot 'front'
