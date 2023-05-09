from setuptools import setup

install_requires=['phidl','jupyter','jupyterlab','pandas'
]

setup(name='pala',
      version='0.01',
      description='Python Package based on amccaugh\phidl for passives GDS layout',
      author='Giuseppe Michetti',
      author_email='michetti.g@northeastern.edu',
      packages=['pala'],
      install_requires=install_requires,
     )