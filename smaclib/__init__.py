"""
SMAC base package.

Contains the core library to publish a SMAC module over different protocols, a
MongoDB asynchronous ORM compatible with twisted, various configuration loaders
for different source types and much more to make work on SMAC a joy.

The api package is generated from the thrift sources found in the conf/api
directory of the *project* root. The project fabfile contains the functions
needed to compile them and put them in the right place.
"""