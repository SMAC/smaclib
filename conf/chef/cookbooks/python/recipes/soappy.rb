execute "install-fpconst" do
  command "pip install -E /home/#{node[:python][:user]}/.virtualenvs/#{node[:python][:virtualenv]} fpconst"
  
  user node[:python][:user]
  group node[:python][:group]
end

execute "install-soappy" do
  user node[:python][:user]
  group node[:python][:group]
  
  command "mkdir -p /tmp/soap"
end

cookbook_file "/tmp/soap/patch" do
  owner node[:python][:user]
  group node[:python][:group]
  
  source "SOAPpy.patch"
end

execute "get-soappy" do
  user node[:python][:user]
  group node[:python][:group]
  cwd "/tmp/soap"
  command <<-EOH
  wget http://downloads.sourceforge.net/project/pywebsvcs/SOAP.py/0.11.6/SOAPpy-0.11.6.tar.gz
  EOH
end

execute "patch-soappy" do
  user node[:python][:user]
  group node[:python][:group]
  cwd "/tmp/soap"
  command "tar -xzf SOAPpy-*.tar.gz ; rm -f SOAPpy-*.tar.gz ; cd SOAPpy-* ; patch -R -p1 -i ../patch"
end

execute "install-soappy" do
  user node[:python][:user]
  group node[:python][:group]
  cwd "/tmp/soap"
  command "cd SOAPpy-* ; pip -E /home/#{node[:python][:user]}/.virtualenvs/#{node[:python][:virtualenv]} install ."
end

execute "cleanup-soappy" do
  user node[:python][:user]
  group node[:python][:group]
  cwd "/tmp"
  command "rm -rf soap"
end
