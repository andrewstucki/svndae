"""
module author: Andrew Stucki
"""

import os
import ConfigParser

from svndae import util
from svndae.group import Group
from svndae.repository import Repo

class SvndaeConfigError(Exception):
  """
  Parent configuration error
  """

class ConfigPathError(SvndaeConfigError):
  """
  Configuration File not found on path!
  """

class EmptyConfigError(SvndaeConfigError):
  """
  Configuration File is empty
  """

class NonExistantGroupError(SvndaeConfigError):
  """
  User specified a non-existant group
  """

class BadPermissionError(SvndaeConfigError):
  """
  User specified a bad permission
  """

class NonExistantRepositoryError(SvndaeConfigError):
  """
  Bad Repository name specified
  """

class SvndaeConfig:
  """
  Class for describing and interacting with the project configuration file.
  """
  
  # Protected configuration variables
  _WRITE = "write"
  _READ = "read"
  _KEYDIR = "keydir"
  _KEYFILE = "authorized_keys"
  _DEFAULT_CONF = "svndae.conf"
  _ALL_REPOS = "@all"

  # Private configuration variables
  __MAIN_SECTION = "svndae"
  __GROUP_PREFIX = "group "
  __REPO_PREFIX = "repo "
  __MEMBER_AREA = "members"
  __REPO_PATH_FIELD = "path"
  __DEFAULT_FIELDS = {__MAIN_SECTION: [_KEYDIR,_KEYFILE],__GROUP_PREFIX: [__MEMBER_AREA,_WRITE,_READ], __REPO_PREFIX: [__REPO_PATH_FIELD]}

  def generate_config(__class,path,name,keydir,keyfile):
    """
    Class method that initializes a basic configuration file
    """
    keypath = os.path.join(path,keydir)
    new_cfg = ConfigParser.RawConfigParser()
    new_cfg.add_section(__class.__MAIN_SECTION)
    new_cfg.set(__class.__MAIN_SECTION,__class._KEYDIR,keypath)
    new_cfg.set(__class.__MAIN_SECTION,__class._KEYFILE,keyfile)
    new_cfg.write(open(os.path.join(path,name),'w'))
  generate_config = classmethod(generate_config)

  def __init__(self,path,name=None,):
    """
    Initialization function, sets up Groups and Repositories as defined
    in the configuration file.
    """
    if name is None:
      name = self._DEFAULT_CONF
    self.path = path
    self.name = name
    self.groups = {}
    self.repos = {}
    self.__config = ConfigParser.RawConfigParser()
    if not self.__config.read(self.get_full_path()):
      raise ConfigPathError("Unable to find the configuration file: '%s'!" % self.get_full_path())
    if not self.__config.sections() or self.__MAIN_SECTION not in self.__config.sections():
      raise EmptyConfigError(
                             "Configuration file: '%s' missing necessary '%s' section!"
                             % (self.get_full_path(),self.__MAIN_SECTION)
                             )
    for section in self.__config.sections():
      if section.startswith(self.__GROUP_PREFIX):
        group_name = section[len(self.__GROUP_PREFIX):]
        self.groups[group_name] = Group(group_name)
        members = self.__group_members_as_list(group_name)
        self.groups[group_name]._add_members(members)
        permissions = self.__group_permissions(group_name)
        self.groups[group_name]._set_permissions(permissions)
      elif section.startswith(self.__REPO_PREFIX):
        repo_name = section[len(self.__REPO_PREFIX):]
        self.repos[repo_name] = Repo(repo_name)

  # Public instance methods

  def get_full_path(self,):
    """
    Returns the full path to the configuration file.
    """
    return os.path.join(self.path,self.name)

  def get_conf_param(self,key,):
    """
    Grab main section configuration parameter, all other sections
    interact via objects.
    """
    return self.__grab_value(self.__MAIN_SECTION,key)

  def expand_group_membership(self,group,previous_groups=None):
    """
    Gets the full listing of members who are assigned to groups,
    as groups can contain other groups for members. Handles circular
    references by doing a "union" operation.
    """
    if group in self.groups.keys():
      members = self.groups[group].get_direct_members()
      for new_group in self.groups[group].get_groups():
        if previous_groups and new_group in previous_groups:
          continue
        elif previous_groups:
          previous_groups.append(group)
        else:
          previous_groups = [group]
        members.extend(self.expand_group_membership(new_group,previous_groups))
      return self.__uniq(members)
    else:
      if previous_groups:
        # clean up the Group because someone added a non-existant group
        self.remove_member_or_subgroup_from_group("@%s" % group,previous_groups[-1])
        return []
      else:
        # the group asked to expand is invalid
        raise NonExistantGroupError("The group '%s' does not yet exist!" % group)

  def add_member_or_subgroup_to_group(self,user,group,):
    """
    Adds a member to a group as defined in the configuration file,
    also adds the member to the Group object representing the group.
    """
    if group in self.groups.keys():
      members = self.groups[group]._add_member(user)
      self.__update_group_membership(group,members)
    else:
      raise NonExistantGroupError("The group '%s' does not yet exist!" % group)

  def add_members_or_subgroups_to_group(self,users,group,):
    """
    Adds multiple members to a Group.
    """
    if group in self.groups.keys():
      members = self.groups[group]._add_members(users)
      self.__update_group_membership(group,members)
    else:
      raise NonExistantGroupError("The group '%s' does not yet exist!" % group)

  def remove_member_or_subgroup_from_group(self,user,group,):
    """
    Removes a member from a group as defined in the configuration file,
    also removes the member from the Group object representing the group.
    """
    if group in self.groups.keys():
      members = self.groups[group]._remove_member(user)
      self.__update_group_membership(group,members)
    else:
      raise NonExistantGroupError("The group '%s' does not yet exist!" % group)

  def remove_members_or_subgroups_from_group(self,users,group,):
    """
    Removes multiple members from a Group.
    """
    if group in self.groups.keys():
      members = self.groups[group]._remove_members(users)
      self.__update_group_membership(group,members)
    else:
      raise NonExistantGroupError("The group '%s' does not yet exist!" % group)

  def unset_permission(self,group,type,repo):
    """
    Removes permission for a repo from a group
    """
    if group in self.groups.keys():
      perms = self.groups[group]._remove_repo_permission(type,repo)
      self.__update_group_permissions(group,perms)
    else:
      raise NonExistantGroupError("The group '%s' does not yet exist!" % group)

  def add_permission(self,group,type,repo):
    """
    Adds permission for a repo to a group
    """
    if group in self.groups.keys():
      if type is not self._WRITE and type is not self._READ:
        raise BadPermissionError("The specified permission type '%s' is invalid!" % type)
      if repo not in self.repos.keys() and repo != self._ALL_REPOS:
        raise NonExistantRepositoryError("The repository '%s' does not have an entry!" % repo)
      perms = self.groups[group]._add_repo_permission(type,repo)
      self.__update_group_permissions(group,perms)
    else:
      raise NonExistantGroupError("The group '%s' does not yet exist!" % group)

  def create_group(self,group):
    """
    Adds a new group to the configuration file
    """
    self.groups[group] = Group(group)
    self.__add_section("%s%s" % (self.__GROUP_PREFIX,group))
    self.__add_section_value("%s%s" % (self.__GROUP_PREFIX,group),self.__MEMBER_AREA,'',)

  def remove_group(self,group):
    """
    Removes a group
    """
    if group in self.groups.keys():
      del self.groups[group]
      self.__remove_section("%s%s" % (self.__GROUP_PREFIX,group))
    else:
      raise NonExistantGroupError("The group '%s' does not yet exist!" % group)

  def create_repo(self,repo,path=None):
    """
    Adds a new repository to the configuration file
    """
    self.repos[repo] = Repo(repo,path)
    self.__add_section("%s%s" % (self.__REPO_PREFIX,repo))
    if path:
      self.__update_repo_path(repo,path)

  def remove_repo(self,repo):
    """
    Removes a repository
    """
    if repo in self.repos.keys():
      del self.repos[repo]
      self.__remove_section("%s%s" % (self.__REPO_PREFIX,repo))
    else:
      raise NonExistantRepositoryError("The repository '%s' does not have an entry!" % repo)

  def clean_config(self,):
    """
    Clean the configuration file from invalid entries
    """
    for group_name,group in self.groups.items():
      for subgroup in group.get_groups():
        if subgroup not in self.groups.keys():
          self.remove_member_or_subgroup_from_group("@%s" % subgroup,group_name)
      for key in self.__DEFAULT_FIELDS[self.__GROUP_PREFIX]:
        section = "%s%s" % (self.__GROUP_PREFIX,group_name)
        try:
          values = self.__grab_value(section,key).split()
          if key is self._WRITE or key is self._READ:
            for value in values:
              if value not in self.repos.keys():
                self.unset_permission(group_name,key,value)
        except ConfigParser.NoOptionError:
          self.__add_section_value(section,key,'')

  # Private instance methods
  
  def __add_section(self,section,):
    """
    Adds a new section the the configuration file
    """
    self.__config.add_section(section,)
    self.__config.write(open(self.get_full_path(),'wb'))

  def __remove_section(self,section,):
    """
    Removes a section from the configuration file
    """
    self.__config.remove_section(section,)
    self.__config.write(open(self.get_full_path(),'wb'))

  def __grab_value(self,section,key,):
    """
    Wrapper to get a section from the configuration file
    """
    return self.__config.get(section,key)

  def __add_section_value(self,section,key,value,):
    """
    Wrapper to add a section value to the configuration file
    """
    self.__config.set(section,key,value)
    self.__config.write(open(self.get_full_path(),'wb'))

  def __group_members_as_string(self,group,):
    """
    Parsed through the configuration file and returns the members
    of a Group in string form.
    """
    return self.__config.get("%s%s" % (self.__GROUP_PREFIX,group),self.__MEMBER_AREA)

  def __group_members_as_list(self,group,):
    """
    Returns the members of a Group in list form
    """
    return self.__group_members_as_string(group).split()

  def __group_permissions(self,group,):
    """
    Returns a dict of permissions for the group
    """
    section = "%s%s" % (self.__GROUP_PREFIX,group)
    perms = {}
    try:
      perms[self._WRITE] = self.__grab_value(section,self._WRITE).split()
    except ConfigParser.NoOptionError:
      self.__add_section_value(section,self._WRITE,'')
      perms[self._WRITE] = []
    try:
      perms[self._READ] = self.__grab_value(section,self._READ).split()
    except ConfigParser.NoOptionError:
      self.__add_section_value(section,self._READ,'')
      perms[self._READ] = []
    return perms

  def __update_group_membership(self,group,members,):
    """
    Updates the members of a group in the configuration file.
    """
    self.__add_section_value("%s%s" % (self.__GROUP_PREFIX,group), self.__MEMBER_AREA," ".join(members))

  def __update_group_permissions(self,group,perms,):
    """
    Updates the permissions of a group in the configuration file.
    """
    for (type,repos) in perms.items():
      self.__add_section_value("%s%s" % (self.__GROUP_PREFIX,group), type," ".join(repos))
  
  def __update_repo_path(self,repo,path,):
    """
    Updates the path of a repository in the configuration file.
    """
    self.__add_section_value("%s%s" % (self.__REPO_PREFIX,repo), self.__REPO_PATH_FIELD,path)

  def __uniq(self,list,):
    """
    Removes duplicates from a list.
    """
    if not list:
      return []
    keys = {}
    for l in list:
      keys[l] = 1
    return keys.keys()
