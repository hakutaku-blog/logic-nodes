import os
import glob
import shutil
import sys

def main():
    posts_dir = r"C:\Users\takut\.gemini\antigravity\scratch\logic-nodes\src\posts"
    archive_dir = r"C:\Users\takut\.gemini\antigravity\scratch\logic-nodes\src\archive"
    os.makedirs(archive_dir, exist_ok=True)
    
    md_files = glob.glob(os.path.join(posts_dir, "*.md"))
    archived_count = 0
    
    for fpath in md_files:
        basename = os.path.basename(fpath)
        # Expected format: YYYY-MM-DD-something.md
        parts = basename.split('-')
        if len(parts) >= 3:
            date_str = f"{parts[0]}-{parts[1]}-{parts[2]}"
            if date_str <= "2026-08-17":
                # Move to archive
                dest = os.path.join(archive_dir, basename)
                shutil.move(fpath, dest)
                print(f"Archived: {basename}")
                archived_count += 1
                
    print(f"Total archived: {archived_count} files.")
    
    # Update manifest and sitemap by calling generate.py's functions
    # I'll just run python -c "from generate import update_posts_manifest, update_sitemap_xml; update_posts_manifest(); update_sitemap_xml()"
    
if __name__ == "__main__":
    main()
