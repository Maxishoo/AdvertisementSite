-- Тренды по объявлениям
CREATE OR REPLACE FUNCTION get_trending_ads(
    p_days INTEGER DEFAULT 7,
    p_category_id INTEGER DEFAULT NULL,
    p_city VARCHAR(100) DEFAULT NULL,
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    ad_id UUID,
    title TEXT,
    price NUMERIC(12,2),
    currency VARCHAR(10),
    city VARCHAR(100),
    category_name TEXT,
    views_last_period BIGINT,
    messages_last_period BIGINT,
    favorites_last_period BIGINT,
    trending_score NUMERIC,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.id AS ad_id,
        a.title::TEXT AS title,
        a.price,
        a.currency,
        l.city,
        c.name::TEXT AS category_name,
        COALESCE(v.views_count, 0) AS views_last_period,
        COALESCE(m.messages_count, 0) AS messages_last_period,
        COALESCE(f.favorites_count, 0) AS favorites_last_period,
        (
            COALESCE(v.views_count, 0)::NUMERIC * 1.0 +
            COALESCE(m.messages_count, 0)::NUMERIC * 10.0 +
            COALESCE(f.favorites_count, 0)::NUMERIC * 5.0
        ) AS trending_score,
        a.created_at
    FROM ads a
    INNER JOIN categories c ON c.id = a.category_id
    INNER JOIN locations l ON l.id = a.location_id
    -- Просмотры за период
    LEFT JOIN LATERAL (
        SELECT COUNT(*) AS views_count
        FROM views
        WHERE views.ad_id = a.id
          AND views.viewed_at >= NOW() - INTERVAL '1 day' * p_days
    ) v ON true
    -- Сообщения за период
    LEFT JOIN LATERAL (
        SELECT COUNT(*) AS messages_count
        FROM messages
        WHERE messages.ad_id = a.id
          AND messages.sent_at >= NOW() - INTERVAL '1 day' * p_days
    ) m ON true
    -- Избранное за период
    LEFT JOIN LATERAL (
        SELECT COUNT(*) AS favorites_count
        FROM favorites
        WHERE favorites.ad_id = a.id
          AND favorites.added_at >= NOW() - INTERVAL '1 day' * p_days
    ) f ON true
    WHERE 
        a.moderation_status = 'APPROVED'
        AND a.is_active = true
        AND a.created_at >= NOW() - INTERVAL '30 days'
        AND (p_category_id IS NULL OR a.category_id = p_category_id)
        AND (p_city IS NULL OR l.city = p_city)
    ORDER BY trending_score DESC, a.created_at DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql STABLE;


CREATE OR REPLACE FUNCTION get_optimal_price_suggestion(ad_id UUID)
RETURNS NUMERIC(12,2) AS $$
DECLARE
    suggested_price NUMERIC(12,2);
BEGIN
    SELECT COALESCE(AVG(a.price), 0)
    INTO suggested_price
    FROM ads a
    WHERE a.category_id = (
        SELECT category_id FROM ads WHERE id = $1
    )
    AND a.moderation_status = 'APPROVED'
    AND a.is_active = true
    AND a.id != $1;
    
    RETURN suggested_price;
END;
$$ LANGUAGE plpgsql STABLE;