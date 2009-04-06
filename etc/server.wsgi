# WSGIPythonHome /home/greentv/sites/mint.repoze
# WSGIDaemonProcess greentv threads=1 processes=4 maximum-requests=10000 python-path=/home/greentv/env/mint.repoze/lib/python2.6/site-packages
# 
# <VirtualHost *:80>
#     ServerName mint.green.tv
#     WSGIScriptAlias / /home/greentv/sites/mint.repoze/etc/server.wsgi
#     WSGIProcessGroup greentv
#     WSGIPassAuthorization On
#     SetEnv HTTP_X_VHM_HOST http://mint.green.tv/
# </VirtualHost>

import os
from paste.deploy import loadapp
from os.path import join, dirname

application = loadapp('config:' + join(dirname(__file__), 'paste.ini'))