using System;
using System.Windows.Forms;

namespace HHMS.Client;

internal static class Program
{
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
