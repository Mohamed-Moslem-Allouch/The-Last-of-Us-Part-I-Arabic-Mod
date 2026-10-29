using System;
using System.IO;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Windows.Forms;
using System.Diagnostics;
using System.Reflection;

[assembly: AssemblyTitle("The Last of Us Part I - Arabic Localization Mod Installer")]
[assembly: AssemblyDescription("Pure Native Arabic Localization Mod Installer & Game Engine Patcher for The Last of Us Part I (PC)")]
[assembly: AssemblyCompany("Mohamed Moslem Allouch")]
[assembly: AssemblyProduct("The Last of Us Part I Arabic Localization Mod")]
[assembly: AssemblyCopyright("Copyright © 2026 Mohamed Moslem Allouch. All rights reserved.")]
[assembly: AssemblyVersion("1.0.0.0")]
[assembly: AssemblyFileVersion("1.0.0.0")]

namespace TLOUArabicInstaller {
    class Program {
        const string VERSION = "1.0.0";
        const string AUTHOR = "Mohamed Moslem Allouch";

        [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        static extern IntPtr LoadLibrary(string libname);

        [DllImport("kernel32.dll", CharSet = CharSet.Ansi, ExactSpelling = true, SetLastError = true)]
        static extern IntPtr GetProcAddress(IntPtr hModule, string procName);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        delegate long OodleCompressDelegate(
            int codec, byte[] rawBuf, long rawLen, byte[] compBuf, int level,
            IntPtr p1, IntPtr p2, IntPtr p3, IntPtr p4, long p5
        );

        static OodleCompressDelegate OodleCompress;

        static void InitOodle(string oodleDllPath) {
            IntPtr hModule = LoadLibrary(oodleDllPath);
            if (hModule == IntPtr.Zero) throw new FileNotFoundException("Cannot load Oodle library from: " + oodleDllPath);
            IntPtr pProc = GetProcAddress(hModule, "OodleLZ_Compress");
            if (pProc == IntPtr.Zero) throw new EntryPointNotFoundException("OodleLZ_Compress export not found in " + oodleDllPath);
            OodleCompress = (OodleCompressDelegate)Marshal.GetDelegateForFunctionPointer(pProc, typeof(OodleCompressDelegate));
        }

        [STAThread]
        static void Main(string[] args) {
            Console.OutputEncoding = Encoding.UTF8;
            Console.Title = "The Last of Us Part I - Arabic Localization Installer (by Mohamed Moslem Allouch)";

            PrintBanner();

            string appDir = AppDomain.CurrentDomain.BaseDirectory;
            string modDataDir = Path.Combine(appDir, "mod_data");
            if (!Directory.Exists(modDataDir)) {
                // Check if running from tools directory or parent
                DirectoryInfo parentDir = Directory.GetParent(appDir);
                string parentModData = (parentDir != null) ? Path.Combine(parentDir.FullName, "mod_data") : "";
                if (!string.IsNullOrEmpty(parentModData) && Directory.Exists(parentModData)) {
                    modDataDir = parentModData;
                } else {
                    Console.ForegroundColor = ConsoleColor.Red;
                    Console.WriteLine("[-] ERROR: 'mod_data' folder not found!");
                    Console.WriteLine("    Please make sure 'mod_data' folder is extracted alongside this installer.");
                    Console.ResetColor();
                    Console.WriteLine("\nPress any key to exit...");
                    Console.ReadKey();
                    return;
                }
            }

            string gameDir = FindGameDirectory();
            if (string.IsNullOrEmpty(gameDir)) {
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine("[!] Game directory could not be detected automatically.");
                Console.WriteLine("[*] Opening folder selector window...");
                Console.ResetColor();
                gameDir = BrowseGameDirectory();
            }

            if (string.IsNullOrEmpty(gameDir)) {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("[-] Installation aborted. Game directory not found.");
                Console.ResetColor();
                Console.WriteLine("\nPress any key to exit...");
                Console.ReadKey();
                return;
            }

            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine("[+] Game detected at: " + gameDir);
            Console.ResetColor();
            Console.WriteLine();
            Console.WriteLine("Please choose an option:");
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("  [1] Install Arabic Localization Mod");
            Console.ForegroundColor = ConsoleColor.Yellow;
            Console.WriteLine("  [2] Uninstall Mod (Restore Original Files)");
            Console.ForegroundColor = ConsoleColor.Gray;
            Console.WriteLine("  [3] Exit");
            Console.ResetColor();
            Console.WriteLine();
            Console.Write("Enter your choice [1-3]: ");

            string input = Console.ReadLine();
            string choice = (input != null) ? input.Trim() : "";
            if (choice == "2") {
                RunUninstall(gameDir);
            } else if (choice == "1") {
                RunInstall(gameDir, modDataDir);
            } else {
                Console.WriteLine("Exiting.");
            }
        }

        static void PrintBanner() {
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("================================================================================");
            Console.ForegroundColor = ConsoleColor.Yellow;
            Console.WriteLine("   THE LAST OF US PART I - ARABIC LOCALIZATION MOD INSTALLER");
            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine("   Created by: " + AUTHOR);
            Console.ForegroundColor = ConsoleColor.White;
            Console.WriteLine("   Nexus Mods Edition - Version " + VERSION);
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("================================================================================");
            Console.ResetColor();
            Console.WriteLine();
        }

        static string FindGameDirectory() {
            string currentDir = AppDomain.CurrentDomain.BaseDirectory;
            DirectoryInfo parent = Directory.GetParent(currentDir);
            string parentPath = (parent != null) ? parent.FullName : "";

            List<string> candidates = new List<string>();
            candidates.Add(currentDir);
            if (!string.IsNullOrEmpty(parentPath)) candidates.Add(parentPath);
            candidates.Add(@"D:\The Last of Us");
            candidates.Add(@"C:\Games\The Last of Us Part I");
            candidates.Add(@"D:\Games\The Last of Us Part I");
            candidates.Add(@"E:\Games\The Last of Us Part I");
            candidates.Add(@"C:\Program Files (x86)\Steam\steamapps\common\The Last of Us Part I");
            candidates.Add(@"D:\SteamLibrary\steamapps\common\The Last of Us Part I");
            candidates.Add(@"E:\SteamLibrary\steamapps\common\The Last of Us Part I");
            candidates.Add(@"F:\SteamLibrary\steamapps\common\The Last of Us Part I");

            foreach (string c in candidates) {
                if (string.IsNullOrEmpty(c) || !Directory.Exists(c)) continue;
                string exe = Path.Combine(c, "tlou-i.exe");
                string psarc = Path.Combine(c, "build", "pc", "main", "core.psarc");
                if (File.Exists(exe) && File.Exists(psarc)) {
                    return Path.GetFullPath(c);
                }
            }
            return null;
        }

        static string BrowseGameDirectory() {
            try {
                using (FolderBrowserDialog dlg = new FolderBrowserDialog()) {
                    dlg.Description = "Select 'The Last of Us Part I' Game Directory (where tlou-i.exe is located)";
                    dlg.ShowNewFolderButton = false;
                    if (dlg.ShowDialog() == DialogResult.OK) {
                        string sel = dlg.SelectedPath;
                        string exe = Path.Combine(sel, "tlou-i.exe");
                        string psarc = Path.Combine(sel, "build", "pc", "main", "core.psarc");
                        if (File.Exists(exe) && File.Exists(psarc)) {
                            return sel;
                        } else {
                            Console.ForegroundColor = ConsoleColor.Red;
                            Console.WriteLine("[-] 'tlou-i.exe' or 'build/pc/main/core.psarc' not found in selected directory!");
                            Console.ResetColor();
                        }
                    }
                }
            } catch (Exception ex) {
                Console.WriteLine("[!] Folder browser error: " + ex.Message);
            }
            return null;
        }

        static void RunUninstall(string gameDir) {
            Console.WriteLine("\n" + new string('=', 72));
            Console.ForegroundColor = ConsoleColor.Yellow;
            Console.WriteLine("   UNINSTALLING ARABIC LOCALIZATION MOD");
            Console.ResetColor();
            Console.WriteLine(new string('=', 72));

            string exePath = Path.Combine(gameDir, "tlou-i.exe");
            string exeBak = Path.Combine(gameDir, "tlou-i.exe.orig_bak");
            string psarcPath = Path.Combine(gameDir, "build", "pc", "main", "core.psarc");
            string psarcBak = Path.Combine(gameDir, "build", "pc", "main", "core.psarc.orig_bak");

            int restored = 0;
            if (File.Exists(exeBak)) {
                File.Copy(exeBak, exePath, true);
                File.Delete(exeBak);
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("  -> Restored original tlou-i.exe");
                Console.ResetColor();
                restored++;
            }
            if (File.Exists(psarcBak)) {
                File.Copy(psarcBak, psarcPath, true);
                File.Delete(psarcBak);
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("  -> Restored original core.psarc");
                Console.ResetColor();
                restored++;
            }

            if (restored > 0) {
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("\n[+] Arabic mod uninstalled successfully! Game restored to original vanilla state.");
                Console.ResetColor();
            } else {
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine("\n[!] No original backups found (.orig_bak). Nothing to restore.");
                Console.ResetColor();
            }

            Console.WriteLine("\nPress any key to exit...");
            Console.ReadKey();
        }

        static void RunInstall(string gameDir, string modDataDir) {
            string exePath = Path.Combine(gameDir, "tlou-i.exe");
            string exeBak = Path.Combine(gameDir, "tlou-i.exe.orig_bak");
            string psarcPath = Path.Combine(gameDir, "build", "pc", "main", "core.psarc");
            string psarcBak = Path.Combine(gameDir, "build", "pc", "main", "core.psarc.orig_bak");
            string oodlePath = Path.Combine(gameDir, "oo2core_9_win64.dll");

            // Step 1: Backups
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("\n[Step 1/3] Checking Backups...");
            Console.ResetColor();

            if (!File.Exists(exeBak)) {
                Console.WriteLine("  Creating backup: tlou-i.exe.orig_bak...");
                File.Copy(exePath, exeBak, true);
            } else {
                Console.WriteLine("  Backup already exists: tlou-i.exe.orig_bak");
            }

            if (!File.Exists(psarcBak)) {
                Console.WriteLine("  Creating backup: core.psarc.orig_bak (~6.3 GB, may take ~20-30s)...");
                Stopwatch swBak = Stopwatch.StartNew();
                File.Copy(psarcPath, psarcBak, true);
                swBak.Stop();
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine(string.Format("  Backup created in {0:F1}s.", swBak.Elapsed.TotalSeconds));
                Console.ResetColor();
            } else {
                Console.WriteLine("  Backup already exists: core.psarc.orig_bak");
            }

            // Step 2: Patch Executable
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("\n[Step 2/3] Patching Game Executable (tlou-i.exe)...");
            Console.ResetColor();

            byte[] exeData = File.ReadAllBytes(exeBak);

            // 1. Format strings in .rdata
            byte[] patFmt1 = Encoding.ASCII.GetBytes("<font color=\"#%08X\">%s:</font>");
            int offFmt1 = FindBytes(exeData, patFmt1);
            if (offFmt1 != -1) {
                byte[] newFmt1 = Encoding.ASCII.GetBytes(" <font color=\"#%08X\">:%s</font>\0");
                Array.Copy(newFmt1, 0, exeData, offFmt1, newFmt1.Length);
                int offFmt2 = offFmt1 + 32;
                byte[] newFmt2 = Encoding.ASCII.GetBytes(" :%s\0\0\0\0");
                Array.Copy(newFmt2, 0, exeData, offFmt2, newFmt2.Length);
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("  -> Patched subtitle speaker layout format strings");
                Console.ResetColor();
            }

            // 2. Outline check 1 (disable per-glyph outline border -> forces Material 0x1e)
            for (int i = 0; i < exeData.Length - 20; i++) {
                if (exeData[i] == 0x83 && exeData[i + 1] == 0xf9 && exeData[i + 2] == 0x01 && exeData[i + 3] == 0x75) {
                    if (exeData[i + 5] == 0x80 && exeData[i + 6] == 0x3d) {
                        if (exeData[i + 12] == 0x75 && exeData[i + 13] == 0x17 && exeData[i + 14] == 0xc7 && exeData[i + 15] == 0x43 && exeData[i + 16] == 0x30 && exeData[i + 17] == 0x1f) {
                            exeData[i + 12] = 0xeb;
                            Console.ForegroundColor = ConsoleColor.Green;
                            Console.WriteLine("  -> Patched outline check 1 (seamless cursive text enabled)");
                            Console.ResetColor();
                            break;
                        }
                    }
                }
            }

            // 3. Outline check 2
            for (int i = 0; i < exeData.Length - 15; i++) {
                if (exeData[i] == 0x80 && exeData[i + 1] == 0x3d) {
                    if (exeData[i + 7] == 0x75 && exeData[i + 8] == 0x09 && exeData[i + 9] == 0xc7 && exeData[i + 10] == 0x43 && exeData[i + 11] == 0x30 && exeData[i + 12] == 0x1f) {
                        exeData[i + 7] = 0xeb;
                        Console.ForegroundColor = ConsoleColor.Green;
                        Console.WriteLine("  -> Patched outline check 2 (seamless cursive text enabled)");
                        Console.ResetColor();
                        break;
                    }
                }
            }

            // 4. Injected RTL dialogue layout hook (465 bytes)
            string hookPath = Path.Combine(modDataDir, "func_hook.bin");
            if (File.Exists(hookPath)) {
                byte[] hookBytes = File.ReadAllBytes(hookPath);
                byte[] prologue = new byte[] {
                    0x48, 0x89, 0x5c, 0x24, 0x08, 0x48, 0x89, 0x6c, 0x24, 0x18, 0x56, 0x57,
                    0x41, 0x54, 0x41, 0x56, 0x41, 0x57, 0x48, 0x81, 0xec, 0x50, 0x02, 0x00, 0x00
                };
                int offFunc = FindBytes(exeData, prologue);
                if (offFunc != -1) {
                    Array.Copy(hookBytes, 0, exeData, offFunc, hookBytes.Length);
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine(string.Format("  -> Injected RTL subtitle layout hook ({0} bytes at offset 0x{1:X})", hookBytes.Length, offFunc));
                    Console.ResetColor();
                }
            }

            File.WriteAllBytes(exePath, exeData);
            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine("  -> Saved patched tlou-i.exe!");
            Console.ResetColor();

            // Step 3: Inject core.psarc
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("\n[Step 3/3] Injecting Arabic Localization Assets into core.psarc (~30s)...");
            Console.ResetColor();

            byte[] freCommon = File.ReadAllBytes(Path.Combine(modDataDir, "text2", "fre.common"));
            byte[] freSub = File.ReadAllBytes(Path.Combine(modDataDir, "text2", "fre.subtitles"));
            byte[] freSys = File.ReadAllBytes(Path.Combine(modDataDir, "text2", "fre.subtitles-systemic"));
            byte[] dinReg = File.ReadAllBytes(Path.Combine(modDataDir, "fonts", "DINPro-Regular.otf"));
            byte[] dinMed = File.ReadAllBytes(Path.Combine(modDataDir, "fonts", "DINPro-Medium.otf"));

            Dictionary<string, byte[]> replacements = new Dictionary<string, byte[]>() {
                { "text2/fre.common", freCommon },
                { "text2/fre.subtitles", freSub },
                { "text2/fre.subtitles-systemic", freSys },
                { "text2/eng.common", freCommon },
                { "text2/eng.subtitles", freSub },
                { "text2/eng.subtitles-systemic", freSys },
                { "fonts/DINPro-Regular.otf", dinReg },
                { "fonts/DINPro-Medium.otf", dinMed }
            };

            string tempPsarc = psarcPath + ".tmp_mod";
            Stopwatch swPsarc = Stopwatch.StartNew();
            InjectPsarc(psarcBak, tempPsarc, replacements, oodlePath);
            swPsarc.Stop();

            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine(string.Format("  PSARC successfully patched in {0:F1}s.", swPsarc.Elapsed.TotalSeconds));
            Console.ResetColor();

            if (File.Exists(psarcPath)) File.Delete(psarcPath);
            File.Move(tempPsarc, psarcPath);

            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine("  Deployed modified core.psarc!");
            Console.ResetColor();

            Console.WriteLine("\n" + new string('=', 72));
            Console.ForegroundColor = ConsoleColor.Yellow;
            Console.WriteLine("   ARABIC LOCALIZATION MOD SUCCESSFULLY INSTALLED!");
            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine("   Created by: " + AUTHOR);
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine(new string('=', 72));
            Console.ResetColor();
            Console.WriteLine("\nHOW TO USE IN-GAME:");
            Console.WriteLine("- The mod is active immediately!");
            Console.WriteLine("- Both English (US) and French slots now display clean Arabic subtitles");
            Console.WriteLine("  and Arabic Document reading with English menus.");
            Console.WriteLine("- When you restart the game, your subtitles will STAY in Arabic automatically!");
            Console.WriteLine("- Simply launch 'The Last of Us Part I' and enjoy playing!\n");

            Console.WriteLine("Press any key to exit...");
            Console.ReadKey();
        }

        static int FindBytes(byte[] haystack, byte[] needle) {
            int limit = haystack.Length - needle.Length;
            for (int i = 0; i <= limit; i++) {
                bool match = true;
                for (int j = 0; j < needle.Length; j++) {
                    if (haystack[i + j] != needle[j]) {
                        match = false;
                        break;
                    }
                }
                if (match) return i;
            }
            return -1;
        }

        class PsarcEntry {
            public byte[] Md5;
            public uint ZIndex;
            public ulong UncompSz;
            public ulong Offset;
        }

        static void InjectPsarc(string srcPsarc, string dstPsarc, Dictionary<string, byte[]> replacements, string oodleDll) {
            InitOodle(oodleDll);

            MD5 md5 = MD5.Create();
            Dictionary<string, byte[]> replByHex = new Dictionary<string, byte[]>();
            foreach (var kv in replacements) {
                byte[] h = md5.ComputeHash(Encoding.UTF8.GetBytes(kv.Key));
                string hex = BitConverter.ToString(h).Replace("-", "").ToLower();
                replByHex[hex] = kv.Value;
            }

            using (FileStream srcFs = new FileStream(srcPsarc, FileMode.Open, FileAccess.Read, FileShare.Read))
            using (BinaryReader br = new BinaryReader(srcFs))
            using (FileStream dstFs = new FileStream(dstPsarc, FileMode.Create, FileAccess.Write, FileShare.None))
            using (BinaryWriter bw = new BinaryWriter(dstFs)) {
                byte[] magic = br.ReadBytes(4);
                ushort verMajor = ReadUInt16BE(br);
                ushort verMinor = ReadUInt16BE(br);
                byte[] compType = br.ReadBytes(4);
                uint origTocLen = ReadUInt32BE(br);
                uint tocEntrySz = ReadUInt32BE(br);
                uint numEntries = ReadUInt32BE(br);
                uint blockSz = ReadUInt32BE(br);
                uint flags = ReadUInt32BE(br);

                List<PsarcEntry> entries = new List<PsarcEntry>((int)numEntries);
                for (int i = 0; i < numEntries; i++) {
                    PsarcEntry e = new PsarcEntry();
                    e.Md5 = br.ReadBytes(16);
                    e.ZIndex = ReadUInt32BE(br);
                    e.UncompSz = ReadUInt40BE(br);
                    e.Offset = ReadUInt40BE(br);
                    entries.Add(e);
                }

                int numZ = (int)((origTocLen - 32 - numEntries * 30) / 2);
                ushort[] origZLengths = new ushort[numZ];
                for (int i = 0; i < numZ; i++) {
                    origZLengths[i] = ReadUInt16BE(br);
                }

                // Compute block counts
                List<int> entryNumBlocks = new List<int>(entries.Count);
                for (int i = 0; i < entries.Count; i++) {
                    string hex = BitConverter.ToString(entries[i].Md5).Replace("-", "").ToLower();
                    ulong sz = replByHex.ContainsKey(hex) ? (ulong)replByHex[hex].Length : entries[i].UncompSz;
                    int nb = (sz > 0) ? (int)((sz + blockSz - 1) / blockSz) : 0;
                    entryNumBlocks.Add(nb);
                }

                int totalZ = 0;
                foreach (int nb in entryNumBlocks) totalZ += nb;
                uint newTocLen = (uint)(32 + numEntries * 30 + totalZ * 2);

                // Placeholder seek
                dstFs.Seek(newTocLen, SeekOrigin.Begin);

                List<PsarcEntry> newEntries = new List<PsarcEntry>(entries.Count);
                List<ushort> newZLengths = new List<ushort>(totalZ);
                byte[] streamBuf = new byte[blockSz + 65536];
                byte[] compBuf = new byte[blockSz + 65536];

                for (int i = 0; i < entries.Count; i++) {
                    PsarcEntry orig = entries[i];
                    string hex = BitConverter.ToString(orig.Md5).Replace("-", "").ToLower();
                    uint curZIdx = (uint)newZLengths.Count;
                    ulong curOffset = (ulong)dstFs.Position;

                    if (replByHex.ContainsKey(hex)) {
                        byte[] data = replByHex[hex];
                        ulong uncompSz = (ulong)data.Length;
                        int nb = entryNumBlocks[i];

                        for (int b = 0; b < nb; b++) {
                            int chunkSz = Math.Min((int)blockSz, data.Length - b * (int)blockSz);
                            byte[] chunk = new byte[chunkSz];
                            Array.Copy(data, b * (int)blockSz, chunk, 0, chunkSz);

                            long cSz = OodleCompress(8, chunk, chunkSz, compBuf, 4, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, 0);
                            if (cSz > 0 && cSz < chunkSz) {
                                newZLengths.Add((ushort)cSz);
                                bw.Write(compBuf, 0, (int)cSz);
                            } else {
                                newZLengths.Add((ushort)0);
                                bw.Write(chunk, 0, chunkSz);
                            }
                        }

                        PsarcEntry ne = new PsarcEntry { Md5 = orig.Md5, ZIndex = curZIdx, UncompSz = uncompSz, Offset = curOffset };
                        newEntries.Add(ne);
                    } else {
                        int nb = entryNumBlocks[i];
                        for (int b = 0; b < nb; b++) {
                            ushort zlen = origZLengths[orig.ZIndex + b];
                            newZLengths.Add(zlen);
                            int readLen = (zlen == 0) ? (int)blockSz : (int)zlen;
                            if (b == nb - 1 && zlen == 0) {
                                int rem = (int)(orig.UncompSz % blockSz);
                                if (rem > 0) readLen = rem;
                            }

                            int readBytes = srcFs.Read(streamBuf, 0, readLen);
                            bw.Write(streamBuf, 0, readBytes);
                        }

                        PsarcEntry ne = new PsarcEntry { Md5 = orig.Md5, ZIndex = curZIdx, UncompSz = orig.UncompSz, Offset = curOffset };
                        newEntries.Add(ne);
                    }
                }

                // Rewind to header and write TOC
                dstFs.Seek(0, SeekOrigin.Begin);
                bw.Write(magic);
                WriteUInt16BE(bw, verMajor);
                WriteUInt16BE(bw, verMinor);
                bw.Write(compType);
                WriteUInt32BE(bw, newTocLen);
                WriteUInt32BE(bw, tocEntrySz);
                WriteUInt32BE(bw, numEntries);
                WriteUInt32BE(bw, blockSz);
                WriteUInt32BE(bw, flags);

                foreach (var e in newEntries) {
                    bw.Write(e.Md5);
                    WriteUInt32BE(bw, e.ZIndex);
                    WriteUInt40BE(bw, e.UncompSz);
                    WriteUInt40BE(bw, e.Offset);
                }

                foreach (ushort zl in newZLengths) {
                    WriteUInt16BE(bw, zl);
                }
            }
        }

        static ushort ReadUInt16BE(BinaryReader br) {
            byte[] b = br.ReadBytes(2);
            return (ushort)((b[0] << 8) | b[1]);
        }
        static uint ReadUInt32BE(BinaryReader br) {
            byte[] b = br.ReadBytes(4);
            return (uint)((b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]);
        }
        static ulong ReadUInt40BE(BinaryReader br) {
            byte[] b = br.ReadBytes(5);
            return ((ulong)b[0] << 32) | ((ulong)b[1] << 24) | ((ulong)b[2] << 16) | ((ulong)b[3] << 8) | (ulong)b[4];
        }
        static void WriteUInt16BE(BinaryWriter bw, ushort val) {
            bw.Write((byte)(val >> 8));
            bw.Write((byte)val);
        }
        static void WriteUInt32BE(BinaryWriter bw, uint val) {
            bw.Write((byte)(val >> 24));
            bw.Write((byte)(val >> 16));
            bw.Write((byte)(val >> 8));
            bw.Write((byte)val);
        }
        static void WriteUInt40BE(BinaryWriter bw, ulong val) {
            bw.Write((byte)(val >> 32));
            bw.Write((byte)(val >> 24));
            bw.Write((byte)(val >> 16));
            bw.Write((byte)(val >> 8));
            bw.Write((byte)val);
        }
    }
}
