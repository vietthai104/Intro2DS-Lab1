import os, tarfile, glob
import logging

def get_directory_size(path: str) -> int:
    """Calculate total size of a directory in bytes."""
    if not os.path.exists(path):
        return 0
    
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if not os.path.islink(filepath):
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        pass
    except Exception as e:
        logging.warning(f"Error calculating directory size for {path}: {e}")
    
    return total_size

def _extract_all_tars(tex_dir):
    """Extract all .tar.gz files in the tex directory into version-specific subdirectories"""
    tar_files = glob.glob(os.path.join(tex_dir, "*.tar.gz"))
    logging.info(f"  Extracting {len(tar_files)} tar.gz file(s)")
    
    for tgz in tar_files:
        # Get the version name from the tar.gz filename
        # e.g., "202510-00824v1.tar.gz" -> "202510-00824v1"
        version_name = os.path.splitext(os.path.splitext(os.path.basename(tgz))[0])[0]
        version_dir = os.path.join(tex_dir, version_name)
        os.makedirs(version_dir, exist_ok=True)
        
        try:
            # Try to open as gzipped tarfile
            with tarfile.open(tgz, "r:gz") as tf:
                tf.extractall(version_dir)
            logging.debug(f"  Extracted {os.path.basename(tgz)} to {version_name}/")
        except tarfile.ReadError:
            # Some arXiv sources are single files, not tarballs
            # Try to open as plain tarfile or just skip
            try:
                with tarfile.open(tgz, "r:") as tf:
                    tf.extractall(version_dir)
                logging.debug(f"  Extracted (uncompressed) {os.path.basename(tgz)} to {version_name}/")
            except Exception:
                # Not a tar file at all - might be a single .tex file renamed
                logging.debug(f"  Skipping {os.path.basename(tgz)} (not a valid tar archive)")
        except Exception as e:
            logging.warning(f"  Could not extract {os.path.basename(tgz)}: {e}")
        
        # Check if any .tex files were extracted
        tex_files = glob.glob(os.path.join(version_dir, "**", "*.tex"), recursive=True)
        if not tex_files:
            logging.info(f"  No .tex files found in {version_name}")
        
        # Always remove the tar.gz file to save disk space
        try:
            os.remove(tgz)
            logging.debug(f"  Removed {os.path.basename(tgz)}")
        except Exception as e:
            logging.warning(f"  Could not remove {os.path.basename(tgz)}: {e}")

def _remove_images(tex_dir):
    """Remove image files to reduce storage size"""
    exts = (".png", ".jpg", ".jpeg", ".pdf", ".eps", ".svg", ".tif", ".tiff", ".bmp", ".gif")
    removed_count = 0
    
    for root, _, files in os.walk(tex_dir):
        for f in files:
            if f.lower().endswith(exts):
                try:
                    file_path = os.path.join(root, f)
                    os.remove(file_path)
                    removed_count += 1
                except Exception as e:
                    logging.warning(f"  Could not remove {f}: {e}")
    
    logging.info(f"  Removed {removed_count} image file(s)")

def strip_figures_and_images(paper_dir):
    """
    Main function to clean a paper directory:
    1. Extract all tar.gz files
    2. Remove image files
    
    Returns:
        tuple: (size_before, size_after) in bytes
    """
    tex_dir = os.path.join(paper_dir, "tex")
    
    if not os.path.exists(tex_dir):
        logging.warning(f"  tex/ directory not found in {paper_dir}")
        return (0, 0)
    
    # Calculate size before cleaning
    size_before = get_directory_size(tex_dir)
    
    logging.info(f"  Extracting and removing images")
    _extract_all_tars(tex_dir)
    _remove_images(tex_dir)
    
    # Calculate size after cleaning
    size_after = get_directory_size(tex_dir)
    
    return (size_before, size_after)
