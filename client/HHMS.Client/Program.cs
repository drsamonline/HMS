using System;
using System.Windows.Forms;

namespace HHMS.Client;

internal static class Program
{
    /// <summary>
    /// Client release version. Kept in lock-step with the repository-root
    /// VERSION file; test_batch108 asserts the two never drift.
    /// </summary>
    // Kept in step with the root VERSION file, which is the source of truth. The
    // backend regression suite asserts these two match - `client Program.Version
    // drifted from root VERSION` - and it was right: the root moved to 0.0.2 and this
    // constant did not, so HMS/release.yml has been failing on every run.
    public const string Version = "0.0.2";

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
