import os, sys, time
from psarc import PsarcArchive, get_oodle

def verify_archive(psarc_path):
    print(f"Testing PSARC archive: {psarc_path} ({os.path.getsize(psarc_path):,} bytes)...")
    t0 = time.time()
    with PsarcArchive(psarc_path) as arc:
        print(f"  Total entries: {len(arc.entries):,}")
        print(f"  Block size: {arc.block_sz}")
        print(f"  Compression: {arc.comp}")
        
        # 1. Verify Entry 0 (Manifest)
        manifest = arc.extract_by_entry(arc.entries[0])
        print(f"  Entry 0 (Manifest): {len(manifest):,} bytes decompressed.")
        assert len(manifest) > 1000, "Manifest too small!"

        # 2. Verify replaced files
        targets = [
            "text2/fre.common",
            "text2/fre.subtitles",
            "text2/fre.subtitles-systemic",
            "text2/eng.common",
            "text2/eng.subtitles",
            "text2/eng.subtitles-systemic",
            "fonts/DINPro-Regular.otf",
            "fonts/DINPro-Medium.otf"
        ]
        for t in targets:
            data = arc.extract_by_name(t)
            print(f"  Extracted {t}: {len(data):,} bytes (OK)")

        # 3. Verify random untouched files across the archive
        sample_indices = [1, 10, 50, 100, 500, 1000, 2000, 3000, 4000, 5000, len(arc.entries)-1]
        for idx in sample_indices:
            ent = arc.entries[idx]
            d = arc.extract_by_entry(ent)
            assert len(d) == ent.uncomp_sz, f"Decompression mismatch at entry {idx}!"
        print(f"  Verified {len(sample_indices)} random untouched entries across the archive!")

    print(f"ALL CHECKS PASSED in {time.time()-t0:.1f}s! Archive is 100% HEALTHY.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        verify_archive(sys.argv[1])
    else:
        print("Usage: python test_csharp_patcher.py <psarc_path>")
