
# Environment
## python environment setup
$ conda env list
$ conda create -n python-remix-ide python=3.6

$ conda env list 
You can see there is a python-remix-ide item


$ conda activate python-remix-ide
First time to do this function may not work ,but 
the console may hint you to do conda init ... 

Mac User 
$ bash
$ conda init bash   <-- If you need 


Close you terminal app and re-open it again . 
$ conda env list 
you can see there is a python-remix-ide . 

$ conda activate python-remix-ide 

$ conda env list 
you can see there is a star behind the item of python-remix-ide
It's mean you have already to choice 

$ git clone https://github.com/milochen0418/python-remix-ide
$ cd python-remix-ide
$ conda install -n python-remix-ide --file requirements.txt
$ pip install eventlet
(conda cannot support to install eventlet. it is pip install only)

$ flask run -h 0.0.0.0 -p 3344
use flask and run for host 0.0.0.0 (all people can get this host)
and with port 3344

Then the code should run 




