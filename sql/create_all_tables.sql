-- Consolidated SQL Schema for E-commerce Microservices
-- Generated based on Django models

-------------------------------------------------------------------------------
-- AUTH SERVICE
-------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    is_superuser BOOLEAN DEFAULT FALSE,
    email VARCHAR(254) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'customer' NOT NULL,
    address TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_staff BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS users_email_idx ON users (email);

-------------------------------------------------------------------------------
-- PRODUCT SERVICE
-------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(120) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(280) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE PROTECT,
    brand VARCHAR(100),
    price NUMERIC(12, 0) NOT NULL,
    compare_price NUMERIC(12, 0),
    sku VARCHAR(50) UNIQUE NOT NULL,
    stock_quantity INTEGER DEFAULT 0 NOT NULL,
    sold_count INTEGER DEFAULT 0 NOT NULL,
    specifications JSONB DEFAULT '{}'::jsonb NOT NULL,
    image_url VARCHAR(500),
    images JSONB DEFAULT '[]'::jsonb NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    rating_avg NUMERIC(3, 2) DEFAULT 0 NOT NULL,
    rating_count INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Analytics (Product Service)
CREATE TABLE IF NOT EXISTS user_product_views (
    id UUID PRIMARY KEY,
    user_id UUID,
    session_id VARCHAR(100) NOT NULL,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS user_search_logs (
    id UUID PRIMARY KEY,
    user_id UUID,
    session_id VARCHAR(100) NOT NULL,
    query VARCHAR(255) NOT NULL,
    results_count INTEGER DEFAULT 0 NOT NULL,
    filters JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS user_click_events (
    id UUID PRIMARY KEY,
    user_id UUID,
    session_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    product_id UUID,
    metadata JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS product_views_created_at_idx ON user_product_views (created_at);
CREATE INDEX IF NOT EXISTS search_logs_created_at_idx ON user_search_logs (created_at);
CREATE INDEX IF NOT EXISTS click_events_created_at_idx ON user_click_events (created_at);

-------------------------------------------------------------------------------
-- CART SERVICE
-------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS cart_items (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    product_id UUID NOT NULL,
    quantity INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (user_id, product_id)
);

CREATE INDEX IF NOT EXISTS cart_items_user_id_idx ON cart_items (user_id);

-------------------------------------------------------------------------------
-- ORDER SERVICE
-------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY,
    order_number VARCHAR(20) UNIQUE NOT NULL,
    user_id UUID NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    total_amount NUMERIC(12, 0) NOT NULL,
    shipping_fee NUMERIC(10, 0) DEFAULT 0 NOT NULL,
    shipping_address JSONB DEFAULT '{}'::jsonb NOT NULL,
    payment_method VARCHAR(50) DEFAULT 'cod' NOT NULL,
    note TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    product_price NUMERIC(12, 0) NOT NULL,
    product_image VARCHAR(500),
    quantity INTEGER NOT NULL,
    subtotal NUMERIC(12, 0) NOT NULL
);

CREATE TABLE IF NOT EXISTS shipping_tracking (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    location VARCHAR(255),
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS orders_user_id_idx ON orders (user_id);

-------------------------------------------------------------------------------
-- NOTIFICATION SERVICE
-------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-------------------------------------------------------------------------------
-- PAYMENT SERVICE
-------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL,
    user_id UUID NOT NULL,
    amount NUMERIC(12, 0) NOT NULL,
    method VARCHAR(20) DEFAULT 'cod' NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    transaction_id VARCHAR(100),
    metadata JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS payments_order_id_idx ON payments (order_id);
CREATE INDEX IF NOT EXISTS payments_user_id_idx ON payments (user_id);

-------------------------------------------------------------------------------
-- REVIEW SERVICE
-------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL,
    user_id UUID NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT NOT NULL,
    is_approved BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS reviews_product_id_idx ON reviews (product_id);
