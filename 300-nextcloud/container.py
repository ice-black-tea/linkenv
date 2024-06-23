#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author  : Hu Ji
@file    : deploy.py 
@time    : 2023/05/21
@site    :  
@software: PyCharm 

              ,----------------,              ,---------,
         ,-----------------------,          ,"        ,"|
       ,"                      ,"|        ,"        ,"  |
      +-----------------------+  |      ,"        ,"    |
      |  .-----------------.  |  |     +---------+      |
      |  |                 |  |  |     | -==----'|      |
      |  | $ sudo rm -rf / |  |  |     |         |      |
      |  |                 |  |  |/----|`---=    |      |
      |  |                 |  |  |   ,/|==== ooo |      ;
      |  |                 |  |  |  // |(((( [33]|    ,"
      |  `-----------------'  |," .;'| |((((     |  ,"
      +-----------------------+  ;;  | |         |,"
         /_)______________(_/  //'   | +---------+
    ___________________________/___  `,
   /  oooooooooooooooo  .o.  oooo /,   `,"-----------
  / ==ooooooooooooooo==.o.  ooo= //   ,``--{)B     ,"
 /_==__==========__==_ooo__ooo=_/'   /___________,"
"""
import os
import random
import string

from linktools import Config
from linktools.cli import subcommand
from linktools.container import BaseContainer, ExposeLink
from linktools.decorator import cached_property


class Container(BaseContainer):

    @property
    def dependencies(self) -> [str]:
        return ["nginx"]

    @cached_property
    def configs(self):
        return dict(
            NEXTCLOUD_TAG="latest",
            NEXTCLOUD_DOMAIN=self.get_nginx_domain(),
            NEXTCLOUD_MYSQL_ROOT_PASSWORD="root_password",
            NEXTCLOUD_MYSQL_DATABASE="nas",
            NEXTCLOUD_MYSQL_USER="nas",
            NEXTCLOUD_MYSQL_PASSWORD="password",
            NEXTCLOUD_ONLYOFFICE_ENABLED=False,
            NEXTCLOUD_ONLYOFFICE_SECRET=Config.Alias(default="".join(random.sample(string.ascii_letters + string.digits, 12)), cached=True),
            NEXTCLOUD_MAINTENANCE_WINDOW_START=2,
            NEXTCLOUD_PHP_MEMORY_LIMIT=None,
            NEXTCLOUD_PHP_UPLOAD_LIMIT=None,
        )

    @cached_property
    def exposes(self) -> [ExposeLink]:
        return [
            self.expose_public("Nextcloud", "cloudDownloadOutline", "私人网盘", self.load_nginx_url("NEXTCLOUD_DOMAIN")),
        ]

    @subcommand("scan", help="scan all files")
    def on_exec_scan(self):
        self.manager.create_docker_process(
            "exec", "nextcloud", "./occ", "files:scan", "--all"
        ).check_call()

    def on_starting(self):
        self.write_nginx_conf(
            self.manager.config.get("NEXTCLOUD_DOMAIN"),
            self.get_path("nginx.conf"),
        )

    def on_started(self):
        uid = self.manager.config.get("DOCKER_UID")
        if os.stat(self.get_app_path()).st_uid != uid:
            self.manager.change_owner(
                self.get_app_path(),
                self.manager.config.get("DOCKER_USER"),
            )
