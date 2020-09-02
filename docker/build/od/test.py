import tensorflow as tf
if tf.__version__ < '1.8.0':
  raise ImportError('Please upgrade your tensorflow installation to v1.8.* or later!')
else:
  print 'tensorflow installed, version is {}'.format(tf.__version__)
