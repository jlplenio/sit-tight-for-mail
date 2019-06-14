CREATE TABLE IF NOT EXISTS `immoscout` (
`id` int(11) NOT NULL AUTO_INCREMENT,
  `searchid` varchar(10) NOT NULL,
  `immoid` int(11) NOT NULL,
  `titel` varchar(200) DEFAULT NULL,
  `miete` float DEFAULT NULL,
  `qm` float DEFAULT NULL,
  `zimmer` float DEFAULT NULL,
  `adresse` varchar(200) DEFAULT NULL,
  `date` datetime NOT NULL,
  `link` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;
