CREATE TABLE IF NOT EXISTS users (
    id          BIGSERIAL    PRIMARY KEY,
    name        TEXT         NOT NULL,
    email       TEXT         UNIQUE NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id          BIGSERIAL    PRIMARY KEY,
    name        TEXT         NOT NULL,
    description TEXT         NOT NULL DEFAULT '',
    price_cents INTEGER      NOT NULL CHECK (price_cents >= 0),
    image_url   TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    id          BIGSERIAL    PRIMARY KEY,
    user_id     BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    items_json  JSONB        NOT NULL,
    total_cents INTEGER      NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id  TEXT   PRIMARY KEY,
    email       TEXT   NOT NULL,
    expires_at  BIGINT NOT NULL,
    created_at  BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_codes (
    id          BIGSERIAL PRIMARY KEY,
    email       TEXT      NOT NULL,
    code_hash   TEXT      NOT NULL,
    expires_at  BIGINT    NOT NULL,
    created_at  BIGINT    NOT NULL
);
