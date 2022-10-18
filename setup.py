from setuptools import setup, find_packages

setup(name='pyhemo',
      version='0.3',
      description='PYthonic HEad MOdelling',
      url='https://github.com/harmening/pyhemo',
      author='Nils Harmening',
      author_email='nils.harmening@tu-berlin.de',
      license='GNU General Public License v3.0',
      #packages=['pyhemo'],
      packages=find_packages(include=['pyhemo', 'pyhemo.*']),
      zip_safe=False)
