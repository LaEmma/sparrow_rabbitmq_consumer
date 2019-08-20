import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sparrow_rabbitmq_consumer",
    version="0.0.8",
    author="Hanguangbaihuo",
    author_email="chao.liu@hanguangbaihuo.cn",
    description="Sparrow rabbitmq consumer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hanguangbaihuo/sparrow_rabbitmq_consumer.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)