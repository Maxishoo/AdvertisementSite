CREATE OR REPLACE FUNCTION log_user_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO user_audit_log (target_user_id, action)
        VALUES (NEW.id, 'REGISTERED');
        RETURN NEW;
        
    ELSIF (TG_OP = 'UPDATE') THEN
        IF OLD.is_banned <> NEW.is_banned THEN
            IF NEW.is_banned = true THEN
                INSERT INTO user_audit_log (target_user_id, action)
                VALUES (NEW.id, 'BANNED');
            ELSE
                INSERT INTO user_audit_log (target_user_id, action)
                VALUES (NEW.id, 'UNBANNED');
            END IF;
        END IF;
        
        IF OLD.role <> NEW.role THEN
            INSERT INTO user_audit_log (target_user_id, action)
            VALUES (NEW.id, 'ROLE_CHANGED');
        END IF;
        
        IF OLD.is_banned IS DISTINCT FROM NEW.is_banned OR 
           OLD.role IS DISTINCT FROM NEW.role THEN
        ELSE
            INSERT INTO user_audit_log (target_user_id, action)
            VALUES (NEW.id, 'UPDATED');
        END IF;
        
        RETURN NEW;
        
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO user_audit_log (target_user_id, action)
        VALUES (OLD.id, 'DELETED');
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION log_user_changes();


CREATE OR REPLACE FUNCTION log_ad_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO ad_audit_log (ad_id, user_id, action)
        VALUES (NEW.id, NEW.user_id, 'CREATED');
        RETURN NEW;
        
    ELSIF (TG_OP = 'UPDATE') THEN
        IF OLD.moderation_status <> NEW.moderation_status THEN
            IF NEW.moderation_status = 'APPROVED' THEN
                INSERT INTO ad_audit_log (ad_id, user_id, action)
                VALUES (NEW.id, NEW.user_id, 'MODERATION_APPROVED');
            ELSIF NEW.moderation_status = 'REJECTED' THEN
                INSERT INTO ad_audit_log (ad_id, user_id, action)
                VALUES (NEW.id, NEW.user_id, 'MODERATION_REJECTED');
            END IF;
        END IF;
        
        IF OLD.is_active <> NEW.is_active THEN
            IF NEW.is_active = false THEN
                INSERT INTO ad_audit_log (ad_id, user_id, action)
                VALUES (NEW.id, NEW.user_id, 'DEACTIVATED');
            ELSE
                INSERT INTO ad_audit_log (ad_id, user_id, action)
                VALUES (NEW.id, NEW.user_id, 'ACTIVATED');
            END IF;
        END IF;
        
        IF OLD.moderation_status = NEW.moderation_status AND 
           OLD.is_active = NEW.is_active AND
           (OLD.title <> NEW.title OR OLD.description <> NEW.description OR 
            OLD.price <> NEW.price OR OLD.category_id <> NEW.category_id) THEN
            
            INSERT INTO ad_audit_log (ad_id, user_id, action)
            VALUES (NEW.id, NEW.user_id, 'UPDATED');
        END IF;
        
        RETURN NEW;
        
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO ad_audit_log (ad_id, user_id, action)
        VALUES (OLD.id, OLD.user_id, 'DELETED');
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ad_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON ads
FOR EACH ROW EXECUTE FUNCTION log_ad_changes();


-- Автоматическое обновление счетчика просмотров
CREATE OR REPLACE FUNCTION increment_ad_views()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE ads
    SET views_count = views_count + 1
    WHERE id = NEW.ad_id;

    INSERT INTO ad_audit_log (ad_id, user_id, action)
    VALUES (NEW.ad_id, NEW.user_id, 'VIEWS_INCREMENTED');
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER view_count_increment_trigger
AFTER INSERT ON views
FOR EACH ROW EXECUTE FUNCTION increment_ad_views();


-- Предотвращения дублирования жалоб от одного пользователя на одно объявление
CREATE OR REPLACE FUNCTION check_duplicate_report()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM reports 
        WHERE complainant_id = NEW.complainant_id 
          AND ad_id = NEW.ad_id
          AND status IN ('PENDING', 'IN_PROGRESS')
    ) THEN
        RAISE EXCEPTION 'User already has an active report for this ad';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_duplicate_reports
BEFORE INSERT ON reports
FOR EACH ROW EXECUTE FUNCTION check_duplicate_report();

-- Запрет создания сообщения к неактивному объявлению
CREATE OR REPLACE FUNCTION prevent_message_to_inactive_ad()
RETURNS TRIGGER AS $$
DECLARE
    ad_active BOOLEAN;
BEGIN
    SELECT is_active INTO ad_active FROM ads WHERE id = NEW.ad_id;
    
    IF NOT ad_active THEN
        RAISE EXCEPTION 'Cannot send message to inactive ad';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_ad_active_before_message
BEFORE INSERT ON messages
FOR EACH ROW EXECUTE FUNCTION prevent_message_to_inactive_ad();


-- Автоматическое установления reported_user_id в жалобах
CREATE OR REPLACE FUNCTION set_reported_user_from_ad()
RETURNS TRIGGER AS $$
BEGIN
    SELECT user_id INTO NEW.reported_user_id FROM ads WHERE id = NEW.ad_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_reported_user_from_ad_trigger
BEFORE INSERT ON reports
FOR EACH ROW EXECUTE FUNCTION set_reported_user_from_ad();