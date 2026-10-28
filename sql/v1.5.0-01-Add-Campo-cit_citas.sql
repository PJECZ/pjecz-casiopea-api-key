-- 2026-06-25 - Añadir campo codigo_acceso_url_whatsapp
ALTER TABLE cit_citas
    ADD COLUMN codigo_acceso_url_whatsapp VARCHAR(512) DEFAULT NULL;