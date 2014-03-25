from os.path import exists,abspath,expanduser,join,dirname
import init
import util
from config import SvndaeConfig

def print_confirmation_error():
  print '\n ERROR:\n  Bad input, please give \'y\', \'n\', or hit enter!\n'

def print_heading(title):
  div = '-'*len(title)
  print '\n%s\n%s\n%s\n' % (div,title,div)

def print_final():
  print '\nCongratulations, you have configured everything!\n'

def print_table(dict_vals,key_head,val_head):
  def __padding(length,sub_length=0):
    v1 = ' '*int(float(length-sub_length)/2)
    if (length-sub_length) % 2:
      return(v1,v1+' ')
    return(v1,v1)

  def __row(pad1,val1,pad1_1,pad2,val2,pad2_2):
    return '%s%s%s|%s%s%s' % (pad1,val1,pad1_1,pad2,val2,pad2_2)

  # for offset vals
  longest_key = 0
  longest_val = 0
  for (key,val) in dict_vals.items():
    if '\n' in val:
      vals = val.split('\n')
      val = vals[0]
      for val_n in vals:
        if len(val_n) > len(val):
          val = val_n
    if len(key) > longest_key:
      longest_key = len(key)
    if len(val) > longest_val:
      longest_val = len(val)
  if len(key_head) > longest_key:
    longest_key = len(key_head)
  if len(val_head) > longest_val:
    longest_val = len(val_head)
  longest_key+=2
  longest_val+=2

  (k_sep,k_sep2) = __padding(longest_key,len(key_head))
  (v_sep,v_sep2) = __padding(longest_val,len(val_head))
  header = __row(k_sep,key_head,k_sep2,v_sep,val_head,v_sep2)
  print '='*len(header)
  print header
  print '='*len(header)

  for (key,val) in dict_vals.items():
    if '\n' in val:
      vals = val.split('\n')
      first_val = True
      for val in vals:
        if first_val:
          first_val = False
          (k_sep,k_sep2) = __padding(longest_key,len(key))
        else:
          (k_sep,k_sep2) = __padding(longest_key)
          key = ''
        (v_sep,v_sep2) = __padding(longest_val,len(val))
        row = __row(k_sep,key,k_sep2,v_sep,val,v_sep2)
        print row
    else:
      (k_sep,k_sep2) = __padding(longest_key,len(key))
      (v_sep,v_sep2) = __padding(longest_val,len(val))
      row = __row(k_sep,key,k_sep2,v_sep,val,v_sep2)
      print row
    print '-'*len(row)

def validate_path_input(prompt,path='',create=False):
  kludge_flag = True
  while path == '' or kludge_flag:
    kludge_flag = False
    path_in = raw_input(prompt)
    if path_in != '':
      path = path_in
    if exists(abspath(path)) and path != '':
      return abspath(path)
    elif create and exists(dirname(abspath(path))):
      return abspath(path)
    print '\n ERROR:\n  Bad path, please give a relative or absolute path!\n'
    path = ''

def get_user_groups(config,groups=[],group_perms={}):
  print_heading('Please enter the information for the groups you would like to add.')
  done = False
  while not done:
    group = raw_input(' Group name: ')
    groups.append(group)
    if config.repos:
      while True:
        prompt_in = raw_input('\nWould you like to add any group permissions for configured repositories? ([y]/n) ')
        if prompt_in == '' or prompt_in == 'y':
          print 'The following repositories have been added:'
          repos = []
          index = 0
          for repo in config.repos.keys():
            index+=1
            repos.append(repo)
            print "%s) %s" % (index,repo)
          try:
            selection = int(raw_input('Please choose a number from above: '))
            if selection < 1 or selection > index:
              raise
          except:
            print '\n ERROR:\n Invalid repository selection\n'
            continue
          try:
            type = int(raw_input('Please choose an access restriction (0 = r, 1 = w, 2 = r/w): '))
            if type > 2 or type < 0:
              raise
          except:
            print '\n ERROR:\n  Bad restriction selection!\n'
            continue
          if group in group_perms.keys():
            group_perms[group][repos[selection-1]] = type
          else:
            group_perms[group] = {repos[selection-1]: type}
        elif prompt_in == 'n':
          break
        else:
          print_confirmation_error()
    while True:
      prompt_in_2 = raw_input('Are you finished adding groups? ([y]/n) ')
      if prompt_in_2 == '' or prompt_in_2 == 'y':
        done = True
        break
      elif prompt_in_2 == '' or prompt_in_2 == 'n':
        break
      else:
        print_confirmation_error()
  confirm_groups(config,groups,group_perms)

def confirm_groups(config,groups,group_perms):
  groups_extended = {}
  perms = ['read','write','read/write']
  for group in groups:
    groups_extended[group]=''
    if group in group_perms.keys():
      first_perm = True
      for repo,perm in group_perms[group].items():
        if first_perm:
          first_perm = False
          groups_extended[group] = "%s: %s" % (repo,perms[perm])
        else:
          groups_extended[group] = "%s: %s\n%s" % (repo,perms[perm],groups_extended[group])
  print_heading('Please check that the following information is correct:')
  print_table(groups_extended,'Groups','ACL')
  while True:
    correct_in = raw_input('Is this correct? ([y]/n)')
    if correct_in == '' or correct_in == 'y':
      break
    elif correct_in == 'n':
      get_user_groups(config,groups,group_perms)
      break
    else:
      print_confirmation_error()
  print('\nAdding groups to configuration.')
  for group in groups:
    config.create_group(group)
    if group in group_perms.keys():
      for repo,perm in group_perms[group].items():
        if perm > 0:
          config.add_permission(group,SvndaeConfig._WRITE,repo)
        if (perm % 2) == 0:
          config.add_permission(group,SvndaeConfig._READ,repo)

def get_repo_manage(config,repositories={}):
  repository = ''
  path = ''
  print_heading('Please enter the information of a repository that you would like to manage.')
  done = False
  while not done:
    while repository == '':
      repository = raw_input(' Repository name: ')
    while path == '': 
      path = validate_path_input(' Path to repository: ')
    repositories[repository]=path
    done_input = raw_input(' Are you finished adding repositories? ([y]/n) ')
    if done_input == '' or done_input == 'y':
      done = True
    elif done_input == 'n':
      print ''
      repository = ''
      path = ''
      continue
    else:
      while True:
        print_confirmation_error()
        done_input = raw_input(' Are you finished adding repositories? ([y]/n) ')
        if done_input == '' or done_input == 'y':
          done = True
          break
        elif done_input == 'n':
          print ''
          repository = ''
          path = ''
          break
  confirm_repo(config,repositories)

def confirm_repo(config,repositories):
  print_heading('Please check that the following information is correct:')
  print_table(repositories,'Repository','Path')
  print ''
  while True:
    correct_in = raw_input('Is this correct? ([y]/n)')
    if correct_in == '' or correct_in == 'y':
      break
    elif correct_in == 'n':
      get_repo_manage(config,repositories)
      break
    else:
      print_confirmation_error()
  print('\nAdding repositories to configuration.')
  for repo,path in repositories.items():
    config.create_repo(repo,path)

def get_configuration_defaults(defaults={}):
  prompts = {
             'path': 'Project Path',
             'conf': 'Configuration file name',
             'dir': 'Svndae Key Directory',
             'file': 'Path to authorized_keys',
            }
  prompt_defaults = {
                      'path': expanduser(join('~','.svndae')),
                      'conf': 'svndae.conf',
                      'dir': 'keys',
                      'file': expanduser(init.DEFAULT_AUTH_KEYS),
                    }
  def prefs(key):
    return ' %s: ' % prompts[key],defaults[key]
  
  def default_valid(prompt,default):
    d_in = raw_input(prompt)
    if d_in != '':
      default = d_in
    return default

  for key in prompts.keys():
    if key in defaults.keys():
      prompts[key] = '%s [%s]' % (prompts[key],defaults[key])
    else:
      prompts[key] = '%s [%s]' % (prompts[key],prompt_defaults[key])
      defaults[key] = prompt_defaults[key]

  print_heading('Please enter your preferences for your svndae installation:')
  (k,v)=prefs('path')
  defaults['path'] = validate_path_input(k,v,create=True)
  (k,v) = prefs('conf')
  defaults['conf'] = default_valid(k,v)
  (k,v) = prefs('dir')
  defaults['dir'] = default_valid(k,v)
  (k,v) = prefs('file')
  defaults['file'] = validate_path_input(k,v)

  print_heading('Please check that the following information is correct:')
  print_table(defaults,'Parameter','Value')
  print ''
  ending=False
  while not ending:
    correct_in = raw_input('Is this correct? ([y]/n) ')
    if correct_in == '' or correct_in == 'y':
      ending=True
    elif correct_in == 'n':
      ending=True
      get_configuration_defaults(defaults)
    else:
      print_confirmation_error()
  return defaults

def initialize():
  print '\nWelcome to the interactive Svndae configuration!'
  options = get_configuration_defaults()
  print "\nInitializing file system in '%s'" % options['path']
  util.mkdir(options['path'])
  util.mkdir(join(options['path'],options['dir']))
  print "Generating configuration file '%s'" % options['conf']
  SvndaeConfig.generate_config(options['path'],options['conf'],options['dir'],options['file'])
  config = SvndaeConfig(options['path'],name=options['conf'])
  print "Adding default administrative groups"
  config.create_group(init.ADMIN_GROUP)
  config.add_permission(init.ADMIN_GROUP,SvndaeConfig._WRITE,SvndaeConfig._ALL_REPOS)
  config.add_permission(init.ADMIN_GROUP,SvndaeConfig._READ,SvndaeConfig._ALL_REPOS)
  while True:
    correct_in = raw_input('Would you like to add any repository ACLs? ([y]/n) ')
    if correct_in == '' or correct_in == 'y':
      get_repo_manage(config)
      break
    elif correct_in == 'n':
      break
    else:
      print_confirmation_error()
  while True:
    correct_in = raw_input('Would you like to add any additional groups? ([y]/n) ')
    if correct_in == '' or correct_in == 'y':
      get_user_groups(config)
      break
    elif correct_in == 'n':
      break
    else:
      print_confirmation_error()
  print_final()

if __name__ == '__main__':
  initialize()
