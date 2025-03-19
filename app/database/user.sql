-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- 主机： localhost
-- 生成日期： 2025-03-19 21:35:27
-- 服务器版本： 5.7.44-log
-- PHP 版本： 8.0.26

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- 数据库： `text`
--

-- --------------------------------------------------------

--
-- 表的结构 `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `role` varchar(25) NOT NULL,
  `nickname` varchar(255) NOT NULL,
  `avatar` varchar(255) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `vip_end` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `login_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `token` text,
  `auth_num` int(11) DEFAULT '0',
  `use_num` int(11) DEFAULT '0',
  `login_ip` varchar(50) DEFAULT '127.0.0.1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- 转存表中的数据 `users`
--

INSERT INTO `users` (`id`, `role`, `nickname`, `avatar`, `username`, `password`, `vip_end`, `login_time`, `token`, `auth_num`, `use_num`, `login_ip`) VALUES
(1, 'R_ADMIN', '管理员', 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fm.duitang.com%2Fcategory%2F%3Fcat%3Davatar&psig=AOvVaw2aiVOzKRr8NyKYy6XmSLYu&ust=1742472744217000&source=images&cd=vfe&opi=89978449&ved=0CBEQjRxqFwoTCKiaqIGPlowDFQAAAAAdAAAAABAE', 'admin', 'c2d6c5e937899f7aef4428a2b065eedc1a0bed36b9c838c5e7c52937d2c63a9b', '2025-03-19 12:09:56', '2025-03-19 12:31:10', '09097230-04be-11f0-b392-acde48001122', 0, 0, '157.254.22.27');

--
-- 转储表的索引
--

--
-- 表的索引 `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`);

--
-- 在导出的表使用AUTO_INCREMENT
--

--
-- 使用表AUTO_INCREMENT `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
