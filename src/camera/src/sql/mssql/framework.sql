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
CREATE TABLE API (
  ke varchar(50) DEFAULT NULL,
  uid varchar(50) DEFAULT NULL,
  ip varchar(255),
  code varchar(100) DEFAULT NULL,
  details varchar(max),
  time datetime2(0) NULL DEFAULT GETDATE() 
) ;

-- Data exporting was unselected.
-- Dumping structure for table ccio.Events
CREATE TABLE Events (
  ke varchar(50) DEFAULT NULL,
  mid varchar(50) DEFAULT NULL,
  details varchar(max),
  time datetime2(0) NOT NULL DEFAULT GETDATE() 
)  ;

-- Data exporting was unselected.
-- Dumping structure for table ccio.Logs
CREATE TABLE Logs (
  ke varchar(50) DEFAULT NULL,
  mid varchar(50) DEFAULT NULL,
  info varchar(max),
  time datetime2(0) NOT NULL DEFAULT GETDATE() 
) ;

-- Data exporting was unselected.
-- Dumping structure for table ccio.Monitors
CREATE TABLE Monitors (
  mid varchar(50) DEFAULT NULL,
  ke varchar(50) DEFAULT NULL,
  name varchar(50) DEFAULT NULL,
  shto varchar(max),
  shfr varchar(max),
  details varchar(max),
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
CREATE TABLE Presets (
  ke varchar(50) DEFAULT NULL,
  name varchar(max),
  details varchar(max),
  type enum('monitor','event','user') DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Data exporting was unselected.
-- Dumping structure for table ccio.Users
CREATE TABLE Users (
  ke varchar(50) DEFAULT NULL,
  uid varchar(50) DEFAULT NULL,
  auth varchar(50) DEFAULT NULL,
  mail varchar(100) DEFAULT NULL,
  pass varchar(100) DEFAULT NULL,
  details varchar(max),
  CONSTRAINT mail UNIQUE  (mail)
) ;

-- Data exporting was unselected.
-- Dumping structure for table ccio.Videos
CREATE TABLE Videos (
  mid varchar(50) DEFAULT NULL,
  ke varchar(50) DEFAULT NULL,
  ext enum('webm','mp4') DEFAULT NULL,
  time datetime2(0) NULL DEFAULT NULL,
  duration float DEFAULT NULL,
  size float DEFAULT NULL,
  frames int DEFAULT NULL,
  end datetime2(0) NULL DEFAULT NULL,
  status int DEFAULT '0' ,
  details varchar(max)
) ;

-- Data exporting was unselected.
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
