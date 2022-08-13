USE ccio;
ALTER TABLE Monitors MODIFY ext VARCHAR(50);

CREATE TABLE IF NOT EXISTS `API` (
  `ke` varchar(50) DEFAULT NULL,
  `uid` varchar(50) DEFAULT NULL,
  `ip` tinytext,
  `code` varchar(100) DEFAULT NULL,
  `details` text,
  `time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8;