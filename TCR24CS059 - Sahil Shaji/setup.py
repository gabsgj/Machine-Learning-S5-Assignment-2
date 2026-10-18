from setuptools import setup, find_packages

setup(
    name="capability-embedding",
    version="1.0.0",
    description="Vector Embedding Framework for Capability Composition and Functional Reasoning",
    author="Antigravity Advanced AI Systems",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.22.0",
        "scipy>=1.8.0",
        "scikit-learn>=1.0.0",
        "matplotlib>=3.5.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
