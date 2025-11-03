import os, re, tarfile, glob

FIG_ENV = re.compile(r"\\begin{figure}.*?\\end{figure}", re.S)
INC_GFX = re.compile(r"\\includegraphics(?:\[[^\]]*\])?{[^}]+}")

def _extract_all_tars(tex_dir):
    for tgz in glob.glob(os.path.join(tex_dir, "*.tar.gz")):
        with tarfile.open(tgz, "r:gz") as tf:
            tf.extractall(tex_dir)

def _remove_images(tex_dir):
    exts = (".png",".jpg",".jpeg",".pdf",".eps",".svg",".tif",".tiff",".bmp")
    for root,_,files in os.walk(tex_dir):
        for f in files:
            if f.lower().endswith(exts):
                try: os.remove(os.path.join(root,f))
                except: pass

def _strip_tex(tex_dir):
    for root,_,files in os.walk(tex_dir):
        for f in files:
            if f.endswith(".tex"):
                p = os.path.join(root,f)
                s = open(p,"r",errors="ignore").read()
                s = FIG_ENV.sub("% removed figure env", s)
                s = INC_GFX.sub("% removed includegraphics", s)
                open(p,"w").write(s)

def strip_figures_and_images(paper_dir):
    tex_dir = os.path.join(paper_dir, "tex")
    _extract_all_tars(tex_dir)
    _remove_images(tex_dir)
    _strip_tex(tex_dir)
