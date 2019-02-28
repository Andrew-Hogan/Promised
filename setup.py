import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="promised",
    version="1.1.1",
    author="Andrew M. Hogan",
    author_email="drewthedruid@gmail.com",
    description="A flexible cached property with get/set/del/init/dependant/cached-mapping capabilities.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Andrew-Hogan/Promised",
    packages=setuptools.find_packages(),
    install_requires=[],
    platforms=['any'],
    license="LICENSE",
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
)
