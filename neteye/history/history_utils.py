"""
History record limit management utilities
"""
from sqlalchemy.sql import func
from neteye.extensions import db, settings


class HistoryUtils:
    """
    Utility class providing record limit functionality for history tables
    Methods are dynamically injected into history model classes
    """
    @staticmethod
    def _to_non_negative(value) -> int:
        """Safely convert to non-negative integer; fallback to 0 on error."""
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0

    @classmethod
    def get_max_records_setting(cls):
        """
        Get the maximum records setting for this history type.
        Returns the setting value or 0 for unlimited.

        Note:
        This method is designed to be injected at runtime into
        SQLAlchemy-Continuum's dynamically generated version/transaction
        classes (e.g., `node_version`, `node_transaction`, etc.).
        Therefore, it must not rely on static inheritance and should work
        purely based on `cls.__tablename__` and application settings.
        """
        table_setting_map = {
            'command_histories': 'COMMAND_HISTORY_MAX_RECORDS',
            'node_version': 'NODE_HISTORY_MAX_RECORDS', 
            'interface_version': 'INTERFACE_HISTORY_MAX_RECORDS',
            'serial_version': 'SERIAL_HISTORY_MAX_RECORDS',
            'cable_version': 'CABLE_HISTORY_MAX_RECORDS',
            'arp_entry_version': 'ARP_ENTRY_HISTORY_MAX_RECORDS',
            # Transaction tables use same limits as their version counterparts
            'node_transaction': 'NODE_HISTORY_MAX_RECORDS',
            'interface_transaction': 'INTERFACE_HISTORY_MAX_RECORDS', 
            'serial_transaction': 'SERIAL_HISTORY_MAX_RECORDS',
            'cable_transaction': 'CABLE_HISTORY_MAX_RECORDS',
            'arp_entry_transaction': 'ARP_ENTRY_HISTORY_MAX_RECORDS',
        }

        table_name = cls.__tablename__
        setting_name = table_setting_map.get(table_name)

        if setting_name:
            return cls._to_non_negative(getattr(settings, setting_name, 0))
        else:
            return 0
    
    @classmethod
    def enforce_record_limit(cls):
        """
        Remove oldest records if limit is exceeded
        """
        max_records = cls.get_max_records_setting()
        
        # Skip if limit is 0 (unlimited) or not set
        if max_records <= 0:
            return
            
        # Count current records
        current_count = db.session.query(func.count(cls.id)).scalar()
        
        if current_count > max_records:
            # Calculate how many records to delete
            records_to_delete = current_count - max_records
            
            # Determine the timestamp column to use for ordering
            timestamp_column = getattr(cls, 'created_at', None) or getattr(cls, 'issued_at', None)
            if not timestamp_column:
                return  # No timestamp column found
            
            # Get the oldest records to delete
            oldest_records = db.session.query(cls.id).order_by(timestamp_column.asc()).limit(records_to_delete).all()
            
            # Delete the oldest records
            if oldest_records:
                oldest_ids = [record.id for record in oldest_records]
                db.session.query(cls).filter(cls.id.in_(oldest_ids)).delete(synchronize_session=False)
                db.session.commit()
    
    def add_with_limit(self):
        """
        Add record and enforce limit
        """
        try:
            db.session.add(self)
            db.session.commit()
            # Enforce record limit after successful addition
            self.__class__.enforce_record_limit()
        except Exception as e:
            db.session.rollback()
            raise
