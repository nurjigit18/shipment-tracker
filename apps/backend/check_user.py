from sqlalchemy import create_engine, text

def main():
    engine = create_engine('postgresql+psycopg://postgres:XBYHOaOSjdGGxSXlhLVirxfHGybVYHwc@mainline.proxy.rlwy.net:47186/railway')

    with engine.connect() as conn:
        # Get user info
        result = conn.execute(text('SELECT id, username, password, password_hash FROM users WHERE username = :username'), {'username': 'test_supplier'})
        user = result.fetchone()

        if user:
            print(f'\n=== USER INFO ===')
            print(f'User ID: {user[0]}')
            print(f'Username: {user[1]}')
            print(f'Password (plaintext): {user[2]}')
            print(f'Password Hash: {user[3][:50]}...' if user[3] else 'None')
        else:
            print('User not found')

    engine.dispose()

if __name__ == '__main__':
    main()
