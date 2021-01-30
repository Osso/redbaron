from setuptools import setup

try:
    from pypandoc import convert_file

    def read_md(f):
        return convert_file(f, 'rst')
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")

    def read_md(f):
        return open(f, 'r').read()


setup(name='redbaron',
      version='1.0',
      description='Abstraction on top of baron, a FST for python to make '
                  'writing refactoring code a realistic task',
      author='Laurent Peuch',
      long_description=read_md("README.md") + "\n\n" + open("CHANGELOG", "r").read(),
      author_email='cortex@worlddomination.be',
      url='https://github.com/PyCQA/redbaron',
      install_requires=["baron==1.0"],
      dependency_links=['http://github.com/Osso/baron/tarball/master#egg=baron-1.0'],
      extras_require={
          "notebook": ["pygments"],
      },
      license='lgplv3+',
      packages=["redbaron"],
      keywords='baron fst ast refactoring',
      classifiers=['Development Status :: 3 - Alpha',
                   'Intended Audience :: Developers',
                   'Programming Language :: Python :: 3',
                   'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
                   'Topic :: Software Development',
                   'Topic :: Software Development :: Code Generators',
                   'Topic :: Software Development :: Libraries'])
