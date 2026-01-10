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


# Singleton instance
sheets_service = GoogleSheetsService()
