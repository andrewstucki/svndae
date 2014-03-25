"""
module author: Andrew Stucki
"""

import errno
import os

def mkdir(*a, **kw):
  """
  Wrapper for the mkdir function
  """
  try:
    os.mkdir(*a, **kw)
  except OSError, e:
    if e.errno == errno.EEXIST:
      pass
    else:
      raise

def rmdir(*a, **kw):
  """
  Wrapper for the rmdir function
  """
  os.rmdir(*a, **kw)

def unlink(*a):
  """
  Wrapper for the unlink function
  """
  os.unlink(*a)
