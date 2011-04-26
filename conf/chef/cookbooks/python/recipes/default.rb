execute "apt-update" do
  command "apt-get update"
  user "root"
  group "root"
end


package "zlib1g-dev"
package "libbz2-dev"
package "libssl-dev"
package "python-dev"
package "python-setuptools"

cookbook_file "/tmp/virtualenv" do
  source "virtualenv"
  owner "vagrant"
end

execute "virtualenvwrapper-path" do
  command "cat /tmp/virtualenv >>/etc/profile"
  not_if "grep \"$(cat /tmp/virtualenv)\" /etc/profile"
  
  user "root"
  group "root"
  
  action :nothing
end

execute "virtualenvwrapper-home" do
  command "mkdir -p /home/#{node[:python][:user]}/.virtualenvs"
  user "vagrant"
  group "vagrant"
  
  action :nothing
end

execute "setupenv-python" do
  cwd "/tmp"
  
  #command <<-EOH
  #wget #{node[:python][:setuptools]}
  #tar -zxf setuptools-*.tar.gz
  #rm setuptools-*.tar.gz
  #cd setuptools-*
  ##{node[:python][:binary]} setup.py install
  #cd ..
  #rm -rf setuptools-*
  #rm -f /usr/local/bin/easy_install
  command <<-EOH
  easy_install-#{node[:python][:version]} pip
  easy_install-#{node[:python][:version]} virtualenv
  easy_install-#{node[:python][:version]} virtualenvwrapper
  EOH
  
  user "root"
  group "root"
  
  #action :nothing
  notifies :run, resources(:execute => "virtualenvwrapper-home"), :immediately
  notifies :run, resources(:execute => "virtualenvwrapper-path"), :immediately
end


#execute "cleanup-python" do
#  command <<-EOH
#  rm -rf /tmp/python
#  rm -f /usr/local/bin/python
#  rm -f /usr/local/bin/python-config
#  EOH
#  
#  user "root"
#  group "root"
#  
#  action :nothing
#  
#  notifies :run, resources(:execute => "setupenv-python"), :immediately
#end
#
#
#execute "install-python" do
#  cwd "/tmp/python"
#  
#  command <<-EOH
#  ./configure
#  make
#  make install
#  EOH
#  
#  user "root"
#  group "root"
#  
#  action :nothing
#  
#  notifies :run, resources(:execute => "cleanup-python"), :immediately
#end
#
#
#execute "get-python" do
#  cwd "/tmp"
#  
#  command <<-EOH
#  wget #{node[:python][:url]}
#  tar -zxf Python-*
#  rm -f Python-*.tgz
#  mv Python-* python
#  EOH
#  
#  user "root"
#  group "root"
#  
#  not_if do
#    File.exists?(node[:python][:binary])
#  end
#  
#  notifies :run, resources(:execute => "install-python"), :immediately
#end
#
#