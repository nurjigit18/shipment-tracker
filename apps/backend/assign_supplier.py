from sqlalchemy import create_engine, text

def main():
    engine = create_engine('postgresql+psycopg://postgres:XBYHOaOSjdGGxSXlhLVirxfHGybVYHwc@mainline.proxy.rlwy.net:47186/railway')

    with engine.connect() as conn:
        # Get user info
        result = conn.execute(text('SELECT id, username, organization_id FROM users WHERE id = 7'))
        user = result.fetchone()
        if user:
            print(f'\n=== USER INFO ===')
            print(f'User ID: {user[0]}, Username: {user[1]}, Organization: {user[2]}')

            user_org_id = user[2]

            # Update supplier to match user's organization
            result = conn.execute(
                text('UPDATE suppliers SET organization_id = :org_id WHERE id = 1 RETURNING id, name, organization_id'),
                {'org_id': user_org_id}
            )
            supplier = result.fetchone()
            conn.commit()

            print(f'\n=== UPDATED SUPPLIER ===')
            print(f'Supplier ID: {supplier[0]}, Organization: {supplier[2]}')

            # Create user-supplier assignment
            result = conn.execute(
                text('INSERT INTO user_suppliers (user_id, supplier_id) VALUES (:user_id, :supplier_id) RETURNING id'),
                {'user_id': user[0], 'supplier_id': 1}
            )
            assignment = result.fetchone()
            conn.commit()

            print(f'\n=== CREATED ASSIGNMENT ===')
            print(f'Assignment ID: {assignment[0]}, User ID: {user[0]}, Supplier ID: 1')
            print('\nSuccess! Supplier is now assigned to your user account.')
        else:
            print('User ID 7 not found!')

    engine.dispose()

if __name__ == '__main__':
    main()
