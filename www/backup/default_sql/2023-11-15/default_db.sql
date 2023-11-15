BEGIN TRANSACTION;
CREATE TABLE `backup` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `type` INTEGER,
  `name` TEXT,
  `pid` INTEGER,
  `filename` TEXT,
  `size` INTEGER,
  `addtime` TEXT
, ps STRING DEFAULT '无');
CREATE TABLE `binding` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pid` INTEGER,
  `domain` TEXT,
  `path` TEXT,
  `port` INTEGER,
  `addtime` TEXT
);
CREATE TABLE `config` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `webserver` TEXT,
  `backup_path` TEXT,
  `sites_path` TEXT,
  `status` INTEGER,
  `mysql_root` TEXT
);
INSERT INTO "config" VALUES(1,'nginx','/www/backup','/www/wwwroot',0,'admin');
CREATE TABLE `crontab` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` TEXT,
  `type` TEXT,
  `where1` TEXT,
  `where_hour` INTEGER,
  `where_minute` INTEGER,
  `echo` TEXT,
  `addtime` TEXT
, 'status' INTEGER DEFAULT 1, 'save' INTEGER DEFAULT 3, 'backupTo' TEXT DEFAULT off, 'sName' TEXT, 'sBody' TEXT, 'sType' TEXT, 'urladdress' TEXT, 'save_local' INTEGER DEFAULT 0, 'notice' INTEGER DEFAULT 0, 'notice_channel' TEXT DEFAULT '');
CREATE TABLE `database_servers` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`db_host` REAL,
`db_port` REAL,
`db_user` INTEGER,
`db_password` INTEGER,
`ps` REAL,
`addtime` INTEGER
, db_type REAL DEFAULT 'mysql');
CREATE TABLE `databases` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pid` INTEGER,
  `name` TEXT,
  `username` TEXT,
  `password` TEXT,
  `accept` TEXT,
  `ps` TEXT,
  `addtime` TEXT
, db_type integer DEFAULT '0', conn_config STRING DEFAULT '{}', sid integer DEFAULT 0, type TEXT DEFAULT MySQL);
CREATE TABLE `div_list` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`div` TEXT
);
INSERT INTO "div_list" VALUES(1,'0Ltt+nq9pDsfDSQ40HXEq2imxP/RAoblQkH1G0uJg6Q=');
CREATE TABLE `domain` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pid` INTEGER,
  `name` TEXT,
  `port` INTEGER,
  `addtime` TEXT
);
CREATE TABLE `download_token` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`token` REAL,
`filename` REAL,
`total` INTEGER DEFAULT 0,
`expire` INTEGER,
`password` REAL,
`ps` REAL,
`addtime` INTEGER
);
CREATE TABLE `firewall` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `port` TEXT,
  `ps` TEXT,
  `addtime` TEXT
);
INSERT INTO "firewall" VALUES(2,'80','网站默认端口','0000-00-00 00:00:00');
INSERT INTO "firewall" VALUES(3,'8888','WEB面板','0000-00-00 00:00:00');
INSERT INTO "firewall" VALUES(4,'21','FTP服务','0000-00-00 00:00:00');
INSERT INTO "firewall" VALUES(5,'22','SSH远程管理服务','0000-00-00 00:00:00');
CREATE TABLE `ftps` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pid` INTEGER,
  `name` TEXT,
  `password` TEXT,
  `path` TEXT,
  `status` TEXT,
  `ps` TEXT,
  `addtime` TEXT
);
CREATE TABLE `logs` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `type` TEXT,
  `log` TEXT,
  `addtime` TEXT
, uid integer DEFAULT '1', username TEXT DEFAULT 'system');
CREATE TABLE `messages` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`level` TEXT,
`msg` TEXT,
`state` INTEGER DEFAULT 0,
`expire` INTEGER,
`addtime` INTEGER
, send integer DEFAULT 0, retry_num integer DEFAULT 0);
CREATE TABLE `security` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `type` TEXT,
    `log` TEXT,
    `addtime` INTEGER DEFAULT 0
    );
INSERT INTO "security" VALUES(1,'安全入口正确','103.220.11.98:8076访问安全入口成功','2023-11-14 10:12:35');
INSERT INTO "security" VALUES(2,'登录成功','103.220.11.98:8087','2023-11-14 10:12:54');
CREATE TABLE "send_msg" ("id" INTEGER PRIMARY KEY AUTOINCREMENT,"name" TEXT,"send_type" TEXT,"msg" TEXT,"is_send" TEXT,"type" TEXT,"inser_time" TEXT DEFAULT '');
CREATE TABLE "send_settings" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,"name" TEXT,"type" TEXT,"path" TEXT,"send_type" TEXT,"last_time" TEXT ,"time_frame" TEXT,"inser_time" TEXT DEFAULT'');
CREATE TABLE `site_types` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`name` REAL,
`ps` REAL
);
CREATE TABLE `sites` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` TEXT,
  `path` TEXT,
  `status` TEXT,
  `index` TEXT,
  `ps` TEXT,
  `addtime` TEXT
, type_id integer DEFAULT 0, edate integer DEFAULT '0000-00-00', project_type STRING DEFAULT 'PHP', project_config STRING DEFAULT '{}');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('config',1);
INSERT INTO "sqlite_sequence" VALUES('firewall',5);
INSERT INTO "sqlite_sequence" VALUES('users',1);
INSERT INTO "sqlite_sequence" VALUES('div_list',1);
INSERT INTO "sqlite_sequence" VALUES('security',2);
INSERT INTO "sqlite_sequence" VALUES('logs',1);
CREATE TABLE `task_list` (
  `id`              INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` 			TEXT,
  `type`			TEXT,
  `status` 			INTEGER,
  `shell` 			TEXT,
  `other`           TEXT,
  `exectime` 	  	INTEGER,
  `endtime` 	  	INTEGER,
  `addtime`			INTEGER
);
CREATE TABLE `tasks` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` 			TEXT,
  `type`			TEXT,
  `status` 		TEXT,
  `addtime` 	TEXT,
  `start` 	  INTEGER,
  `end` 	    INTEGER,
  `execstr` 	TEXT
);
CREATE TABLE `temp_login` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`token` REAL,
`salt` REAL,
`state` INTEGER,
`login_time` INTEGER,
`login_addr` REAL,
`logout_time` INTEGER,
`expire` INTEGER,
`addtime` INTEGER
);
CREATE TABLE `users` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `username` TEXT,
  `password` TEXT,
  `login_ip` TEXT,
  `login_time` TEXT,
  `phone` TEXT,
  `email` TEXT
, 'salt' TEXT);
INSERT INTO "users" VALUES(1,'7f3miett','BT-0x:Ijq/Rpox++yjNdBQoVpWvI8FpiJC0sLQsXkpAEHBZkf0GHEBiNZFPht3fmko9MJ3','192.168.0.10','2016-12-10 15:12:56','0','BT-0x:eCf9QD23n9cKoRFXz+3all+2jhY0bCWiKAeYjIewSCY=','BT-0x:8Nd3vrea5YGSOgU0tr7DQQ==');
COMMIT;
