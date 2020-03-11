from setuptools import setup

from ten_h_looper import __version__


with open("README.md", "r") as f:
    readme = f.read()

setup(
    name="ten-h-looper",
    version=__version__,
    author="Aleksa Ćuković",
    author_email="aleksacukovic1@gmail.com",
    description="Create 10h loops of YouTube video excerpts.",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/AleksaC/ten-h-looper",
    license="MIT",
    python_requires=">=3.4",
    install_requires=["youtube_dl"],
    packages=["ten_h_looper"],
    entry_points={"console_scripts": ["create_loop = ten_h_looper.create_loop:main"]},
)
