import os
import sys
import logging
import optparse
import errno
import ConfigParser

from svndae.config import SvndaeConfig
from svndae.ssh import writeAuthorizedKeys

log = logging.getLogger('svndae.app')

DEFAULT_DIR = os.path.join('~','.svndae','svndae.conf')

class App(object):
  name = None

  def run(class_):
    app = class_()
    return app.main()
  run = classmethod(run)

  def main(self):
    self.setup_basic_logging()
    parser = self.create_parser()
    (options, args) = parser.parse_args()
    (conf_path,conf_name) = os.path.split(options.conf)
    cfg = SvndaeConfig(conf_path,name=conf_name)
    path = cfg.get_conf_param('authorized_keys')
    keydir = cfg.get_conf_param('keydir')
    writeAuthorizedKeys(path,keydir)

  def setup_basic_logging(self):
    logging.basicConfig()

  def create_parser(self):
    parser = optparse.OptionParser()
    parser.set_defaults(
      conf=os.path.expanduser(DEFAULT_DIR),
    )
    parser.add_option('--conf',metavar='PATH',help='path to svndae configuration file',)
    return parser
