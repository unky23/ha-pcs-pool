from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class PCSBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool]


def _bool(value: Any) -> bool:
    if value is True:
        return True
    if value is False or value is None:
        return False
    try:
        return int(value) == 1
    except Exception:
        return False


BINARY_SENSOR_DESCRIPTIONS: tuple[PCSBinarySensorDescription, ...] = (
    PCSBinarySensorDescription(key="pump", name="PCS Pool Pompa", device_class=BinarySensorDeviceClass.RUNNING, icon="mdi:pump", value_fn=lambda c: _bool(c.get("ms1"))),
    PCSBinarySensorDescription(key="online", name="PCS Pool Online", device_class=BinarySensorDeviceClass.CONNECTIVITY, icon="mdi:lan-connect", value_fn=lambda c: _bool(c.get("ka"))),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(PCSBinarySensor(coordinator, entry, description) for description in BINARY_SENSOR_DESCRIPTIONS)


class PCSBinarySensor(CoordinatorEntity, BinarySensorEntity):
    entity_description: PCSBinarySensorDescription
    _attr_has_entity_name = False

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry, description: PCSBinarySensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"pcs_pool_{entry.entry_id}_{description.key}"
        self._attr_name = description.name

    @property
    def device_info(self):
        data = self.coordinator.data or {}
        controller_id = data.get("kid") or "pcs_pool_controller"
        return {
            "identifiers": {(DOMAIN, str(controller_id))},
            "name": "PCS Pool",
            "manufacturer": "PCS / PoolCS",
            "model": str(data.get("kn") or "PCS API Controller"),
            "sw_version": str(data.get("kv")) if data.get("kv") is not None else None,
            "suggested_area": data.get("kl"),
        }

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        return self.entity_description.value_fn(data)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        return {
            "controller_id": data.get("kid"),
            "controller_name": data.get("kn"),
            "location": data.get("kl"),
            "object_id": data.get("wid"),
            "object_name": data.get("wn"),
            "last_seen": data.get("kd"),
        }
