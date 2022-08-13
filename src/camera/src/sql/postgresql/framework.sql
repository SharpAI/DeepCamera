-- --------------------------------------------------------
-- Host:                         192.168.88.37
-- Server version:               10.1.25-MariaDB- - Ubuntu 17.04
-- Server OS:                    debian-linux-gnu
-- HeidiSQL Version:             9.4.0.5125
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;


-- Dumping database structure for ccio
CREATE DATABASE `ccio` /*!40100 DEFAULT CHARACTER SET utf8mb4 */;
USE ccio;

-- Dumping structure for table ccio.API
CREATE TABLE IF NOT EXISTS API (
  ke varchar(50) DEFAULT NULL,
  uid varchar(50) DEFAULT NULL,
  ip tinytext,
  code varchar(100) DEFAULT NULL,
  details text,
  time timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP 
) ;

-- Data exporting was unselected.
-- Dumping structure for table ccio.Events
CREATE TABLE IF NOT EXISTS Events (
  ke varchar(50) DEFAULT NULL,
  mid varchar(50) DEFAULT NULL,
  details text,
  time timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP 
)  ;

-- Data exporting was unselected.
-- Dumping structure for table ccio.Logs
CREATE TABLE IF NOT EXISTS Logs (
  ke varchar(50) DEFAULT NULL,
  mid varchar(50) DEFAULT NULL,
  info text,
  time timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP 
) ;

-- Data exporting was unselected.
-- Dumping structure for table ccio.Monitors
CREATE TABLE IF NOT EXISTS Monitors (
  mid varchar(50) DEFAULT NULL,
  ke varchar(50) DEFAULT NULL,
  name varchar(50) DEFAULT NULL,
  shto text,
  shfr text,
  details longtext,
  type varchar(50) DEFAULT 'jpeg',
  ext varchar(50) DEFAULT 'webm',
  protocol varchar(50) DEFAULT 'http',
  host varchar(100) DEFAULT '0.0.0.0',
  path varchar(100) DEFAULT '/',
  port int DEFAULT '80',
  fps int DEFAULT '1',
  mode varchar(15) DEFAULT NULL,
  width int DEFAULT '640',
  height int DEFAULT '360'
) ;

-- Data exporting was unselected.
-- Dumping structure for table ccio.Presets
CREATE TABLE IF NOT EXISTS Presets (
  ke varchar(50) DEFAULT NULL,
  name text,
  details text,
  type enum('monitor','event','user') DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Data exporting was unselected.
-- Dumping structure for table ccio.Users
CREATE TABLE IF NOT EXISTS Users (
  ke varchar(50) DEFAULT NULL,
  uid varchar(50) DEFAULT NULL,
  auth varchar(50) DEFAULT NULL,
  mail varchar(100) DEFAULT NULL,
  pass varchar(100) DEFAULT NULL,
  details longtext,
  CONSTRAINT mail UNIQUE  (mail)
) ;

-- Data exporting was unselected.
-- Dumping structure for table ccio.Videos
CREATE TABLE IF NOT EXISTS Videos (
  mid varchar(50) DEFAULT NULL,
  ke varchar(50) DEFAULT NULL,
  ext enum('webm','mp4') DEFAULT NULL,
  time timestamp(0) NULL DEFAULT NULL,
  duration double precision DEFAULT NULL,
  size double precision DEFAULT NULL,
  frames int DEFAULT NULL,
  end timestamp(0) NULL DEFAULT NULL,
  status int DEFAULT '0' ,
  details text
) ;

-- Data exporting was unselected.
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
