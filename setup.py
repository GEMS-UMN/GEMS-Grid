from setuptools import setup, find_packages

setup(
    name="gemsgrid",
    version='0.1.0',
    description='GEMS Grid Library Code and Tools',
    url='https://github.umn.edu/IAA/gems_grid',
    author='GEMS Geospatial Developers',
    author_email='gemssupport@umn.edu',
    packages=find_packages(
        where='src',
        include=['gemsgrid*'],
        exclude=['additional'],
        ),
    package_dir={"": "src"},
    package_data={'': ['grid_spec.json', 'levels_specs.json']},
    include_package_data=True,
    install_requires =[
        'pytest',
        #'python >= 3.9.7',
        'pyproj >= 3.2.1',
        'geopandas >= 0.10.0',
        'numpy >= 1.21.2',
        'pandas >= 1.3.3',
        'shapely >= 1.7.1',
        'rasterio >= 1.2',
        ],
    classifiers=[
        'Programming Language :: Python :: 3.9',
        ]
    )
