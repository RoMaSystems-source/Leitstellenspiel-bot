-- Lizenz-Tabelle für Leitstellenspiel Bot
-- Datenbank: roma_portal

CREATE TABLE IF NOT EXISTS licenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    license_key VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME DEFAULT NULL,
    max_activations INT DEFAULT 1,
    current_activations INT DEFAULT 0,
    hardware_id VARCHAR(255) DEFAULT NULL,
    last_check DATETIME DEFAULT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT DEFAULT NULL,
    INDEX idx_license_key (license_key),
    INDEX idx_email (email),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Beispiel-Lizenz einfügen (für Tests)
-- INSERT INTO licenses (license_key, email, expires_at, is_active) 
-- VALUES ('TEST-1234-5678-9ABC', 'test@example.com', DATE_ADD(NOW(), INTERVAL 1 YEAR), TRUE);

