"""
Repository for system configuration operations.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import SystemConfig, AuditLog
from ..schemas import SystemConfigCreate, SystemConfigUpdate
from .base import BaseRepository

class ConfigRepository(BaseRepository[SystemConfig]):
    """Repository for system configuration operations."""

    def __init__(self, session: Session):
        super().__init__(session, SystemConfig)

    def get_current_config(self) -> Dict[str, Any]:
        """
        Fetch current config.
        This implements the 'fetch current config' CRUD function.
        """
        try:
            stmt = select(SystemConfig)
            result = self.session.execute(stmt)
            configs = result.scalars().all()

            # Convert to dictionary format
            config_dict = {}
            for config in configs:
                config_dict[config.key] = config.value

            return config_dict
        except Exception as e:
            self.session.rollback()
            raise e

    def update_config_with_audit(self, key: str, new_value: Dict[str, Any],
                                user_id: Optional[str] = None,
                                ip_address: Optional[str] = None) -> Optional[SystemConfig]:
        """
        Update config with audit logging.
        This implements the 'update config with audit logging' CRUD function.
        """
        try:
            # Get current config
            current_config = self.get_by_key(key)

            # Prepare audit log data
            old_values = None
            if current_config:
                old_values = {'value': current_config.value}

            new_values = {'value': new_value}

            # Update the config
            if current_config:
                updated_config = self.update(current_config.id, {'value': new_value})
            else:
                # Create new config if it doesn't exist
                create_data = SystemConfigCreate(key=key, value=new_value)
                config_data = create_data.model_dump()
                updated_config = self.create(config_data)

            # Create audit log entry
            if updated_config:
                audit_data = {
                    'user_id': user_id,
                    'action': 'UPDATE' if current_config else 'CREATE',
                    'resource_type': 'system_config',
                    'resource_id': updated_config.id,
                    'old_values': old_values,
                    'new_values': new_values,
                    'ip_address': ip_address
                }
                audit_log = AuditLog(**audit_data)
                self.session.add(audit_log)
                self.session.flush()

            return updated_config
        except Exception as e:
            self.session.rollback()
            raise e

    def get_by_key(self, key: str) -> Optional[SystemConfig]:
        """Get configuration by key."""
        try:
            stmt = select(SystemConfig).where(SystemConfig.key == key)
            return self.session.execute(stmt).scalar_one_or_none()
        except Exception as e:
            self.session.rollback()
            raise e

    def get_config_value(self, key: str) -> Optional[Dict[str, Any]]:
        """Get configuration value by key."""
        config = self.get_by_key(key)
        return config.value if config else None

    def set_config_value(self, key: str, value: Dict[str, Any],
                        description: Optional[str] = None,
                        user_id: Optional[str] = None) -> SystemConfig:
        """Set configuration value, creating if it doesn't exist."""
        try:
            existing = self.get_by_key(key)

            if existing:
                # Update existing
                update_data = {'value': value}
                if description:
                    update_data['description'] = description
                return self.update(existing.id, update_data)
            else:
                # Create new
                create_data = {
                    'key': key,
                    'value': value,
                    'description': description or f'Configuration for {key}'
                }
                return self.create(create_data)
        except Exception as e:
            self.session.rollback()
            raise e

    def get_all_configs(self) -> List[SystemConfig]:
        """Get all configuration entries."""
        return self.get_all()

    def delete_config(self, key: str, user_id: Optional[str] = None,
                     ip_address: Optional[str] = None) -> bool:
        """Delete configuration with audit logging."""
        try:
            config = self.get_by_key(key)
            if not config:
                return False

            # Create audit log before deletion
            audit_data = {
                'user_id': user_id,
                'action': 'DELETE',
                'resource_type': 'system_config',
                'resource_id': config.id,
                'old_values': {'key': config.key, 'value': config.value},
                'ip_address': ip_address
            }
            audit_log = AuditLog(**audit_data)
            self.session.add(audit_log)

            # Delete the config
            result = self.delete(config.id)
            self.session.flush()

            return result
        except Exception as e:
            self.session.rollback()
            raise e

    def get_config_history(self, key: str) -> List[AuditLog]:
        """Get audit history for a configuration key."""
        try:
            from ..models import AuditLog

            stmt = (
                select(AuditLog)
                .where(
                    and_(
                        AuditLog.resource_type == 'system_config',
                        AuditLog.resource_id.in_(
                            select(SystemConfig.id).where(SystemConfig.key == key)
                        )
                    )
                )
                .order_by(AuditLog.timestamp.desc())
            )

            result = self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            self.session.rollback()
            raise e

    def validate_config_key(self, key: str) -> bool:
        """Validate if a configuration key exists."""
        return self.get_by_key(key) is not None

    def get_config_keys(self) -> List[str]:
        """Get list of all configuration keys."""
        try:
            stmt = select(SystemConfig.key)
            result = self.session.execute(stmt)
            return [row[0] for row in result.all()]
        except Exception as e:
            self.session.rollback()
            raise e