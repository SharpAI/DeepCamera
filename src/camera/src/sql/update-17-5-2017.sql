CREATE DATABASE IF NOT EXISTS `ccio`;
USE `ccio`;

CREATE TABLE IF NOT EXISTS `BackupVideos` (
  `mid` varchar(50) DEFAULT NULL,
  `ke` varchar(50) DEFAULT NULL,
  `ext` varchar(15) DEFAULT NULL,
  `time` timestamp NULL DEFAULT NULL,
  `end` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `size` float DEFAULT NULL,
  `details` longtext
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE Videos MODIFY COLUMN `ext` varchar(15);
ALTER TABLE Videos ADD `details` longtext;
ALTER TABLE Videos DROP COLUMN `frames`;
ALTER TABLE Videos DROP COLUMN `duration`;