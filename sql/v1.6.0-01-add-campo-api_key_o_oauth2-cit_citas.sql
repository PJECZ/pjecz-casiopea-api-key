-- 2026-11-23 - Añadir campo api_key_o_oauth2
ALTER TABLE cit_citas
    ADD COLUMN api_key_o_oauth2 BOOLEAN DEFAULT NULL;
