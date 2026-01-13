"""Google Sheets integration service for reading/writing shipment data."""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Any, Optional
import os

from ..core.config import settings


class GoogleSheetsService:
    """Service for interacting with Google Sheets API."""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self):
        """Initialize Google Sheets service with credentials."""
        self.credentials = None
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Load credentials and build Google Sheets service."""
        if not settings.GOOGLE_SHEETS_CREDENTIALS_PATH:
            print("⚠️  Warning: GOOGLE_SHEETS_CREDENTIALS_PATH not set")
            return

        credentials_path = settings.GOOGLE_SHEETS_CREDENTIALS_PATH

        # Handle both absolute and relative paths
        if not os.path.isabs(credentials_path):
            # Relative to backend app directory
            credentials_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                credentials_path
            )

        if not os.path.exists(credentials_path):
            print(f"❌ Error: Credentials file not found at: {credentials_path}")
            return

        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=self.SCOPES
            )
            self.service = build('sheets', 'v4', credentials=self.credentials)
            print(f"✅ Google Sheets service initialized successfully")
            print(f"   Credentials: {credentials_path}")
        except Exception as e:
            print(f"❌ Error initializing Google Sheets service: {e}")
            self.service = None

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the Google Sheets connection.

        Returns:
            Dictionary with connection status and details
        """
        if not self.service:
            return {
                "status": "error",
                "message": "Google Sheets service not initialized",
                "credentials_path": settings.GOOGLE_SHEETS_CREDENTIALS_PATH,
            }

        if not settings.GOOGLE_SHEETS_SPREADSHEET_ID:
            return {
                "status": "warning",
                "message": "GOOGLE_SHEETS_SPREADSHEET_ID not set in environment",
                "service_initialized": True,
            }

        try:
            # Try to get spreadsheet metadata
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=settings.GOOGLE_SHEETS_SPREADSHEET_ID
            ).execute()

            return {
                "status": "success",
                "message": "Connected to Google Sheets successfully",
                "spreadsheet_title": spreadsheet.get('properties', {}).get('title'),
                "spreadsheet_id": settings.GOOGLE_SHEETS_SPREADSHEET_ID,
                "sheet_count": len(spreadsheet.get('sheets', [])),
                "sheets": [
                    sheet.get('properties', {}).get('title')
                    for sheet in spreadsheet.get('sheets', [])
                ],
            }
        except HttpError as e:
            return {
                "status": "error",
                "message": f"HTTP Error: {e.reason}",
                "error_code": e.resp.status,
                "spreadsheet_id": settings.GOOGLE_SHEETS_SPREADSHEET_ID,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error connecting to Google Sheets: {str(e)}",
                "spreadsheet_id": settings.GOOGLE_SHEETS_SPREADSHEET_ID,
            }

    def read_range(self, range_name: str) -> Optional[List[List[Any]]]:
        """
        Read data from a specific range in the spreadsheet.

        Args:
            range_name: A1 notation range (e.g., 'Sheet1!A1:D10')

        Returns:
            List of rows, where each row is a list of cell values
        """
        if not self.service or not settings.GOOGLE_SHEETS_SPREADSHEET_ID:
            return None

        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=settings.GOOGLE_SHEETS_SPREADSHEET_ID,
                range=range_name
            ).execute()

            values = result.get('values', [])
            return values
        except HttpError as e:
            print(f"Error reading range {range_name}: {e}")
            return None

    def write_range(self, range_name: str, values: List[List[Any]]) -> bool:
        """
        Write data to a specific range in the spreadsheet.

        Args:
            range_name: A1 notation range (e.g., 'Sheet1!A1:D10')
            values: 2D list of values to write

        Returns:
            True if successful, False otherwise
        """
        if not self.service or not settings.GOOGLE_SHEETS_SPREADSHEET_ID:
            return False

        try:
            body = {
                'values': values
            }

            self.service.spreadsheets().values().update(
                spreadsheetId=settings.GOOGLE_SHEETS_SPREADSHEET_ID,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()

            return True
        except HttpError as e:
            print(f"Error writing to range {range_name}: {e}")
            return False

    def ensure_sheet_exists(self, sheet_name: str) -> bool:
        """
        Ensure a sheet with the given name exists. Creates it if it doesn't exist.

        Args:
            sheet_name: Name of the sheet to check/create

        Returns:
            True if sheet exists or was created successfully, False otherwise
        """
        if not self.service or not settings.GOOGLE_SHEETS_SPREADSHEET_ID:
            return False

        try:
            # Get spreadsheet metadata to check existing sheets
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=settings.GOOGLE_SHEETS_SPREADSHEET_ID
            ).execute()

            # Check if sheet already exists
            existing_sheets = [
                sheet.get('properties', {}).get('title')
                for sheet in spreadsheet.get('sheets', [])
            ]

            if sheet_name in existing_sheets:
                return True  # Sheet already exists

            # Create new sheet
            requests = [{
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }]

            body = {'requests': requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=settings.GOOGLE_SHEETS_SPREADSHEET_ID,
                body=body
            ).execute()

            print(f"✅ Created new sheet: {sheet_name}")

            # Add header row to new sheet
            header = [
                "время", "username", "номер отправки", "номер пакета", "тип упаковки",
                "склад", "фулфилмент", "модель", "цвет", "дата отправки", "Общее количество",
                "XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL", "6XL", "7XL", "8XL",
                "Статус"
            ]
            self.write_range(f"{sheet_name}!A1:W1", [header])

            return True

        except HttpError as e:
            print(f"Error ensuring sheet exists: {e}")
            return False
        except Exception as e:
            print(f"Error ensuring sheet exists: {e}")
            return False

    def append_rows(self, range_name: str, values: List[List[Any]]) -> bool:
        """
        Append rows to the end of a sheet.

        Args:
            range_name: Sheet name or range (e.g., 'Sheet1' or 'Sheet1!A:D')
            values: 2D list of values to append

        Returns:
            True if successful, False otherwise
        """
        if not self.service or not settings.GOOGLE_SHEETS_SPREADSHEET_ID:
            return False

        try:
            body = {
                'values': values
            }

            self.service.spreadsheets().values().append(
                spreadsheetId=settings.GOOGLE_SHEETS_SPREADSHEET_ID,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()

            return True
        except HttpError as e:
            print(f"Error appending to {range_name}: {e}")
            return False

    def sync_shipment_to_sheets(
        self,
        shipment_data: Dict[str, Any],
        username: str,
        sheet_name: str = None
    ) -> bool:
        """
        Sync shipment data to Google Sheets.
        Creates one row per bag item combination.
        Each supplier gets their own tab (sheet).

        Args:
            shipment_data: Shipment dictionary with bags data
            username: Username who created the shipment
            sheet_name: Optional sheet name override. If None, uses supplier name

        Returns:
            True if successful, False otherwise
        """
        if not self.service or not settings.GOOGLE_SHEETS_SPREADSHEET_ID:
            print("⚠️  Google Sheets not configured")
            return False

        try:
            from datetime import datetime

            shipment = shipment_data.get("shipment", {})
            shipment_id = shipment.get("id")
            supplier = shipment.get("supplier", "")
            warehouse = shipment.get("warehouse", "")
            fulfillment = shipment.get("fulfillment", "") or ""
            shipment_date = shipment.get("shipment_date", "")
            shipment_type = shipment.get("shipment_type", "BAGS")
            status = shipment.get("current_status", "") or ""
            bags = shipment.get("bags", [])

            # Translate shipment type to Russian
            shipment_type_ru = {
                "BAGS": "мешки",
                "BOXES": "коробки"
            }.get(shipment_type, shipment_type)

            # Translate status to Russian
            status_ru = {
                "новая отправка": "новая отправка",
                "SENT_FROM_FACTORY": "отправлено из цеха",
                "SHIPPED_FROM_FF": "Отправлено от фулфилмента",
                "DELIVERED": "доставлено"
            }.get(status, status)

            # Use supplier name as sheet name if not provided
            if not sheet_name:
                sheet_name = supplier if supplier else "Shipments"

            # Ensure the supplier's sheet exists
            if not self.ensure_sheet_exists(sheet_name):
                print(f"❌ Failed to create/access sheet: {sheet_name}")
                return False

            # Current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Size columns in order
            size_columns = ["XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL", "6XL", "7XL", "8XL"]

            rows = []

            # Create one row per bag item
            for bag in bags:
                bag_id = bag.get("bag_id", "")
                items = bag.get("items", [])

                for item in items:
                    model = item.get("model", "")
                    color = item.get("color", "")
                    sizes = item.get("sizes", {})

                    # Calculate total quantity for this item
                    total_quantity = sum(sizes.values())

                    # Build row: время, username, номер отправки, номер пакета, тип упаковки,
                    # склад, фулфилмент, модель, цвет, дата отправки, Общее количество,
                    # XS, S, M, L, XL, 2XL, 3XL, 4XL, 5XL, 6XL, 7XL, 8XL, Статус
                    row = [
                        timestamp,                    # время
                        username,                     # username
                        shipment_id,                  # номер отправки
                        bag_id,                       # номер пакета
                        shipment_type_ru,             # тип упаковки
                        warehouse,                    # склад
                        fulfillment,                  # фулфилмент
                        model,                        # модель
                        color,                        # цвет
                        shipment_date,                # дата отправки
                        total_quantity,               # Общее количество
                    ]

                    # Add size columns
                    for size in size_columns:
                        row.append(sizes.get(size, 0))

                    # Add status
                    row.append(status_ru)             # Статус

                    rows.append(row)

            # Append all rows to Google Sheets
            if rows:
                success = self.append_rows(sheet_name, rows)
                if success:
                    print(f"✅ Synced {len(rows)} rows to Google Sheets for shipment {shipment_id}")
                else:
                    print(f"❌ Failed to sync shipment {shipment_id} to Google Sheets")
                return success
            else:
                print(f"⚠️  No rows to sync for shipment {shipment_id}")
                return True

        except Exception as e:
            print(f"❌ Error syncing shipment to Google Sheets: {e}")
            import traceback
            traceback.print_exc()
            return False

    def update_shipment_status_in_sheets(
        self,
        shipment_id: str,
        new_status: str,
        supplier_name: str = None,
        sheet_name: str = None
    ) -> bool:
        """
        Update status for all rows of a shipment in Google Sheets.
        Searches in the supplier-specific sheet.

        Args:
            shipment_id: Shipment ID to update
            new_status: New status value
            supplier_name: Supplier name (used to find the correct sheet)
            sheet_name: Optional sheet name override

        Returns:
            True if successful, False otherwise
        """
        if not self.service or not settings.GOOGLE_SHEETS_SPREADSHEET_ID:
            return False

        try:
            # Translate status to Russian
            status_ru = {
                "новая отправка": "новая отправка",
                "SENT_FROM_FACTORY": "отправлено из цеха",
                "SHIPPED_FROM_FF": "Отправлено от фулфилмента",
                "DELIVERED": "доставлено"
            }.get(new_status, new_status)

            # Determine which sheet to update
            if not sheet_name:
                if supplier_name:
                    sheet_name = supplier_name
                else:
                    # If no supplier name provided, search all sheets
                    print("⚠️  No supplier name provided for status update")
                    return self._update_status_in_all_sheets(shipment_id, new_status)

            # Read all data to find rows with matching shipment_id
            all_data = self.read_range(f"{sheet_name}!A:Z")
            if not all_data:
                print(f"⚠️  No data found in sheet: {sheet_name}")
                return False

            # Find header row (assume it's the first row)
            if len(all_data) < 2:
                return False

            header = all_data[0]
            # Find column indices
            shipment_col_idx = None
            status_col_idx = None

            for idx, col_name in enumerate(header):
                if col_name == "номер отправки":
                    shipment_col_idx = idx
                elif col_name == "Статус":
                    status_col_idx = idx

            if shipment_col_idx is None or status_col_idx is None:
                print("❌ Could not find required columns in Google Sheets")
                return False

            # Find all rows with this shipment_id and update status
            updates = []
            for row_idx, row in enumerate(all_data[1:], start=2):  # Start from row 2 (skip header)
                if len(row) > shipment_col_idx and row[shipment_col_idx] == shipment_id:
                    # Update this row's status
                    # Column letter for status (convert index to letter)
                    status_col_letter = chr(65 + status_col_idx)  # 65 is 'A'
                    cell_range = f"{sheet_name}!{status_col_letter}{row_idx}"
                    updates.append((cell_range, new_status))

            # Perform batch update
            if updates:
                for cell_range, _ in updates:
                    self.write_range(cell_range, [[status_ru]])
                print(f"✅ Updated {len(updates)} rows in Google Sheets for shipment {shipment_id}")
                return True
            else:
                print(f"⚠️  No rows found for shipment {shipment_id}")
                return False

        except Exception as e:
            print(f"❌ Error updating shipment status in Google Sheets: {e}")
            return False

    def _update_status_in_all_sheets(self, shipment_id: str, new_status: str) -> bool:
        """
        Search all sheets and update the shipment status.
        Used when supplier name is not provided.

        Args:
            shipment_id: Shipment ID to update
            new_status: New status value

        Returns:
            True if at least one update was successful
        """
        try:
            # Translate status to Russian
            status_ru = {
                "новая отправка": "новая отправка",
                "SENT_FROM_FACTORY": "отправлено из цеха",
                "SHIPPED_FROM_FF": "Отправлено от фулфилмента",
                "DELIVERED": "доставлено"
            }.get(new_status, new_status)
            # Get all sheets in the spreadsheet
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=settings.GOOGLE_SHEETS_SPREADSHEET_ID
            ).execute()

            sheets = [
                sheet.get('properties', {}).get('title')
                for sheet in spreadsheet.get('sheets', [])
            ]

            success_count = 0
            for sheet_name in sheets:
                # Try to update in this sheet
                all_data = self.read_range(f"{sheet_name}!A:Z")
                if not all_data or len(all_data) < 2:
                    continue

                header = all_data[0]
                shipment_col_idx = None
                status_col_idx = None

                for idx, col_name in enumerate(header):
                    if col_name == "номер отправки":
                        shipment_col_idx = idx
                    elif col_name == "Статус":
                        status_col_idx = idx

                if shipment_col_idx is None or status_col_idx is None:
                    continue

                # Find and update rows
                updates = []
                for row_idx, row in enumerate(all_data[1:], start=2):
                    if len(row) > shipment_col_idx and row[shipment_col_idx] == shipment_id:
                        status_col_letter = chr(65 + status_col_idx)
                        cell_range = f"{sheet_name}!{status_col_letter}{row_idx}"
                        updates.append((cell_range, new_status))

                if updates:
                    for cell_range, _ in updates:
                        self.write_range(cell_range, [[status_ru]])
                    print(f"✅ Updated {len(updates)} rows in sheet '{sheet_name}'")
                    success_count += 1

            return success_count > 0

        except Exception as e:
            print(f"❌ Error searching all sheets: {e}")
            return False


# Singleton instance
sheets_service = GoogleSheetsService()
