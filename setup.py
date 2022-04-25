from setuptools import setup, find_packages

setup(name='pyhemo',
      version='0.1',
      description='PYthonic HEad MOdelling',
      url='https://github.com/harmening/pyhemo',
      author='Nils Harmening',
      author_email='nils.harmening@tu-berlin.de',
      license='MIT',
      #packages=['pyhemo'],
      packages=find_packages(include=['pyhemo', 'pyhemo.*']),
      zip_safe=False)
