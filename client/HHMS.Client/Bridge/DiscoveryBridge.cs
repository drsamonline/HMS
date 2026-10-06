using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;

namespace HHMS.Client.Bridge;

public sealed class DiscoveryBridge
{
    private const string Request = "HHMS_DISCOVER_V1";
    private const int DiscoveryPort = 38541;
    private const int TimeoutMilliseconds = 1200;

    public async Task<DiscoveryResult?> DiscoverAsync(CancellationToken cancellationToken)
    {
        using var socket = new UdpClient(AddressFamily.InterNetwork);
        socket.EnableBroadcast = true;
        socket.Client.ReceiveTimeout = TimeoutMilliseconds;
        var payload = Encoding.UTF8.GetBytes(Request);
        await socket.SendAsync(payload, payload.Length, new IPEndPoint(IPAddress.Broadcast, DiscoveryPort));

        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(TimeoutMilliseconds);
        try
        {
            while (!timeout.IsCancellationRequested)
            {
                var receive = await socket.ReceiveAsync(timeout.Token);
                var json = Encoding.UTF8.GetString(receive.Buffer);
                var metadata = JsonSerializer.Deserialize<DiscoveryPayload>(json);
                if (metadata is null || metadata.Protocol != "hhms-lan-v1" || metadata.HttpPort <= 0)
                    continue;

                var baseUrl = $"http://{receive.RemoteEndPoint.Address}:{metadata.HttpPort}{metadata.ApiBase}";
                return new DiscoveryResult(baseUrl, metadata.Name, metadata.ServerId, metadata.Version);
            }
        }
        catch (OperationCanceledException)
        {
            // Expected on normal timeout/cancellation.
        }
        catch (SocketException)
        {
            // Network unavailable; caller will use manual fallback.
        }

        return null;
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
