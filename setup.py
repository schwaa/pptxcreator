from setuptools import setup, find_packages

setup(
    name="pptx-generator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-pptx>=0.6.21",
        "openai>=1.0.0",
        "markdown>=3.4.0",
        "Pillow>=10.0.0",
        "click>=8.1.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0"
    ],
    entry_points={
        "console_scripts": [
            "pptx-gen=pptx_generator.main:main",
        ],
    },
    python_requires=">=3.13",
)
