# -*- coding: utf-8 -*-

import os
import falcon
import logging as log
import json
import codecs
import pexpect

from oslo_config import cfg

switch_opt = cfg.StrOpt('switch_conf',
                        default='./switch.json',
                        help='switch config file name')


def is_json(string=str()):
    try:
        json.loads(string)
    except ValueError as err:
        log.debug("is_json: %s" % str(err))
        return False
    return True


def load_switch_from_conf(file_name):
    log.debug('load switch from conf: %s' % file_name)
    results = dict()
    if os.path.exists(file_name):
        try:
            results = json.load(codecs.open(file_name, 'r', 'utf-8-sig'))
        except Exception as err:
            log.exception("read_json_file: %s" % str(err))
    else:
        log.debug("read_json_file: %s file does not exist." % file_name)

    return results


def ssh_cmd(user='root', password='', ip='localhost',
            port=22, cmd=None, echo=False):
    if not cmd:
        return 1, None

    status = 0
    results = None
    login = 'ssh -l %(user)s %(ip)s -p %(port)d "%(cmd)s"' % \
            {"user": user, "ip": ip, "port": port, "cmd": cmd}
    ssh = pexpect.spawn(login)
    try:
        i = ssh.expect(['password:', 'continue connecting (yes/no)?'],
                       timeout=5)
        if i == 0:
            ssh.sendline(password)
        elif i == 1:
            ssh.sendline('yes')
            ssh.expect('password:')
            ssh.sendline(password)

        ssh.sendline(cmd)
        if echo:
            results = ssh.read()
        status = 0
    except pexpect.EOF as ex:
        log.exception(ex)
        status = 2
    except pexpect.TIMEOUT as ex:
        log.exception(ex)
        status = 3
    finally:
        ssh.close()
        return status, results


class Switch(object):
    def __init__(self):
        self.switches = load_switch_from_conf("./switch.json")

    def on_post(self, req, res):
        try:
            body = json.load(req.stream)
        except Exception as ex:
            log.exception(ex)
            raise falcon.HTTPInternalServerError('Service unavailable',
                                                 str(ex))

        log.debug("body: %s" % json.dumps(body))

        if "firing" == body.get("status") and len(body.get("alerts")) > 20:
            cmd = "reset l2vpn mac-address"
            for sw in self.switches:
                status, results = ssh_cmd(user=sw.get('user'),
                                          password=sw.get('pwd'),
                                          ip=sw.get('ip'),
                                          port=sw.get('port', 22),
                                          cmd=sw.get('cmd', cmd),
                                          echo=sw.get('echo', False))
                if status == 0:
                    log.debug("'%s' ok." % sw.get('cmd', cmd))
                else:
                    log.debug("'%s' Faild." % sw.get('cmd', cmd))
        else:
            log.error("message format error.")

        res.status = falcon.HTTP_200