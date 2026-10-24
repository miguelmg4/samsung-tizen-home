using System;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;

internal static class HomeRouting
{
    private const string Operation = "http://tizen.org/appcontrol/operation/main";
    private const string Library = "/usr/lib/libcapi-appfw-app-operation-tv.so.0";
    private const string Stock = "com.samsung.tv.csfs";
    // Cualquier id de app Tizen válido (paquete de 10 caracteres + nombre); uno de los dos extremos debe ser el Home de Samsung.
    private static bool Known(string app) { return app == Stock || Regex.IsMatch(app, "^[A-Za-z0-9]{10}\\.[A-Za-z0-9]+$"); }

    private static string Current()
    {
        IntPtr value;
        int result = app_operation_get_current_app(Operation, out value);
        if (result != 0 || value == IntPtr.Zero)
            throw new InvalidOperationException("Read Home assignment failed: " + result);
        try { return Marshal.PtrToStringAnsi(value); }
        finally { free(value); }
    }

    public static int Main(string[] args)
    {
        try
        {
            if (args.Length != 0 &&
                (args.Length != 3 || args[0] != "set" || !Known(args[1]) || !Known(args[2]) || (args[1] != Stock && args[2] != Stock)))
                throw new ArgumentException("Usage: HomeRouting [set <expected-current> <target>]; one side must be " + Stock + ".");
            // The active TV owner's preferences live under UID 5001, not UID 0.
            if (setgroups(UIntPtr.Zero, IntPtr.Zero) != 0 || setgid(100) != 0 || setuid(5001) != 0)
                throw new InvalidOperationException("Cannot switch to the TV owner.");
            string before = Current();
            Console.WriteLine("uid=" + getuid() + " home=" + before);
            if (args.Length == 0) return 0;
            if (before != args[1])
                throw new InvalidOperationException("Home changed since the backup; refusing to overwrite " + before);
            if (before == args[2]) return 0;
            try
            {
                int result = app_operation_set_current_app(Operation, args[2]);
                if (result != 0)
                    throw new InvalidOperationException("Set Home assignment failed: " + result);
                string after = Current();
                if (after != args[2])
                    throw new InvalidOperationException("Home read-back mismatch: " + after);
                Console.WriteLine("verified home=" + after);
            }
            catch (Exception error)
            {
                int restored = app_operation_set_current_app(Operation, before);
                string actual = Current();
                Console.Error.WriteLine("Rollback result=" + restored + " home=" + actual);
                if (actual != before)
                    throw new InvalidOperationException(error.Message + "; rollback could not restore " + before);
                throw;
            }
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(error.Message);
            return 1;
        }
    }

    [DllImport(Library)] private static extern int app_operation_get_current_app(string operation, out IntPtr app);
    [DllImport(Library)] private static extern int app_operation_set_current_app(string operation, string app);
    [DllImport("libc")] private static extern void free(IntPtr value);
    [DllImport("libc")] private static extern int setuid(uint uid);
    [DllImport("libc")] private static extern int setgid(uint gid);
    [DllImport("libc")] private static extern int setgroups(UIntPtr count, IntPtr groups);
    [DllImport("libc")] private static extern uint getuid();
}
