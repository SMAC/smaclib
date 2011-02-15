execute "install-python-packages" do
  user node[:python][:user]
  group node[:python][:group]
  
  command "pip install -E $HOME/.virtualenvs/#{node[:python][:virtualenv]} #{node[:python][:packages]}"
  
  environment ({'HOME' => "/home/#{node[:python][:user]}"})
  
end