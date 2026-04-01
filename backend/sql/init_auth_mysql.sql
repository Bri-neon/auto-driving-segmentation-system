-- Auto Driving Segmentation System
-- MySQL init script for auth + history
-- Default admin account:
--   username: admin
--   password: Admin@123456

CREATE DATABASE IF NOT EXISTS `segmentation_system`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE `segmentation_system`;

CREATE TABLE IF NOT EXISTS `users` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(64) NOT NULL,
  `email` VARCHAR(255) DEFAULT NULL,
  `password_hash` VARCHAR(255) NOT NULL COMMENT 'Format: pbkdf2_sha256$iterations$salt_b64$hash_b64',
  `nickname` VARCHAR(64) DEFAULT NULL,
  `avatar_url` VARCHAR(255) DEFAULT NULL,
  `role` ENUM('admin', 'user') NOT NULL DEFAULT 'user',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_login_at` TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_users_username` (`username`),
  UNIQUE KEY `uk_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE `users`
  ADD COLUMN `avatar_url` VARCHAR(255) DEFAULT NULL AFTER `nickname`;

CREATE TABLE IF NOT EXISTS `user_login_logs` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NULL,
  `login_ip` VARCHAR(45) DEFAULT NULL,
  `user_agent` VARCHAR(255) DEFAULT NULL,
  `is_success` TINYINT(1) NOT NULL DEFAULT 1,
  `reason` VARCHAR(255) DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_login_logs_user_id` (`user_id`),
  KEY `idx_login_logs_created_at` (`created_at`),
  CONSTRAINT `fk_login_logs_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE `user_login_logs`
  MODIFY COLUMN `user_id` BIGINT UNSIGNED NULL;

CREATE TABLE IF NOT EXISTS `inference_histories` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `task_id` VARCHAR(64) DEFAULT NULL,
  `request_type` ENUM('image', 'video') NOT NULL,
  `process_mode` ENUM('sync', 'realtime') NOT NULL,
  `model_key` VARCHAR(64) NOT NULL,
  `model_name` VARCHAR(128) NOT NULL,
  `resolution` VARCHAR(32) DEFAULT NULL,
  `original_url` VARCHAR(255) NOT NULL,
  `segmented_url` VARCHAR(255) DEFAULT NULL,
  `overlay_url` VARCHAR(255) DEFAULT NULL,
  `realtime_status` VARCHAR(32) NOT NULL DEFAULT 'completed',
  `finalize_status` VARCHAR(32) NOT NULL DEFAULT 'completed',
  `status_message` VARCHAR(255) DEFAULT NULL,
  `avg_fps` DECIMAL(10, 3) DEFAULT NULL,
  `realtime_fps` DECIMAL(10, 3) DEFAULT NULL,
  `inference_time` DECIMAL(10, 4) DEFAULT NULL,
  `classes_json` JSON DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_histories_task_id` (`task_id`),
  KEY `idx_histories_user_created` (`user_id`, `created_at`),
  KEY `idx_histories_type_mode` (`request_type`, `process_mode`),
  CONSTRAINT `fk_histories_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `users` (`username`, `email`, `password_hash`, `nickname`, `role`, `is_active`)
VALUES (
  'admin',
  'admin@local.dev',
  'pbkdf2_sha256$120000$ubq4ug/SfSJzrTOQssghVw==$SUf+HiiaxAA/b2dLGmFOCkP5oTyHw4xZgHn8O2reZ80=',
  'System Admin',
  'admin',
  1
)
ON DUPLICATE KEY UPDATE
  `nickname` = VALUES(`nickname`),
  `role` = VALUES(`role`),
  `is_active` = VALUES(`is_active`);

SELECT
  DATABASE() AS current_db,
  COUNT(*) AS user_count
FROM `users`;
