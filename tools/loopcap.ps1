# loopcap.ps1 SECONDS PORTS OUT.pcap : the IPv4 packets on 127.0.0.1 to or from any of PORTS (comma list; TCP and
# UDP), as a pcap (raw IP).
# The RawCap way: a raw socket bound to the loopback address with SIO_RCVALL. Needs an administrator.
param([int]$Seconds = 20, [string]$Port = "49670", [string]$Out = "$env:USERPROFILE\uccap\uc.pcap")
Add-Type -TypeDefinition @'
using System; using System.IO; using System.Net; using System.Net.Sockets;
public static class LoopCap {
  public static int Run(int seconds, string ports, string path) {
    var want = new System.Collections.Generic.HashSet<int>(); foreach (var x in ports.Split(',')) want.Add(int.Parse(x));
    var s = new Socket(AddressFamily.InterNetwork, SocketType.Raw, ProtocolType.IP);
    s.Bind(new IPEndPoint(IPAddress.Loopback, 0));
    s.SetSocketOption(SocketOptionLevel.IP, SocketOptionName.HeaderIncluded, true);
    s.IOControl(IOControlCode.ReceiveAll, new byte[] {1, 0, 0, 0}, new byte[4]);
    s.ReceiveTimeout = 500;
    var buf = new byte[65536]; int n = 0;
    using (var f = new BinaryWriter(File.Create(path))) {
      f.Write(0xa1b2c3d4u); f.Write((ushort)2); f.Write((ushort)4); f.Write(0); f.Write(0u); f.Write(65535u); f.Write(101u);
      var end = DateTime.UtcNow.AddSeconds(seconds);
      while (DateTime.UtcNow < end) {
        int k;
        try { k = s.Receive(buf); } catch (SocketException) { continue; }
        if (k < 20 || (buf[9] != 6 && buf[9] != 17)) continue;
        int ihl = (buf[0] & 15) * 4;
        int sp = (buf[ihl] << 8) | buf[ihl + 1], dp = (buf[ihl + 2] << 8) | buf[ihl + 3];
        if (!want.Contains(sp) && !want.Contains(dp)) continue;
        var t = DateTime.UtcNow - new DateTime(1970, 1, 1);
        f.Write((uint)t.TotalSeconds); f.Write((uint)((t.Ticks % 10000000) / 10));
        f.Write((uint)k); f.Write((uint)k); f.Write(buf, 0, k); n++;
      }
    }
    s.Close();
    return n;
  }
}
'@
"packets: " + [LoopCap]::Run($Seconds, $Port, $Out)
