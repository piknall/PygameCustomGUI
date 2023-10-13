from setuptools import setup, find_packages
import codecs
import os

VERSION = '0.0.1'
DESCRIPTION = 'A customizable button library for pygame'
LONG_DESCRIPTION = 'A customizable button library for pygame featuring squared buttons'

# Setting up
setup(
    name="pygame_custom_gui",
    version=VERSION,
    author="piknall",
    author_email="pisafe@tutanota.com",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=['pygame-ce', 'numpy'],
    keywords=['python', 'pygame', 'gui', 'buttons'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)
