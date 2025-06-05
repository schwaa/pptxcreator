from setuptools import setup, find_packages

setup(
    name='pptx-generator',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'python-pptx',
        'Pillow',
    ],
    entry_points={
        'console_scripts': [
            'pptx-gen=pptx_generator.main:main', # This creates the CLI command
        ],
    },
    author='[Your Name/Organization]',
    author_email='[your.email@example.com]',
    description='A tool to generate PowerPoint presentations from data and templates.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/[your-username]/pptx-generator', # Update with your repo URL
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
    include_package_data=True, # Important for including template files
    package_data={
        'pptx_generator': ['templates/*.pptx', 'data/*.json'], # Not strictly needed with separate directories, but good practice if bundled
    },
)
