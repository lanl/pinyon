from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

#with open('LICENSE') as f:
    #license = f.read()

setup(
    name='pinyon',
    version='0.0.1',
    description='Library for managing analysis and visualization of data',
    long_description=readme,
    #url='https://github.com/',
    license=license,
    install_requires=[
	'bokeh',
	'cornice',
	'jupyter',
        'mongoengine',
        'pandas',
	'pint',
	'periodictable',
        'pyramid',
        'pyramid_chameleon',
	'pyramid_debugtoolbar',
        'scipy',
	'webtest',
	'wtforms',
	'xmltodict',
    ],
    packages=find_packages(exclude=('tests', 'docs'))
)
