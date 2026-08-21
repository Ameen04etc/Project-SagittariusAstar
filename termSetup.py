from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext


ext_modules = [
    Pybind11Extension(
        "termCore",
        [
            "termCore.cpp",
            "termBindings.cpp",
        ],
        cxx_std=17,
    ),
]


setup(
    name="termCore",
    version="0.1.0",
    description="Sagittarius A ConPTY terminal backend",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)