CREATE TABLE IF NOT EXISTS `mydealz` (
`id` int(11) NOT NULL AUTO_INCREMENT,
  `titel` varchar(200) NOT NULL,
  `stext` varchar(250) NOT NULL,
  `ltext` longtext,
  `dlink` varchar(250) DEFAULT NULL,
  `hlink` varchar(250) DEFAULT NULL,
  `datum` datetime DEFAULT NULL,
  `dealid` int(11) DEFAULT NULL,
  `price` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;