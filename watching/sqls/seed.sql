CREATE DATABASE IF NOT EXISTS mediatools_watching CHARACTER
SET
    utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE
    IF NOT EXISTS `platforms` (
        `platform_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '平台唯一标识符，主键',
        `name` VARCHAR(255) NOT NULL COMMENT '平台名称，如B站、微博等',
        `base_url` VARCHAR(255) COMMENT '平台的基础URL，用于构建特定页面的链接'
    ) COMMENT = '存储不同社交媒体平台的信息';

CREATE TABLE
    IF NOT EXISTS `users` (
        `user_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户唯一标识符，主键',
        `name` VARCHAR(255) NOT NULL COMMENT '用户的通用名称或昵称，跨平台使用'
    ) COMMENT = '存储用户的基本信息，包括在多个平台上可能使用的不同用户名';

CREATE TABLE
    IF NOT EXISTS `user_platforms` (
        `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录唯一标识符，主键',
        `user_id` INT COMMENT '关联users表的用户ID，表示特定用户',
        `platform_id` INT COMMENT '关联platforms表的平台ID，表示用户所在的平台',
        `account_id` VARCHAR(255) NOT NULL COMMENT '在该平台上的用户账号ID或用户名',
        `extra_info` TEXT COMMENT '存储关于用户账号的额外信息，如JSON格式的扩展属性',
        FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) COMMENT '外键约束，引用users表',
        FOREIGN KEY (`platform_id`) REFERENCES `platforms` (`platform_id`) COMMENT '外键约束，引用platforms表'
    ) COMMENT = '关联用户和平台，存储用户在各个平台上的账号信息';

-- BV14Z421m7Ks