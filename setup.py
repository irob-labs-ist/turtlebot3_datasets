from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'turtlebot3_datasets'

setup(
    name=package_name,
    version='0.0.2',
    packages=find_packages(exclude=['test']),
    data_files=[
        # ament index marker
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        # package.xml
        ('share/' + package_name, ['package.xml']),
        # launch files
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
        # config files (RViz2, etc.)
        (os.path.join('share', package_name, 'config'),
            glob('config/*')),
        # data files (maps, etc. — bags are large and downloaded separately)
        (os.path.join('share', package_name, 'data'),
            glob('data/*.yaml') + glob('data/*.pgm') + glob('data/*.png')),
        # docs
        (os.path.join('share', package_name, 'docs'),
            glob('docs/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Guilherme Lawless',
    maintainer_email='guilherme.lawless@tecnico.ulisboa.pt',
    description='Datasets to be used with turtlebot3 waffle pi (ROS 2)',
    license='GPLv3',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # Publishes the initial mocap -> fixed_frame static transform
            'publish_initial_tf = turtlebot3_datasets.publish_initial_tf:main',
        ],
    },
)
