-- ============================================================================
-- NATIONAL RETIREMENT CLEARANCE PORTAL FOR NIGERIAN CIVIL SERVANTS
-- Database: retirement_clearance_db
-- Relational Schema DDL (MySQL 8.0+ / MariaDB InnoDB, utf8mb4)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS `retirement_clearance_db` 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

USE `retirement_clearance_db`;

-- 1. Roles Table
CREATE TABLE IF NOT EXISTS `roles` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(50) NOT NULL UNIQUE,
  `display_name` VARCHAR(100) NOT NULL,
  `description` TEXT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_role_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Users Table
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `role_id` INT NOT NULL,
  `username` VARCHAR(80) NOT NULL UNIQUE,
  `email` VARCHAR(120) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `first_name` VARCHAR(80) NOT NULL,
  `last_name` VARCHAR(80) NOT NULL,
  `phone` VARCHAR(25),
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `failed_login_attempts` INT DEFAULT 0,
  `locked_until` DATETIME NULL,
  `must_change_password` BOOLEAN DEFAULT FALSE,
  `last_login_at` DATETIME NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_user_username` (`username`),
  INDEX `idx_user_email` (`email`),
  INDEX `idx_user_role` (`role_id`),
  CONSTRAINT `fk_user_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Employees Table
CREATE TABLE IF NOT EXISTS `employees` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NULL UNIQUE,
  `staff_number` VARCHAR(50) NOT NULL UNIQUE,
  `first_name` VARCHAR(80) NOT NULL,
  `middle_name` VARCHAR(80) NULL,
  `last_name` VARCHAR(80) NOT NULL,
  `gender` VARCHAR(15) NOT NULL,
  `date_of_birth` DATE NOT NULL,
  `state_of_origin` VARCHAR(50) NOT NULL,
  `lga` VARCHAR(80) NULL,
  `residential_address` TEXT NOT NULL,
  `city` VARCHAR(80) NOT NULL,
  `state_of_residence` VARCHAR(50) NOT NULL,
  `phone_number` VARCHAR(25) NOT NULL,
  `email` VARCHAR(120) NOT NULL,
  `nin` VARCHAR(25) NULL,
  `bvn` VARCHAR(25) NULL,
  `ministry_or_agency` VARCHAR(150) NOT NULL,
  `department` VARCHAR(120) NOT NULL,
  `current_cadre` VARCHAR(100) NOT NULL,
  `current_grade_level` VARCHAR(15) NOT NULL,
  `current_step` INT DEFAULT 1,
  `appointment_date` DATE NOT NULL,
  `confirmation_date` DATE NULL,
  `statutory_retirement_date` DATE NOT NULL,
  `passport_photo_path` VARCHAR(255) NULL,
  `biometric_enrolled` BOOLEAN DEFAULT FALSE,
  `biometric_reference_hash` VARCHAR(128) NULL,
  `is_active` BOOLEAN DEFAULT TRUE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_emp_staff_number` (`staff_number`),
  INDEX `idx_emp_ministry` (`ministry_or_agency`),
  INDEX `idx_emp_department` (`department`),
  CONSTRAINT `fk_emp_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Employment Records
CREATE TABLE IF NOT EXISTS `employment_records` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `employee_id` INT NOT NULL,
  `ministry_or_agency` VARCHAR(150) NOT NULL,
  `department` VARCHAR(120) NOT NULL,
  `cadre_and_rank` VARCHAR(100) NOT NULL,
  `grade_level` VARCHAR(15) NOT NULL,
  `start_date` DATE NOT NULL,
  `end_date` DATE NULL,
  `is_current` BOOLEAN DEFAULT TRUE,
  `record_verified` BOOLEAN DEFAULT FALSE,
  `verified_by_user_id` INT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_emprec_employee` (`employee_id`),
  CONSTRAINT `fk_emprec_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_emprec_verifier` FOREIGN KEY (`verified_by_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Promotion Records
CREATE TABLE IF NOT EXISTS `promotion_records` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `employee_id` INT NOT NULL,
  `from_grade_level` VARCHAR(15) NOT NULL,
  `to_grade_level` VARCHAR(15) NOT NULL,
  `effective_date` DATE NOT NULL,
  `gazette_or_ref_number` VARCHAR(120) NULL,
  `is_verified` BOOLEAN DEFAULT FALSE,
  `verified_by_user_id` INT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_prom_employee` (`employee_id`),
  CONSTRAINT `fk_prom_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_prom_verifier` FOREIGN KEY (`verified_by_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Pension Records
CREATE TABLE IF NOT EXISTS `pension_records` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `employee_id` INT NOT NULL,
  `pfa_name` VARCHAR(150) NOT NULL,
  `rsa_pin` VARCHAR(50) NOT NULL UNIQUE,
  `last_contributed_date` DATE NULL,
  `total_contributions_estimate` DECIMAL(14,2) DEFAULT 0.00,
  `status` VARCHAR(30) DEFAULT 'Active',
  `is_verified` BOOLEAN DEFAULT FALSE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_pen_employee` (`employee_id`),
  INDEX `idx_pen_rsa` (`rsa_pin`),
  CONSTRAINT `fk_pen_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Retirement Applications Table
CREATE TABLE IF NOT EXISTS `retirement_applications` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `application_reference` VARCHAR(50) NOT NULL UNIQUE,
  `employee_id` INT NOT NULL,
  `reason_for_retirement` VARCHAR(100) NOT NULL,
  `proposed_retirement_date` DATE NOT NULL,
  `current_status` VARCHAR(60) NOT NULL DEFAULT 'Pending HR Verification',
  `current_stage` VARCHAR(50) NOT NULL DEFAULT 'HR Verification',
  `is_flagged` BOOLEAN DEFAULT FALSE,
  `flag_reason` TEXT NULL,
  `eligibility_summary` VARCHAR(100) NULL,
  `submission_date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `hr_verified_at` DATETIME NULL,
  `hr_officer_id` INT NULL,
  `hr_notes` TEXT NULL,
  `pension_reviewed_at` DATETIME NULL,
  `pension_officer_id` INT NULL,
  `pension_notes` TEXT NULL,
  `rejection_reason` TEXT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_app_ref` (`application_reference`),
  INDEX `idx_app_employee` (`employee_id`),
  INDEX `idx_app_status` (`current_status`),
  INDEX `idx_app_flag` (`is_flagged`),
  CONSTRAINT `fk_app_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_app_hr_officer` FOREIGN KEY (`hr_officer_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_app_pension_officer` FOREIGN KEY (`pension_officer_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Uploaded Documents Table
CREATE TABLE IF NOT EXISTS `uploaded_documents` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `application_id` INT NOT NULL,
  `document_type` VARCHAR(60) NOT NULL,
  `original_filename` VARCHAR(255) NOT NULL,
  `stored_filename` VARCHAR(255) NOT NULL,
  `file_path` VARCHAR(500) NOT NULL,
  `file_size_bytes` INT NOT NULL,
  `mime_type` VARCHAR(100) NOT NULL,
  `sha256_hash` VARCHAR(64) NOT NULL,
  `ocr_status` VARCHAR(30) DEFAULT 'pending',
  `extracted_text` LONGTEXT NULL,
  `extracted_metadata` JSON NULL,
  `is_verified` BOOLEAN DEFAULT FALSE,
  `verified_by_user_id` INT NULL,
  `verification_notes` VARCHAR(255) NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_doc_application` (`application_id`),
  INDEX `idx_doc_type` (`document_type`),
  CONSTRAINT `fk_doc_application` FOREIGN KEY (`application_id`) REFERENCES `retirement_applications` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_doc_verifier` FOREIGN KEY (`verified_by_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. AI Verifications Table
CREATE TABLE IF NOT EXISTS `ai_verifications` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `application_id` INT NOT NULL,
  `verification_timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `calculated_age` INT NOT NULL,
  `calculated_years_of_service` DECIMAL(4,1) NOT NULL,
  `age_eligibility_status` VARCHAR(30) NOT NULL,
  `service_eligibility_status` VARCHAR(30) NOT NULL,
  `overall_eligibility_recommendation` VARCHAR(50) NOT NULL,
  `rule_evaluation_details` JSON NULL,
  `ocr_name_match_status` VARCHAR(50) DEFAULT 'Not Evaluated',
  `ocr_staff_no_match_status` VARCHAR(50) DEFAULT 'Not Evaluated',
  `ocr_date_match_status` VARCHAR(50) DEFAULT 'Not Evaluated',
  `inconsistencies_detected` JSON NULL,
  `missing_documents` JSON NULL,
  `duplicate_records_found` JSON NULL,
  `fraud_risk_level` VARCHAR(30) NOT NULL DEFAULT 'Low',
  `fraud_risk_rationale` TEXT NULL,
  `model_status` VARCHAR(120) NOT NULL DEFAULT 'Rule-based verification & anomaly detection engine',
  `biometric_status` VARCHAR(80) NOT NULL DEFAULT 'Not Configured (Hardware Required)',
  `biometric_details` JSON NULL,
  `requires_manual_review` BOOLEAN DEFAULT FALSE,
  `reviewed_by_officer_id` INT NULL,
  `officer_comments` TEXT NULL,
  `reviewed_at` DATETIME NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_ai_app` (`application_id`),
  CONSTRAINT `fk_ai_application` FOREIGN KEY (`application_id`) REFERENCES `retirement_applications` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ai_officer` FOREIGN KEY (`reviewed_by_officer_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Clearances Table
CREATE TABLE IF NOT EXISTS `clearances` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `application_id` INT NOT NULL UNIQUE,
  `approving_officer_id` INT NOT NULL,
  `decision` VARCHAR(30) NOT NULL,
  `decision_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `remarks` TEXT NULL,
  `pension_entitlement_status` VARCHAR(60) DEFAULT 'Cleared for Statutory Benefits',
  `gratuity_applicable` BOOLEAN DEFAULT TRUE,
  `monthly_pension_applicable` BOOLEAN DEFAULT TRUE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_clr_app` (`application_id`),
  INDEX `idx_clr_officer` (`approving_officer_id`),
  CONSTRAINT `fk_clr_app` FOREIGN KEY (`application_id`) REFERENCES `retirement_applications` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_clr_officer` FOREIGN KEY (`approving_officer_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Retirement Certificates Table
CREATE TABLE IF NOT EXISTS `retirement_certificates` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `certificate_number` VARCHAR(60) NOT NULL UNIQUE,
  `clearance_id` INT NOT NULL UNIQUE,
  `application_id` INT NOT NULL,
  `employee_id` INT NOT NULL,
  `verification_token` VARCHAR(64) NOT NULL UNIQUE,
  `qr_code_path` VARCHAR(255) NULL,
  `pdf_path` VARCHAR(255) NULL,
  `issued_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `is_sample` BOOLEAN DEFAULT TRUE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_cert_num` (`certificate_number`),
  INDEX `idx_cert_token` (`verification_token`),
  CONSTRAINT `fk_cert_clearance` FOREIGN KEY (`clearance_id`) REFERENCES `clearances` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_cert_application` FOREIGN KEY (`application_id`) REFERENCES `retirement_applications` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_cert_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Investigation Records Table
CREATE TABLE IF NOT EXISTS `investigation_records` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `application_id` INT NOT NULL,
  `auditor_id` INT NOT NULL,
  `investigation_type` VARCHAR(60) NOT NULL,
  `findings` TEXT NOT NULL,
  `recommended_action` VARCHAR(80) NOT NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'Open',
  `resolution_date` DATETIME NULL,
  `resolution_notes` TEXT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_inv_app` (`application_id`),
  INDEX `idx_inv_auditor` (`auditor_id`),
  CONSTRAINT `fk_inv_app` FOREIGN KEY (`application_id`) REFERENCES `retirement_applications` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_inv_auditor` FOREIGN KEY (`auditor_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. Application Status History Table
CREATE TABLE IF NOT EXISTS `application_status_history` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `application_id` INT NOT NULL,
  `changed_by_user_id` INT NULL,
  `previous_status` VARCHAR(60) NULL,
  `new_status` VARCHAR(60) NOT NULL,
  `comments` TEXT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_hist_app` (`application_id`),
  CONSTRAINT `fk_hist_app` FOREIGN KEY (`application_id`) REFERENCES `retirement_applications` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_hist_user` FOREIGN KEY (`changed_by_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 14. Audit Logs Table
CREATE TABLE IF NOT EXISTS `audit_logs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NULL,
  `action` VARCHAR(80) NOT NULL,
  `target_model` VARCHAR(60) NULL,
  `target_id` INT NULL,
  `ip_address` VARCHAR(45) NULL,
  `user_agent` VARCHAR(255) NULL,
  `details` JSON NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_audit_user` (`user_id`),
  INDEX `idx_audit_action` (`action`),
  INDEX `idx_audit_time` (`created_at`),
  CONSTRAINT `fk_audit_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 15. Notifications Table
CREATE TABLE IF NOT EXISTS `notifications` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `title` VARCHAR(150) NOT NULL,
  `message` TEXT NOT NULL,
  `link` VARCHAR(255) NULL,
  `category` VARCHAR(30) DEFAULT 'info',
  `is_read` BOOLEAN DEFAULT FALSE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_notif_user` (`user_id`),
  INDEX `idx_notif_read` (`is_read`),
  CONSTRAINT `fk_notif_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 16. System Settings Table
CREATE TABLE IF NOT EXISTS `system_settings` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `setting_key` VARCHAR(80) NOT NULL UNIQUE,
  `setting_value` TEXT NOT NULL,
  `setting_type` VARCHAR(20) DEFAULT 'string',
  `description` TEXT NULL,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_setting_key` (`setting_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
