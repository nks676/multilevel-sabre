from setuptools import setup, find_packages

setup(
    name="multilevel-sabre",
    version="0.1.0",
    package_dir={"multilevel_sabre": "src"},
    packages=["multilevel_sabre"],
    install_requires=[
        "qiskit>=2.0",
    ],
    author="Naren Sathishkumar",
    author_email="nks676@ucla.edu",
    description="A Qiskit transpiler pass implementing multi-level SABRE algorithm",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/nks676/multilevel-sabre",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
) 