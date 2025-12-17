CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE CHECK (email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$'),
    phone VARCHAR(20) NOT NULL UNIQUE CHECK (phone ~ '^\+7\d{10}$'),
    password_hash VARCHAR(128) NOT NULL,
    username VARCHAR(128) NOT NULL UNIQUE CHECK (LENGTH(username) >= 3),
    first_name VARCHAR(64) DEFAULT 'not filled in',
    last_name VARCHAR(64) DEFAULT 'not filled in',
    role VARCHAR(20) DEFAULT 'user' NOT NULL CHECK (role IN ('user', 'moderator', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    is_verified BOOLEAN DEFAULT false NOT NULL,
    is_banned BOOLEAN DEFAULT false NOT NULL,
    avatar_url VARCHAR(512)
);

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL UNIQUE,
    slug VARCHAR(150) NOT NULL UNIQUE,
    icon_url VARCHAR(512),
    description VARCHAR(512)
);

CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    district VARCHAR(100),
    street VARCHAR(200),
    building VARCHAR(20),
    latitude NUMERIC(9,6) CHECK (latitude BETWEEN -90 AND 90),
    longitude NUMERIC(9,6) CHECK (longitude BETWEEN -180 AND 180),
    postal_code VARCHAR(20),
    UNIQUE (city, district, street, building)
);

CREATE TABLE ads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL CHECK (LENGTH(title) >= 10),
    description TEXT NOT NULL CHECK (LENGTH(description) >= 50),
    price NUMERIC(12,2) NOT NULL CHECK (price > 0),
    currency VARCHAR(3) DEFAULT 'RUB' NOT NULL CHECK (currency IN ('RUB', 'USD', 'EUR')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    moderation_status VARCHAR(20) DEFAULT 'PENDING' NOT NULL CHECK (moderation_status IN ('PENDING', 'APPROVED', 'REJECTED')),
    is_active BOOLEAN DEFAULT true NOT NULL,
    views_count INTEGER DEFAULT 0 NOT NULL CHECK (views_count >= 0),
    image_urls VARCHAR(512)
);

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE CHECK (LENGTH(name) >= 2),
    slug VARCHAR(60) NOT NULL UNIQUE
);


CREATE TABLE ad_tags (
    ad_id UUID NOT NULL REFERENCES ads(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (ad_id, tag_id)
);

CREATE TABLE favorites (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ad_id UUID NOT NULL REFERENCES ads(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    PRIMARY KEY (user_id, ad_id)
);

CREATE TABLE views (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ad_id UUID NOT NULL REFERENCES ads(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    viewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    device VARCHAR(20) DEFAULT 'MOBILE' NOT NULL CHECK (device IN ('MOBILE', 'PC'))
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ad_id UUID NOT NULL REFERENCES ads(id) ON DELETE CASCADE,
    text TEXT NOT NULL CHECK (LENGTH(text) BETWEEN 1 AND 2000),
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    is_read BOOLEAN DEFAULT false NOT NULL,
    CHECK (sender_id <> recipient_id)
);

CREATE TABLE ad_audit_log (
    id SERIAL PRIMARY KEY,
    ad_id UUID NOT NULL,
    user_id UUID,
    action VARCHAR(30) NOT NULL CHECK (action IN ('CREATED', 'UPDATED', 'DEACTIVATED', 'DELETED', 'MODERATION_APPROVED', 'MODERATION_REJECTED', 'VIEWS_INCREMENTED')),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE TABLE user_audit_log (
    id SERIAL PRIMARY KEY,
    target_user_id UUID NOT NULL,
    action VARCHAR(30) NOT NULL CHECK (action IN ('REGISTERED', 'UPDATED', 'DEACTIVATED', 'ACTIVATED', 'BANNED', 'UNBANNED', 'ROLE_CHANGED', 'DELETED')),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ad_id UUID NOT NULL REFERENCES ads(id) ON DELETE CASCADE,
    complainant_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reported_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason VARCHAR(50) NOT NULL CHECK (reason IN ('FRAUD', 'INAPPROPRIATE_CONTENT', 'SPAM', 'COPYRIGHT', 'FAKE_PROFILE', 'OTHER')),
    description TEXT NOT NULL CHECK (LENGTH(description) >= 10),
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL CHECK (status IN ('PENDING', 'RESOLVED', 'REJECTED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);