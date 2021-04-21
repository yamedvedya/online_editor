# ----------------------------------------------------------------------
# Author:   yury.matveev@desy.de
# ----------------------------------------------------------------------

import os
import sys

# ----------------------------------------------------------------------
in_dirs = ["src/ui"]
out_dirs = ["src/gui"]

# ----------------------------------------------------------------------
def compile_uis(ui_compiler, rc_compiler, in_dirs, out_dirs):
    """
    """
    for in_dir, out_dir in zip(in_dirs, out_dirs):
        for f in [f for f in os.listdir(in_dir) if os.path.isfile(os.path.join(in_dir, f))
                                                   and os.path.splitext(f)[-1] in [".ui",
                                                                                   ".qrc"]]:  # simplify this loop TODO
            base, ext = os.path.splitext(f)
            if ext == ".ui":
                cmd = "{} {}/{} -o {}/{}{}.py".format(ui_compiler, in_dir, f, out_dir, base, "_ui")
            else:
                cmd = "{} {}/{} -o {}{}.py".format(rc_compiler, in_dir, f, base, "_rc")

            print(cmd)
            os.system(cmd)


# ----------------------------------------------------------------------
def build_gui():

    print("Removing pyc files...")

    for out_dir in out_dirs:
        for root, dirs, files in os.walk(out_dir):
            for f in [f for f in files if f.endswith(".pyc")]:
                if sys.platform == "linux" or sys.platform == "linux2":
                    os.system("rm {}".format(os.path.join(root, f)))
                elif sys.platform == "win32":
                    os.remove(os.path.join(root, f))

    print("Removing uis and rcs...")
    for out_dir in out_dirs:
        for root, dirs, files in os.walk(out_dir):
            for f in [f for f in files if (f.endswith(".pyc") or f.endswith(".py"))
                                          and f != "__init__.py"]:
                if sys.platform == "linux" or sys.platform == "linux2":
                    os.system("rm {}".format(os.path.join(root, f)))
                elif sys.platform == "win32":
                    os.remove(os.path.join(root, f))

    print("All removed!")

    if sys.platform == "linux" or sys.platform == "linux2":
        ui_compilers = "python -m PyQt5.uic.pyuic"
        rc_compilers = "pyrcc5"

    elif sys.platform == "win32":
        ui_compilers = os.path.join(os.path.dirname(sys.executable), os.path.join('Scripts', 'pyuic5.exe'))
        rc_compilers = os.path.join(os.path.dirname(sys.executable), os.path.join('Scripts', 'pyrcc5.exe'))

    compile_uis(ui_compilers, rc_compilers, in_dirs, out_dirs)

    print("All OK!")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    build_gui()
