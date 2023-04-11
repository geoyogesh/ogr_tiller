from setuptools import setup, find_packages

CLASSIFIERS = [
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
]

setup(name='ogr_tiller',
      version='0.0.46',
      url='https://github.com/geoyogesh/ogr_tiller',
      license='GNU-GPL',
      author='Yogesh Dhanapal',
      author_email='geoyogesh@gmail.com',
      entry_points={"console_scripts": ["ogr_tiller = ogr_tiller.main:cli"]},
      description='Creates vector tiles on the fly from local geopackage files',
      packages=find_packages(),
      long_description=open('README.md').read(),
      long_description_content_type='text/markdown',
      zip_safe=False,
      classifiers=CLASSIFIERS,
      install_requires=["fastapi", "uvicorn[standard]", "protobuf", "parse",
                        "morecantile", "fiona", "pyproj", "supermercado", "pyyaml",
                        "mapbox_vector_tile>=2.0.1", "rich"]
      )
