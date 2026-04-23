from setuptools import setup, find_packages

setup(
    name="FSIF_to_FS2_Converter",
    version="2.8.0",
    description="Converts FSIF mission files to Freespace 2 (.fs2) format",
    author="NeuralFS",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "PyYAML",
        "pydantic>=2.0",
        "google-genai",  # Optional, for TTS
    ],
    entry_points={
        'console_scripts': [
            'fsif-convert=FSIF_to_FS2_Converter.fsif_to_fs2:main',
        ],
    },
)
