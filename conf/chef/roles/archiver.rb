name "archiver"

description "Sets up the required environment for the archiver module."
 
#sudo su
#rm -f /var/db/mongodb/mongod.lock
#sudo -u mongodb /opt/mongodb-1.6.5/bin/mongod --repair --config /etc/mongodb.conf

run_list(
  "recipe[python]",
  "recipe[modules::archiver]",
  "recipe[mongodb]",
  "recipe[python::soappy]",
  "recipe[python::packages]"
)

# TODO:
# Add  to the packages to install
# liblame-dev libxvidcore4-dev
#sudo apt-get install libfaad-dev libfaac-dev liba52-0.7.4 liba52-0.7.4-dev libx264-dev ghostscript imagemagick libxml2-dev and libxslt1-dev

default_attributes :python => {
  :virtualenv => "archiver",
  :packages => "twisted pyopenssl pycrypto pyasn1 thrift https://nodeload.github.com/fiorix/mongo-async-python-driver/tarball/master lxml",
  :directories => "/smac-source",
  :version => "2.6",
}
