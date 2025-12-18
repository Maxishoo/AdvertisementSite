CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- users
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_banned ON users(is_banned);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_search_trgm ON users USING GIN ((username || ' ' || COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')) gin_trgm_ops);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- categories
CREATE INDEX idx_categories_name_gin ON categories USING GIN (name gin_trgm_ops);
CREATE INDEX idx_categories_slug_gin ON categories USING GIN (slug gin_trgm_ops);

-- locations
CREATE INDEX idx_locations_city_gin ON locations USING GIN (city gin_trgm_ops);
CREATE INDEX idx_locations_district_gin ON locations USING GIN (district gin_trgm_ops);
CREATE INDEX idx_locations_postal_code ON locations(postal_code);

-- ads
CREATE INDEX idx_ads_category_id ON ads(category_id);
CREATE INDEX idx_ads_location_id ON ads(location_id);
CREATE INDEX idx_ads_user_id ON ads(user_id);
CREATE INDEX idx_ads_price ON ads(price);
CREATE INDEX idx_ads_views_count ON ads(views_count DESC);
CREATE INDEX idx_ads_description_trgm ON ads USING GIN (description gin_trgm_ops);
CREATE INDEX idx_ads_title_trgm ON ads USING GIN (title gin_trgm_ops);

-- tags
CREATE INDEX idx_tags_name_trgm ON tags USING GIN (name gin_trgm_ops);
CREATE INDEX idx_tags_slug_trgm ON tags USING GIN (slug gin_trgm_ops);

-- связи объявлений и тегов
CREATE INDEX idx_ad_tags_ad_id ON ad_tags(ad_id);
CREATE INDEX idx_ad_tags_tag_id ON ad_tags(tag_id);
CREATE INDEX idx_ad_tags_composite ON ad_tags(ad_id, tag_id);

-- избранное
CREATE INDEX idx_favorites_user_id ON favorites(user_id);
CREATE INDEX idx_favorites_ad_id ON favorites(ad_id);
CREATE INDEX idx_favorites_added_at ON favorites(added_at DESC);

-- просмотры
CREATE INDEX idx_views_ad_id ON views(ad_id);
CREATE INDEX idx_views_user_id ON views(user_id);
CREATE INDEX idx_views_device ON views(device);
CREATE INDEX idx_views_viewed_at_brin ON views USING BRIN (viewed_at);
CREATE INDEX idx_views_user_ad ON views(user_id, ad_id);

-- сообщения
CREATE INDEX idx_messages_sender_id ON messages(sender_id);
CREATE INDEX idx_messages_recipient_id ON messages(recipient_id);
CREATE INDEX idx_messages_ad_id ON messages(ad_id);
CREATE INDEX idx_messages_is_read ON messages(is_read);
CREATE INDEX idx_messages_text_trgm ON messages USING GIN (text gin_trgm_ops);
CREATE INDEX idx_messages_sent_at_brin ON messages USING BRIN (sent_at);

-- жалобы
CREATE INDEX idx_reports_ad_id ON reports(ad_id);
CREATE INDEX idx_reports_complainant_id ON reports(complainant_id);
CREATE INDEX idx_reports_reported_user_id ON reports(reported_user_id);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_created_at ON reports USING BRIN(created_at);

-- аудит-логи
CREATE INDEX idx_ad_audit_log_ad_id ON ad_audit_log(ad_id);
CREATE INDEX idx_ad_audit_log_action ON ad_audit_log(action);
CREATE INDEX idx_ad_audit_log_changed_at_brin ON ad_audit_log USING BRIN (changed_at);

CREATE INDEX idx_user_audit_log_target_user_id ON user_audit_log(target_user_id);
CREATE INDEX idx_user_audit_log_action ON user_audit_log(action);
CREATE INDEX idx_user_audit_log_changed_at_brin ON user_audit_log USING BRIN (changed_at);