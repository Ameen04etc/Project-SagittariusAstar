import os
from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

# Paths to your frameworks
QT = r"C:\Qt\6.11.1\msvc2022_64"
OPENCV = r"C:\opencv\build"

# Automatically detect if OpenCV uses vc16 or vc17 under the hood
vc_dir = "vc16"
if os.path.exists(os.path.join(OPENCV, "x64", "vc17")):
    vc_dir = "vc17"

ext_modules = [
    Pybind11Extension(
        "renderCore",
        ["renderCore.cpp"],

        include_dirs=[
            QT + r"\include",
            QT + r"\include\QtCore",
            QT + r"\include\QtGui",
            QT + r"\include\QtWidgets",
            OPENCV + r"\include",  # 1. Tells compiler where opencv2/opencv.hpp is
        ],

        library_dirs=[
            QT + r"\lib",
            os.path.join(OPENCV, "x64", vc_dir, "lib"),  # 2. Tells linker where the .lib files live
        ],

        libraries=[
            "Qt6Core",
            "Qt6Gui",
            "Qt6Widgets",
            "opencv_world4130",  # 3. Links the unified OpenCV binary
        ],

        extra_compile_args=[
            "/Zc:__cplusplus",
        ],
    ),
]

setup(
    name="renderCore",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)