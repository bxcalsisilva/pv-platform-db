-- MariaDB dump 10.19  Distrib 10.5.12-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: pv_platform
-- ------------------------------------------------------
-- Server version	10.5.12-MariaDB-0ubuntu0.21.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `ambients`
--

DROP TABLE IF EXISTS `ambients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ambients` (
  `ambient_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `observation_id` int(10) unsigned NOT NULL,
  `location_id` tinyint(3) unsigned NOT NULL,
  `t_amb` decimal(10,4) DEFAULT NULL,
  `humidity_relative` decimal(10,4) DEFAULT NULL,
  `humidity_absolute` decimal(10,4) DEFAULT NULL,
  `wind_speed` decimal(10,4) DEFAULT NULL,
  `wind_direction` decimal(10,4) DEFAULT NULL,
  `air_density` decimal(10,4) DEFAULT NULL,
  `pressure_relative` decimal(10,4) DEFAULT NULL,
  `pressure_absolute` decimal(10,4) DEFAULT NULL,
  PRIMARY KEY (`ambient_id`),
  KEY `ambients_FK` (`observation_id`),
  KEY `ambients_FK_1` (`location_id`),
  CONSTRAINT `ambients_FK` FOREIGN KEY (`observation_id`) REFERENCES `observations` (`observation_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `ambients_FK_1` FOREIGN KEY (`location_id`) REFERENCES `locations` (`location_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `errors`
--

DROP TABLE IF EXISTS `errors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `errors` (
  `error_id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `message` varchar(500) NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`error_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `inverters`
--

DROP TABLE IF EXISTS `inverters`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `inverters` (
  `inverter_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `observation_id` int(10) unsigned NOT NULL,
  `system_id` tinyint(3) unsigned NOT NULL,
  `voltage_dc` decimal(10,4) DEFAULT NULL,
  `current_dc` decimal(10,4) DEFAULT NULL,
  `power_apparent` decimal(10,4) DEFAULT NULL,
  `power_dc` decimal(10,4) DEFAULT NULL,
  `power_dc_t25` decimal(10,4) DEFAULT NULL,
  `power_ac` decimal(10,4) DEFAULT NULL,
  `power_ac_t25` decimal(10,4) DEFAULT NULL,
  PRIMARY KEY (`inverter_id`),
  KEY `inverters_FK` (`observation_id`),
  KEY `inverters_FK_1` (`system_id`),
  CONSTRAINT `inverters_FK` FOREIGN KEY (`observation_id`) REFERENCES `observations` (`observation_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `inverters_FK_1` FOREIGN KEY (`system_id`) REFERENCES `systems` (`system_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `irradiances`
--

DROP TABLE IF EXISTS `irradiances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `irradiances` (
  `irradiance_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `observation_id` int(10) unsigned NOT NULL,
  `location_id` tinyint(3) unsigned NOT NULL,
  `irradiance` decimal(10,4) NOT NULL,
  PRIMARY KEY (`irradiance_id`),
  KEY `irradiances_FK` (`observation_id`),
  KEY `irradiances_FK_1` (`location_id`),
  CONSTRAINT `irradiances_FK` FOREIGN KEY (`observation_id`) REFERENCES `observations` (`observation_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `irradiances_FK_1` FOREIGN KEY (`location_id`) REFERENCES `locations` (`location_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `locations`
--

DROP TABLE IF EXISTS `locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `locations` (
  `location_id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `label` varchar(10) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `region` varchar(50) NOT NULL,
  `city` varchar(50) NOT NULL,
  `address` varchar(100) NOT NULL,
  `latitude` decimal(11,6) NOT NULL,
  `longitude` decimal(11,6) NOT NULL,
  `altitude` decimal(11,6) NOT NULL,
  PRIMARY KEY (`location_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logs`
--

DROP TABLE IF EXISTS `logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logs` (
  `log_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `system_id` tinyint(3) unsigned NOT NULL,
  `date` date NOT NULL,
  `type` char(1) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `message` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`log_id`),
  KEY `logs_FK` (`system_id`),
  CONSTRAINT `logs_FK` FOREIGN KEY (`system_id`) REFERENCES `systems` (`system_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `observations`
--

DROP TABLE IF EXISTS `observations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `observations` (
  `observation_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `datetime` datetime NOT NULL,
  PRIMARY KEY (`observation_id`),
  UNIQUE KEY `observations_UN` (`datetime`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `performances`
--

DROP TABLE IF EXISTS `performances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `performances` (
  `performance_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `system_id` tinyint(3) unsigned NOT NULL,
  `date` date NOT NULL,
  `radiation` decimal(10, 4) DEFAULT NULL,
  `yield_reference` decimal(10,4) DEFAULT NULL,
  `yield_absolute` decimal(10,4) DEFAULT NULL,
  `yield_final` decimal(10,4) DEFAULT NULL,
  `yield_absolute_t25` decimal(10,4) DEFAULT NULL,
  `yield_final_t25` decimal(10,4) DEFAULT NULL,
  `performance_ratio` decimal(10,4) DEFAULT NULL,
  `performance_ratio_t25` decimal(10,4) DEFAULT NULL,
  `efficiency_array` decimal(10,4) DEFAULT NULL,
  `efficiency_system` decimal(10,4) DEFAULT NULL,
  `efficiency_inverter` decimal(10,4) DEFAULT NULL,
  `energy_dc` decimal(10,4) DEFAULT NULL,
  `energy_ac` decimal(10,4) DEFAULT NULL,
  `energy_dc_t25` decimal(10,4) DEFAULT NULL,
  `energy_ac_t25` decimal(10,4) DEFAULT NULL,
  PRIMARY KEY (`performance_id`),
  KEY `performances_FK` (`system_id`),
  CONSTRAINT `performances_FK` FOREIGN KEY (`system_id`) REFERENCES `systems` (`system_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `systems`
--

DROP TABLE IF EXISTS `systems`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `systems` (
  `system_id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `location_id` tinyint(3) unsigned NOT NULL,
  `nominal_power` decimal(10,4) NOT NULL,
  `area` decimal(10, 4) NOT NULL,
  `technology` varchar(50) NOT NULL,
  `row` tinyint(3) unsigned NOT NULL,
  `parallel` tinyint(3) unsigned NOT NULL,
  `commisioned` date NOT NULL,
  `inclination` decimal(10,4) NOT NULL,
  `orientation` char(1) NOT NULL,
  `azimuth` decimal(10,4) NOT NULL,
  `gamma` decimal (10, 4) NOT NULL,
  `filename` char(10) NOT NULL,
  PRIMARY KEY (`system_id`),
  KEY `systems_FK` (`location_id`),
  CONSTRAINT `systems_FK` FOREIGN KEY (`location_id`) REFERENCES `locations` (`location_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `t_mods`
--

DROP TABLE IF EXISTS `t_mods`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `t_mods` (
  `t_mod_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `observation_id` int(10) unsigned NOT NULL,
  `system_id` tinyint(3) unsigned NOT NULL,
  `t_mod` decimal(10,4) DEFAULT NULL,
  `t_noct` decimal(10,4) DEFAULT NULL,
  PRIMARY KEY (`t_mod_id`),
  KEY `t_mods_FK` (`observation_id`),
  KEY `t_mods_FK_1` (`system_id`),
  CONSTRAINT `t_mods_FK` FOREIGN KEY (`observation_id`) REFERENCES `observations` (`observation_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `t_mods_FK_1` FOREIGN KEY (`system_id`) REFERENCES `systems` (`system_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-10-12 16:39:55
