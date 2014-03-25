"""
module author: Andrew Stucki
"""

class GroupError(Exception):
  """
  Base class for Group errors
  """

class IllegalMemberError(GroupError):
  """
  Member's name contains illegal characters
  """

class IllegalGroupError(GroupError):
  """
  Group name contains illegal characters
  """

class Group:
  """
  Group class
  """

  def __init__(self,name):
    """
    Initialization method
    """
    if ' ' in name:
      raise IllegalGroupError("The group name '%s' contains illegal characters!",name)
    self.name = name
    self.__members = []
    self.__groups = []
    self.__permissions = {}

  # Public instance methods

  def get_permissions(self,):
    """
    Returns the group permissions
    """
    return self.__permissions

  def get_groups(self,):
    """
    Returns the subgroups of this Group mapped to
    readable names.
    """
    return map(lambda x: x[1:], self.__groups)

  def get_direct_members(self,):
    """
    Returns only the members of the group that
    are immediately defined in the configuration file,
    not members of this Group's subgroups.
    """
    return self.__members

  # Protected instance methods

  def _add_members(self,members,):
    """
    Adds multiple members to the group, returns all
    of the members as defined in the configuration file
    (members + subgroups)
    """
    for member in members:
      if ' ' in member:
        raise IllegalMemberError("The member name '%s' contains illegal characters!" % member)
      elif member.startswith("@"):
        self.__groups.append(member)
      else:
        self.__members.append(member)
    return self.__get_members_with_groups()

  def _add_member(self,member,):
    """
    Adds single member to the group.
    """
    if ' ' in member:
      raise IllegalMemberError("The member name '%s' contains illegal characters!" % member)
    elif member.startswith("@"):
      self.__groups.append(member)
    else:
      self.__members.append(member)
    return self.__get_members_with_groups()

  def _remove_member(self,member,):
    """
    Removes member from a group.
    """
    if ' ' in member: 
      raise IllegalMemberError("The member name '%s' contains illegal characters!" % member)
    elif member.startswith("@"):
      self.__groups.remove(member)
    else:
      self.__members.remove(member)
    return self.__members

  def _remove_members(self,members,):
    """
    Removes multiple members from a group.
    """
    for member in members:
      if ' ' in member: 
        raise IllegalMemberError("The member name '%s' contains illegal characters!" % member)
      elif member.startswith("@"):
        if member in self.__groups:
          self.__groups.remove(member)
      elif member in self.__members:
        self.__members.remove(member)
    return self.__get_members_with_groups()

  def _add_repo_permission(self,type,repo,):
    """
    Adds permissions to a repo for this group
    """
    if type in self.__permissions.keys():
      self.__permissions[type].append(repo)
    else:
      self.__permissions[type]=[repo]
    return self.__permissions

  def _remove_repo_permission(self,type,repo,):
    """
    Removes permissions of given type from the group
    returns current permissions of given type
    """
    self.__permissions[type].remove(repo)
    return self.__permissions[type]

  def _set_permissions(self,perms,):
    self.__permissions = perms

  # Private instance methods

  def __get_members_with_groups(self,):
    """
    Returns the members + subgroups for this Group
    """
    retval = []
    retval.extend(self.__members)
    retval.extend(self.__groups)
    return retval
