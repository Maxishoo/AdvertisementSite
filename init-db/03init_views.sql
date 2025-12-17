CREATE VIEW ad_full_statistics AS
SELECT
    a.id AS ad_id,
    a.user_id,
    a.category_id,
    a.location_id,
    a.title,
    a.description,
    a.price,
    a.currency,
    a.created_at,
    a.moderation_status,
    a.is_active,
    a.views_count,
    a.image_urls,
    
    -- Статистика по просмотрам
    (SELECT COUNT(*) FROM views v WHERE v.ad_id = a.id) AS total_views,
    (SELECT COUNT(DISTINCT v.user_id) FROM views v WHERE v.ad_id = a.id) AS unique_viewers,
    (SELECT COUNT(*) FROM views v WHERE v.ad_id = a.id AND v.device = 'MOBILE') AS mobile_views,
    (SELECT COUNT(*) FROM views v WHERE v.ad_id = a.id AND v.device = 'PC') AS pc_views,
    
    -- Статистика по сообщениям
    (SELECT COUNT(*) FROM messages m WHERE m.ad_id = a.id) AS total_messages,
    (SELECT COUNT(DISTINCT m.sender_id) FROM messages m WHERE m.ad_id = a.id) AS unique_senders,
    (SELECT COUNT(*) FROM messages m WHERE m.ad_id = a.id AND m.is_read = false) AS unread_messages,
    
    -- Статистика по избранному
    (SELECT COUNT(*) FROM favorites f WHERE f.ad_id = a.id) AS favorites_count,
    
    -- Статистика по жалобам
    (SELECT COUNT(*) FROM reports r WHERE r.ad_id = a.id) AS total_reports,
    (SELECT COUNT(*) FROM reports r WHERE r.ad_id = a.id AND r.status = 'PENDING') AS pending_reports,
    (SELECT COUNT(*) FROM reports r WHERE r.ad_id = a.id AND r.status = 'RESOLVED') AS resolved_reports,
    (SELECT COUNT(*) FROM reports r WHERE r.ad_id = a.id AND r.status = 'REJECTED') AS rejected_reports,
    
    c.name AS category_name,
    c.slug AS category_slug,
    l.city,
    l.district,
    l.street,
    u.username AS owner_username,
    u.is_banned AS owner_is_banned
    
FROM ads a
JOIN categories c ON c.id = a.category_id
JOIN locations l ON l.id = a.location_id
JOIN users u ON u.id = a.user_id;



CREATE VIEW user_performance_dashboard AS
SELECT
    u.id AS user_id,
    u.username,
    u.role,
    u.created_at AS registration_date,
    u.is_banned,
    
    -- Объявления
    COUNT(a.id) AS total_ads,
    COUNT(CASE WHEN a.is_active AND a.moderation_status = 'APPROVED' THEN 1 END) AS active_ads,
    COUNT(CASE WHEN a.moderation_status = 'REJECTED' THEN 1 END) AS rejected_ads,
    
    -- Просмотры
    COALESCE(SUM(a.views_count), 0) AS total_views,
    COALESCE(AVG(a.views_count), 0) AS avg_views_per_ad,
    
    -- Сообщения
    COALESCE(SUM(m.total_messages), 0) AS total_messages_received,
    COALESCE(AVG(m.total_messages), 0) AS avg_messages_per_ad,
    
    -- Избранное
    COALESCE(SUM(f.favorites_count), 0) AS total_favorites,
    
    -- Жалобы
    COALESCE(r.total_reports, 0) AS total_reports_received,
    COALESCE(r.resolved_reports, 0) AS resolved_reports,
    
    -- Активность
    MAX(a.created_at) AS last_ad_created,
    COUNT(CASE WHEN a.created_at >= NOW() - INTERVAL '7 days' THEN 1 END) AS ads_last_7_days

FROM users u
LEFT JOIN ads a ON a.user_id = u.id
LEFT JOIN (
    SELECT ad_id, COUNT(*) AS total_messages
    FROM messages
    GROUP BY ad_id
) m ON m.ad_id = a.id
LEFT JOIN (
    SELECT ad_id, COUNT(*) AS favorites_count
    FROM favorites
    GROUP BY ad_id
) f ON f.ad_id = a.id
LEFT JOIN (
    SELECT 
        reported_user_id,
        COUNT(*) AS total_reports,
        COUNT(CASE WHEN status = 'RESOLVED' THEN 1 END) AS resolved_reports
    FROM reports
    GROUP BY reported_user_id
) r ON r.reported_user_id = u.id
WHERE u.role != 'admin'
GROUP BY u.id, u.username, u.role, u.created_at, u.is_banned, r.total_reports, r.resolved_reports;

-- Статистика по категориям
CREATE OR REPLACE VIEW category_market_insights AS
SELECT
    c.id AS category_id,
    c.name AS category_name,
    c.slug AS category_slug,
    
    -- Счетчики объявлений
    COUNT(a.id) AS total_active_ads,
    COUNT(CASE WHEN a.created_at >= NOW() - INTERVAL '7 days' THEN 1 END) AS new_ads_last_7_days,
    COUNT(CASE WHEN a.created_at >= NOW() - INTERVAL '1 day' THEN 1 END) AS new_ads_last_24h,
    
    -- Статистики по ценам
    COALESCE(AVG(a.price), 0) AS avg_price,
    COALESCE(MIN(a.price), 0) AS min_price,
    COALESCE(MAX(a.price), 0) AS max_price,
    
    -- Счетчики просмотров
    COALESCE(SUM(a.views_count), 0) AS total_views,
    COALESCE(AVG(a.views_count), 0) AS avg_views_per_ad

FROM categories c
LEFT JOIN ads a ON a.category_id = c.id
    AND a.moderation_status = 'APPROVED'
    AND a.is_active = true
    AND a.created_at >= NOW() - INTERVAL '30 days'
GROUP BY c.id, c.name, c.slug
ORDER BY total_active_ads DESC;