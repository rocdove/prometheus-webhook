# -*- coding: utf-8 -*-

import falcon
import logging as log
import switch

log.basicConfig(level=log.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d]'
                       ' %(levelname)s %(message)s',
                datefmt=' %Y-%b-%d %H:%M:%S',
                filename='webhook.log',
                filemode='w')


def lunch(conf):
    api = falcon.API()
    
    sw = switch.Switch()
    api.add_route("/alert/v1.0/switch", sw)

    return api

