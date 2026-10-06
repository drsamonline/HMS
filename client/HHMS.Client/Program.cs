using System;
using System.Windows.Forms;

namespace HHMS.Client;

internal static class Program
{
    /// <summary>
    /// Client release version. Kept in lock-step with the repository-root
    /// VERSION file; test_batch108 asserts the two never drift.
    /// </summary>
    public const string Version = "0.0.1";

    [STAThread]
    private static void Main()
    {
        ApplicationConfiguration.Initialize();
        Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
        Application.ThreadException += (_, args) => MessageBox.Show(
            args.Exception.Message,
            "HHMS Client Error",
            MessageBoxButtons.OK,
            MessageBoxIcon.Error);

        Application.Run(new MainForm());
    }
}
