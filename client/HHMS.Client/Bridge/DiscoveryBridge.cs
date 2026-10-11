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
    private const int RoundTimeoutMilliseconds = 900;

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

        using var socket = new UdpClient(AddressFamily.InterNetwork);
        socket.EnableBroadcast = true;
        socket.Client.ReceiveTimeout = RoundTimeoutMilliseconds;
        var payload = Encoding.UTF8.GetBytes(Request);

        using var round = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        round.CancelAfter(RoundTimeoutMilliseconds);
        try
        {
            // Fire one probe per target, then collect replies until the round
            // deadline. Duplicate probes are harmless; the first valid reply wins.
            foreach (var target in targets.DistinctBy(t => t.Address))
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

            while (!round.IsCancellationRequested)
            {
                try
                {
                    var receive = await socket.ReceiveAsync(round.Token);
                    var json = Encoding.UTF8.GetString(receive.Buffer);
                    var metadata = JsonSerializer.Deserialize<DiscoveryPayload>(json);
                    if (metadata is null || metadata.Protocol != "hhms-lan-v1" || metadata.HttpPort <= 0)
                        continue;

                    var baseUrl = $"http://{receive.RemoteEndPoint.Address}:{metadata.HttpPort}{metadata.ApiBase}";
                    return new DiscoveryResult(baseUrl, metadata.Name, metadata.ServerId, metadata.Version);
                }
                catch (OperationCanceledException)
                {
                    break; // Round deadline reached.
                }
                catch (SocketException)
                {
                    break; // Network unavailable; caller will use manual fallback.
                }
            }
        }
        catch (OperationCanceledException)
        {
            // Expected on normal timeout/cancellation.
        }

        return null;
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
