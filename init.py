import os
import sys
import logging
import optparse
import ConfigParser

from svndae.config import SvndaeConfig
from svndae import util
from svndae.interactive_init import initialize

log = logging.getLogger('svndae.app')
DEFAULT_DIR = os.path.join('~','.svndae')
DEFAULT_AUTH_KEYS = os.path.join('~','.ssh','authorized_keys')
DEFAULT_KEYDIR = 'keys'
ADMIN_GROUP = 'admins'

class Init(object):
  name = None

  def run(class_):
    app = class_()
    return app.main()
  run = classmethod(run)

  def main(self):
    parser = self.create_parser()
    (options, args) = parser.parse_args()
    if options.interactive:
      initialize()
    else:
      print "\nInitializing file system in '%s'" % options.path
      util.mkdir(options.path)
      util.mkdir(os.path.join(options.path,options.dir))
      print "Generating configuration file '%s'" % options.conf
      SvndaeConfig.generate_config(options.path,options.conf,options.dir,options.file)
      config = SvndaeConfig(options.path,name=options.conf)
      print "Adding default administrative groups"
      config.create_group(ADMIN_GROUP)
      config.add_permission(ADMIN_GROUP,SvndaeConfig._WRITE,SvndaeConfig._ALL_REPOS)
      config.add_permission(ADMIN_GROUP,SvndaeConfig._READ,SvndaeConfig._ALL_REPOS)
      print "Initialization finished!\n"
      print "You can now add users to the file system with the '%s' command!\n" % 'svndae-addkeys'

  def setup_basic_logging(self):
    logging.basicConfig()

  def create_parser(self):
    parser = optparse.OptionParser()
    parser.set_defaults(
      path=os.path.expanduser(DEFAULT_DIR),
      dir=DEFAULT_KEYDIR,
      conf=SvndaeConfig._DEFAULT_CONF,
      file=os.path.expanduser(DEFAULT_AUTH_KEYS),
      interactive=False,
    )
    parser.add_option('-i','--interactive',action="store_true",help='run in interactive mode')
    parser.add_option('-p','--path',metavar='PATH',help='path to svndae files',)
    parser.add_option('-d','--dir',metavar='DIR',help='directory that will hold svndae keys',)
    parser.add_option('-c','--conf',metavar='FILE',help='name of the svndae configuration file')
    parser.add_option('-f','--file',metavar='FILE',help='path of the authorized keys file to manage')
    return parser
