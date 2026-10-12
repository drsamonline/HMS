using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;

namespace HHMS.Client.Bridge;

public sealed class DiscoveryBridge
{
    private const string Request = "HHMS_DISCOVER_V1";
    // Must match the server default DISCOVERY_PORT in backend/app/config/settings.py.
    private const int DiscoveryPort = 38541;
    private const int RoundTimeoutMilliseconds = 1200;
    // Two extra rounds after the first so a server that is still booting,
    // or a Wi-Fi adapter that drops the very first broadcast, still gets
    // several chances.  Worst case ~3.6s total, which the UI shows as
    // "Searching…".
    private const int MaxRounds = 3;

    public async Task<DiscoveryResult?> DiscoverAsync(CancellationToken cancellationToken)
    {
        // Probe every IPv4 interface: global broadcast (255.255.255.255), the
        // interface-directed broadcast, and the subnet directed broadcast.
        // On wireless LANs the AP often drops the global broadcast, but the
        // per-interface/subnet-directed probes still reach servers that bind
        // 0.0.0.0 UDP on that Wi-Fi adapter. This also covers multi-SSID or
        // Ethernet+Wi-Fi machines where the server sits behind another NIC.
        var targets = new List<IPEndPoint>();
        foreach (var address in LocalIPv4Addresses())
        {
            try
            {
                uint raw = BitConverter.ToUInt32(address.GetAddressBytes(), 0);
                uint mask = GetSubnetMaskRaw(address);
                var directed = new IPAddress(raw | ~mask); // subnet-directed broadcast
                targets.Add(new IPEndPoint(directed, DiscoveryPort));
            }
            catch
            {
                // Skip interfaces whose mask cannot be resolved.
            }
        }
        targets.Add(new IPEndPoint(IPAddress.Broadcast, DiscoveryPort));
        // Same-machine fallback: when server and client run on one PC and the
        // Wi-Fi adapter is AP-isolated (or Windows Firewall blocks inbound
        // broadcast), UDP broadcasts never loop back to the sender.  A direct
        // unicast probe to 127.0.0.1 always reaches a server bound to
        // 0.0.0.0, so local auto-discovery works with zero configuration.
        targets.Add(new IPEndPoint(IPAddress.Loopback, DiscoveryPort));

        using var socket = new UdpClient(AddressFamily.InterNetwork);
        socket.EnableBroadcast = true;
        socket.Client.ReceiveTimeout = RoundTimeoutMilliseconds;
        var payload = Encoding.UTF8.GetBytes(Request);
        var distinctTargets = targets.DistinctBy(t => t.Address).ToList();

        try
        {
            // Repeat broadcast rounds until a reply arrives or the caller
            // cancels.  A single round is unreliable on real hardware: Wi-Fi
            // drivers drop the first broadcast, and the server may still be
            // booting when the client opens.  Each round fires one probe per
            // target (unicast loopback included) and collects replies until
            // the round deadline; duplicates are harmless — first valid wins.
            for (var round = 0; round < MaxRounds && !cancellationToken.IsCancellationRequested; round++)
            {
                foreach (var target in distinctTargets)
                {
                    try
                    {
                        await socket.SendAsync(payload, payload.Length, target, CancellationToken.None);
                    }
                    catch (SocketException)
                    {
                        // Interface may not support broadcast; keep probing others.
                    }
                }

                using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
                deadline.CancelAfter(RoundTimeoutMilliseconds);
                while (!deadline.IsCancellationRequested)
                {
                    try
                    {
                        var receive = await socket.ReceiveAsync(deadline.Token);
                        var json = Encoding.UTF8.GetString(receive.Buffer);
                        var metadata = JsonSerializer.Deserialize<DiscoveryPayload>(json);
                        if (metadata is null || metadata.Protocol != "hhms-lan-v1" || metadata.HttpPort <= 0)
                            continue;

                        var baseUrl = BuildBaseUrl(receive.RemoteEndPoint.Address, metadata);
                        return new DiscoveryResult(baseUrl, metadata.Name, metadata.ServerId, metadata.Version);
                    }
                    catch (OperationCanceledException)
                    {
                        break; // Round deadline reached; start the next round.
                    }
                    catch (SocketException)
                    {
                        break; // Network unavailable; caller will use manual fallback.
                    }
                }
            }
        }
        catch (OperationCanceledException)
        {
            // Expected on normal timeout/cancellation.
        }

        return null;
    }

    private static string BuildBaseUrl(IPAddress replySource, DiscoveryPayload metadata)
    {
        // Prefer the LAN address the operator can actually reach: if the
        // reply came from our own loopback probe but the machine has a real
        // IPv4 address, advertise that instead so saved URLs survive the
        // "localhost works but phones don't" confusion.  When no LAN
        // address exists (server truly local-only), keep the loopback.
        var host = replySource;
        if (IPAddress.IsLoopback(replySource))
        {
            host = LocalIPv4Addresses()
                .FirstOrDefault(a => !a.IsIPv6LinkLocal && !IPAddress.IsLoopback(a)) ?? replySource;
        }
        return $"http://{host}:{metadata.HttpPort}{metadata.ApiBase}";
    }

    private static IEnumerable<IPAddress> LocalIPv4Addresses()
    {
        try
        {
            return NetworkInterface.GetAllNetworkInterfaces()
                .Where(ni => ni.OperationalStatus == OperationalStatus.Up &&
                             ni.NetworkInterfaceType != NetworkInterfaceType.Loopback)
                .SelectMany(ni => ni.GetIPProperties().UnicastAddresses)
                .Select(ua => ua.Address)
                .Where(a => a.AddressFamily == AddressFamily.InterNetwork);
        }
        catch
        {
            return Array.Empty<IPAddress>();
        }
    }

    private static uint GetSubnetMaskRaw(IPAddress address)
    {
        foreach (var ni in NetworkInterface.GetAllNetworkInterfaces())
        {
            foreach (var ua in ni.GetIPProperties().UnicastAddresses)
            {
                if (ua.Address.Equals(address))
                {
                    var maskBytes = ua.IPv4Mask.GetAddressBytes();
                    return BitConverter.ToUInt32(maskBytes, 0);
                }
            }
        }
        throw new InvalidOperationException("No subnet mask for address.");
    }

    private sealed record DiscoveryPayload(
        string Protocol,
        string Name,
        string ServerId,
        string Version,
        int HttpPort,
        string ApiBase);
}

public sealed record DiscoveryResult(string BaseUrl, string Name, string ServerId, string Version);
