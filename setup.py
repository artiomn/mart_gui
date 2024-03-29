from setuptools import setup
import pathlib

here = pathlib.Path(__file__).parent.resolve()

requirements = [r for r in (here / 'requirements.txt').read_text(encoding='utf-8').split()
                if r and not r.lstrip().startswith('#')]
version = here / 'mart_gui' / '__version__.py'
v = compile(version.read_text(encoding='utf-8'), '', 'exec')
exec(v)

setup(
    install_requires=requirements,
    tests_require=['pytest'],
    # scripts=['mart.py'],
    entry_points={
        'console_scripts': [
            'mart = mart_gui.app:main',
        ],
    },
    # flake8: ignore=F821
    version=__version__,  # noqa
    zip_safe=False
)
