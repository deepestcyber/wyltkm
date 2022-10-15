from setuptools import find_packages, setup

setup(
    name='wyltkm',
    version='0.1.2',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'flask-wtf',
        'qrcode',
        'reportlab',
        'svgwrite',
        'svglib',
        'ziafont',
    ],
)
