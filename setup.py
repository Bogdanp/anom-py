from setuptools import setup


with open("anom/__init__.py") as module:
    version_marker = "__version__ = "
    for line in module:
        if line.startswith(version_marker):
            version = line[len(version_marker):].strip().strip('"')
            break
    else:
        assert False, "could not find version in anom/__init__.py"


setup(
    name="anom",
    version=version,
    description="anom is an object mapper for Google Cloud Datastore.",
    long_description="https://github.com/Bogdanp/anom-py",
    packages=["anom", "anom.adapters", "anom.testing"],
    install_requires=[
        "google-cloud-datastore==0.23.0",
        "python-dateutil==2.6.0",
    ],
    author="Bogdan Popa",
    author_email="popa.bogdanp@gmail.com",
    url="https://github.com/Bogdanp/anom-py",
)
