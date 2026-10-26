using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

internal static class PrototypeLauncher
{
    [STAThread]
    private static void Main()
    {
        try
        {
            string applicationRoot = @"__APPLICATION_ROOT__";
            string pythonPath = @"__PYTHON_PATH__";
            if (!File.Exists(pythonPath) || !File.Exists(Path.Combine(applicationRoot, "run_prototype.py")))
            {
                MessageBox.Show("실행 파일 또는 프로젝트 폴더가 이동되었습니다. 바탕화면 실행파일 만들기를 다시 실행해 주세요.", "AX 나침반", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            ProcessStartInfo start = new ProcessStartInfo();
            start.FileName = pythonPath;
            start.Arguments = "-X utf8 \"" + Path.Combine(applicationRoot, "run_prototype.py") + "\"";
            start.WorkingDirectory = applicationRoot;
            start.UseShellExecute = false;
            start.CreateNoWindow = true;
            start.WindowStyle = ProcessWindowStyle.Hidden;
            Process.Start(start);
        }
        catch
        {
            MessageBox.Show("프로그램을 시작하지 못했습니다. 프로젝트의 실행 안내를 확인해 주세요.", "AX 나침반", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}
