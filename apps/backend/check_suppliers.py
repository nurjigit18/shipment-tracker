from sqlalchemy import create_engine, text

def main():
    engine = create_engine('postgresql+psycopg://postgres:XBYHOaOSjdGGxSXlhLVirxfHGybVYHwc@mainline.proxy.rlwy.net:47186/railway')

    with engine.connect() as conn:
        # Get suppliers
        result = conn.execute(text('SELECT id, name, organization_id FROM suppliers ORDER BY id'))
        suppliers = result.fetchall()

        print('\n=== SUPPLIERS ===')
        for supplier in suppliers:
            print(f'ID: {supplier[0]}, Name: {supplier[1]}, Org ID: {supplier[2]}')

        # Get user_suppliers
        result = conn.execute(text('SELECT user_id, supplier_id FROM user_suppliers'))
        user_suppliers = result.fetchall()

        print('\n=== USER SUPPLIER ASSIGNMENTS ===')
        if user_suppliers:
            for us in user_suppliers:
                print(f'User ID: {us[0]}, Supplier ID: {us[1]}')
        else:
            print('No assignments found')

    engine.dispose()

if __name__ == '__main__':
    main()
