name "archiver"

description "Sets up the required environment for the archiver module."

#sudo rm -f /var/db/mongodb/mongod.lock 
#sudo su
#sudo -u mongodb /opt/mongodb-1.6.5/bin/mongod --repair --config /etc/mongodb.conf

run_list(
  "recipe[mongodb]",
  "recipe[python::soappy]",
  "recipe[python::packages]",
  "recipe[modules::archiver]"
)

# TODO:
# Add ghostscript imagemagick libxml-dev and libxsl-dev to the packages to install
#add apt-get install liblame-dev libfaad-dev libfaac-dev libxvidcore4-dev liba52-0.7.4 liba52-0.7.4-dev libx264-dev 

default_attributes :python => {
  :virtualenv => "archiver",
  :packages => "twisted pyopenssl pycrypto pyasn1 thrift https://nodeload.github.com/fiorix/mongo-async-python-driver/tarball/master lxml",
  :directories => "/smac-source",
}

