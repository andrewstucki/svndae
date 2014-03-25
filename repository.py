"""
module author: Andrew Stucki
"""

class RepositoryError(Exception):
  """
  Base class for Repo errors
  """

class IllegalRepoError(RepositoryError):
  """
  Repository's name contains illegal characters
  """

class Repo:
  """
  Repo class
  """

  def __init__(self,name,path=None):
    """
    Initialization method
    """
    if ' ' in name:
      raise IllegalRepoError("The repository name '%s' contains illegal characters!",name)
    self.name = name
    self.path = path

  # Public instance methods
