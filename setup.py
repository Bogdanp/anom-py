from setuptools import setup


with open("anom/__init__.py") as module:
    version_marker = "__version__ = "
    for line in module:
        if line.startswith(version_marker):
            version = line[len(version_marker):].strip().strip('"')
            break
    else:
        assert False, "could not find version in anom/__init__.py"


dependencies = []
with open("requirements.txt") as reqs:
    for line in reqs:
        dependencies.append(line.strip())


extra_dependencies = {}
for group in ("memcache",):
    extra_dependencies[group] = extra_dep_list = []
    with open(f"requirements-{group}.txt") as reqs:
        for line in reqs:
            extra_dep_list.append(line.strip())


setup(
    name="anom",
    version=version,
    description="anom is an object mapper for Google Cloud Datastore.",
    long_description="https://github.com/Bogdanp/anom-py",
    packages=["anom", "anom.adapters", "anom.testing"],
    install_requires=dependencies,
    extras_require=extra_dependencies,
    author="Bogdan Popa",
    author_email="popa.bogdanp@gmail.com",
    url="https://github.com/Bogdanp/anom-py",
)
