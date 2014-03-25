import os
from nose.tools import eq_ as eq, assert_raises, assert_true
from ConfigParser import RawConfigParser

from svndae.config import *
from svndae.group import IllegalMemberError,IllegalGroupError
from svndae.test import util

def test_non_existant_config():
  assert_raises(ConfigPathError,SvndaeConfig,'.',name='I_do_not_exist')

def test_empty_config():
  tmp = util.maketemp()
  path = os.path.join(tmp,'empty.conf')
  util.touch(path)
  assert_raises(EmptyConfigError,SvndaeConfig,tmp,name='empty.conf')

def test_config_init_path():
  tmp = util.maketemp()
  cfg = RawConfigParser()
  cfg.add_section('svndae')
  
  # first check the default name conventions in the initializer
  path = os.path.join(tmp,'svndae.conf')
  cfg.write(open(path,'wb'))
  cfg_file = SvndaeConfig(tmp)
  eq(cfg_file.get_full_path(),path)

  # next check overriding the default convention
  path = os.path.join(tmp,'nonstandard.conf')
  cfg.write(open(path,'wb'))
  cfg_file = SvndaeConfig(tmp,name='nonstandard.conf')
  eq(cfg_file.get_full_path(),path)

def test_config_init_detailed():
  tmp = util.maketemp()
  cfg = RawConfigParser()
  cfg.add_section('svndae')
  cfg.add_section('group testgroup')
  cfg.add_section('group testgroup2')
  cfg.add_section('repo testrepo')
  cfg.set('group testgroup','members','testmember @testgroup2')
  cfg.set('group testgroup2','members','testmember2')
  cfg.set('repo testrepo','path','/')

  # uses default name conventions in the initializer
  path = os.path.join(tmp,'svndae.conf')
  cfg.write(open(path,'wb'))
  cfg_file = SvndaeConfig(tmp)
  eq(cfg_file.name,'svndae.conf')
  eq(len(cfg_file.groups),2)
  eq(len(cfg_file.repos),1)
  eq(len(cfg_file.groups['testgroup'].get_permissions()['write']),0)
  eq(len(cfg_file.groups['testgroup'].get_direct_members()),1)
  eq(len(cfg_file.groups['testgroup'].get_groups()),1)
  eq(len(cfg_file.groups['testgroup2'].get_direct_members()),1)
  eq(len(cfg_file.groups['testgroup2'].get_groups()),0)

def test_config_group_functions():
  tmp = util.maketemp()
  cfg = RawConfigParser()
  cfg.add_section('svndae')
  cfg.add_section('group testgroup')
  cfg.add_section('group testgroup2')
  cfg.add_section('group testgroup3')
  cfg.add_section('repo testrepo')
  cfg.set('group testgroup','members','testmember')
  cfg.set('group testgroup2','members','testmember2 @testgroup')
  cfg.set('group testgroup3','members','testmember3 @testgroup3 @testgroup2')
  cfg.set('repo testrepo','path','/')

  path = os.path.join(tmp,'svndae.conf')
  cfg.write(open(path,'wb'))
  cfg_file = SvndaeConfig(tmp)
  tgroup = cfg_file.groups['testgroup']

  # add_member_or_subgroup_to_group tests
  cfg_file.add_member_or_subgroup_to_group('john','testgroup')
  cfg_file.add_member_or_subgroup_to_group('@testgroup','testgroup')
  assert_true('john' in tgroup.get_direct_members())
  assert_true('testgroup' in tgroup.get_groups())
  assert_raises(IllegalMemberError,cfg_file.add_member_or_subgroup_to_group,'john doe','testgroup')
  assert_raises(NonExistantGroupError,cfg_file.add_member_or_subgroup_to_group,'john','nonexistant')

  # remove_member_or_subgroup_from_group tests
  cfg_file.remove_member_or_subgroup_from_group('john','testgroup')
  cfg_file.remove_member_or_subgroup_from_group('@testgroup','testgroup')
  assert_true('john' not in tgroup.get_direct_members())
  assert_true('testgroup' not in tgroup.get_groups())
  assert_raises(IllegalMemberError,cfg_file.remove_member_or_subgroup_from_group,'john doe','testgroup')
  assert_raises(NonExistantGroupError,cfg_file.remove_member_or_subgroup_from_group,'john','nonexistant')

  # add_members_or_subgroups_to_group tests
  cfg_file.add_members_or_subgroups_to_group(['john','jane','@testgroup'],'testgroup')
  assert_true('john' in tgroup.get_direct_members() and 'jane' in tgroup.get_direct_members()) 
  assert_true('testgroup' in tgroup.get_groups())
  assert_raises(IllegalMemberError,cfg_file.add_members_or_subgroups_to_group,['john doe','jane'],'testgroup')
  assert_raises(NonExistantGroupError,cfg_file.add_members_or_subgroups_to_group,['john','jane'],'nonexistant')

  # remove_members_or_subgroups_from_group tests
  cfg_file.remove_members_or_subgroups_from_group(['john','jane','@testgroup'],'testgroup')
  assert_true('john' not in tgroup.get_direct_members() and 'jane' not in tgroup.get_direct_members()) 
  assert_true('testgroup' not in tgroup.get_groups())
  assert_raises(IllegalMemberError,cfg_file.remove_members_or_subgroups_from_group,['john doe','jane'],'testgroup')
  assert_raises(NonExistantGroupError,cfg_file.remove_members_or_subgroups_from_group,['john','jane'],'nonexistant')

  # create_group tests
  cfg_file.create_group('newgroup')
  assert_true('newgroup' in cfg_file.groups.keys())
  assert_raises(IllegalGroupError,cfg_file.create_group,'bad group')

  # remove_group tests
  cfg_file.remove_group('newgroup')
  assert_true('newgroup' not in cfg_file.groups.keys())
  assert_raises(NonExistantGroupError,cfg_file.remove_group,'newgroup')

  # expand_group_membership tests
  eq(cfg_file.groups['testgroup'].get_direct_members(),['testmember'])
  eq(cfg_file.groups['testgroup'].get_groups(),[])
  eq(cfg_file.expand_group_membership('testgroup'),['testmember'])
  eq(cfg_file.groups['testgroup2'].get_direct_members(),['testmember2'])
  eq(cfg_file.groups['testgroup2'].get_groups(),['testgroup'])
  eq(cfg_file.expand_group_membership('testgroup2'),['testmember','testmember2'])
  eq(cfg_file.groups['testgroup3'].get_direct_members(),['testmember3'])
  eq(cfg_file.groups['testgroup3'].get_groups(),['testgroup3','testgroup2'])
  eq(cfg_file.expand_group_membership('testgroup3'),['testmember','testmember3','testmember2'])
  cfg_file.add_member_or_subgroup_to_group('@nogroup','testgroup')
  eq(cfg_file.expand_group_membership('testgroup'),['testmember'])
  assert_true('nogroup' not in tgroup.get_groups())
  assert_raises(NonExistantGroupError,cfg_file.expand_group_membership,'nogroup')

  # add_permission test
  cfg_file.add_permission('testgroup','write','testrepo')
  assert_true('testrepo' in tgroup.get_permissions()['write'])
  assert_true('norepo' not in tgroup.get_permissions().keys())
  assert_raises(BadPermissionError,cfg_file.add_permission,'testgroup','badperm','testrepo')
  assert_raises(NonExistantRepositoryError,cfg_file.add_permission,'testgroup','write','norepo')

  # unset_permission test
  cfg_file.unset_permission('testgroup','write','testrepo')
  assert_true('testrepo' not in tgroup.get_permissions()['write'])
  assert_raises(BadPermissionError,cfg_file.add_permission,'testgroup','badperm','testrepo')

def test_clean_config():
  tmp = util.maketemp()
  cfg = RawConfigParser()
  cfg.add_section('svndae')
  cfg.add_section('group testgroup')
  cfg.add_section('group testgroup2')
  cfg.add_section('group testgroup3')
  cfg.add_section('repo testrepo')
  cfg.set('group testgroup','members','testmember @nonexistant')
  cfg.set('group testgroup','write','norepo testrepo')
  cfg.set('group testgroup2','members','testmember2 @testgroup')
  cfg.set('group testgroup3','members','testmember3 @testgroup3 @testgroup2')
  cfg.set('repo testrepo','path','/')

  path = os.path.join(tmp,'svndae.conf')
  cfg.write(open(path,'wb'))
  cfg_file = SvndaeConfig(tmp)

  assert_true('nonexistant' in cfg_file.groups['testgroup'].get_groups())
  cfg_file.clean_config()
  assert_true('nonexistant' not in cfg_file.groups['testgroup'].get_groups())
