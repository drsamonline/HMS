using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;
using System.Text.Json;
using HHMS.Client.Bridge;

namespace HHMS.Client;

public sealed class MainForm : Form
{
    private readonly WebView2 _webView = new() { Dock = DockStyle.Fill };
    private readonly DiscoveryBridge _discovery = new();

    public MainForm()
    {
        Text = "HHMS";
        Width = 1280;
        Height = 800;
        StartPosition = FormStartPosition.CenterScreen;
        Controls.Add(_webView);
        Load += MainForm_Load;
    }

    private async void MainForm_Load(object? sender, EventArgs e)
    {
        try
        {
            await _webView.EnsureCoreWebView2Async();
            _webView.CoreWebView2.WebMessageReceived += WebMessageReceived;
            _webView.CoreWebView2.Settings.AreDevToolsEnabled = false;
            _webView.CoreWebView2.Settings.AreDefaultContextMenusEnabled = false;
            _webView.CoreWebView2.NavigationCompleted += (_, _) => InjectBridge();

            var frontend = Path.GetFullPath(
                Path.Combine(AppContext.BaseDirectory, "frontend", "index.html"));
            if (!File.Exists(frontend))
                throw new FileNotFoundException("HHMS frontend index.html was not found.", frontend);

            _webView.CoreWebView2.Navigate(new Uri(frontend).AbsoluteUri);
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "HHMS Client Startup Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            Close();
        }
    }

    private async void InjectBridge()
    {
        const string script = """
            window.hhms = window.hhms || {};
            window.hhms.discovery = window.hhms.discovery || {};
            window.hhms.discovery.discover = () => {
                const requestId = crypto.randomUUID();
                return new Promise((resolve, reject) => {
                    window.__hhmsDiscoveryPending = window.__hhmsDiscoveryPending || new Map();
                    window.__hhmsDiscoveryPending.set(requestId, { resolve, reject });
                    window.chrome.webview.postMessage(JSON.stringify({ type: 'discover', requestId }));
                });
            };
            window.__hhmsResolveDiscovery = (message) => {
                const pending = window.__hhmsDiscoveryPending?.get(message.requestId);
                if (!pending) return;
                window.__hhmsDiscoveryPending.delete(message.requestId);
                if (message.ok) pending.resolve(message.result);
                else pending.reject(new Error(message.error || 'LAN discovery failed.'));
            };
            """;
        await _webView.CoreWebView2.AddScriptToExecuteOnDocumentCreatedAsync(script);
    }

    private async void WebMessageReceived(object? sender, CoreWebView2WebMessageReceivedEventArgs e)
    {
        try
        {
            var message = JsonSerializer.Deserialize<BridgeRequest>(e.TryGetWebMessageAsString());
            if (message?.Type != "discover" || string.IsNullOrWhiteSpace(message.RequestId)) return;

            var result = await _discovery.DiscoverAsync(CancellationToken.None);
            var response = JsonSerializer.Serialize(new
            {
                requestId = message.RequestId,
                ok = result is not null,
                result,
                error = result is null ? "HHMS server was not found on the LAN." : null,
            });
            await _webView.CoreWebView2.ExecuteScriptAsync(
                $"window.__hhmsResolveDiscovery({JsonSerializer.Serialize(response)});");
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "HHMS Client Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private sealed record BridgeRequest(string? Type, string? RequestId);
}
