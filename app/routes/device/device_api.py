from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import HTTPException
from starlette import status

"""from app.app.models.models import Device, DeviceData
from app.app.models.schemas import DeviceCreationInput
from app.app.routes.device import router


@router.get("/")
async def get_devices():
	devices = await Device.all().to_list()

	return devices


@router.get("/{device_id}")
async def get_device(device_id: PydanticObjectId):
	device = await Device.get(device_id)

	if not device:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with ID {device_id} not found")

	return device


@router.post("/")
async def create_device(device: DeviceCreationInput):
	device_object = Device(
		measuring_point_id=42069,
		device_serial_id=device.device_serial_id,
		device_type=device.device_type,
		variables=device.variables,
		data_mapping=device.data_mapping,
		timestamp_mapping=device.timestamp_mapping,
		created_at=datetime.now(tz=timezone.utc),
		updated_at=datetime.now(tz=timezone.utc)
	)
	await device_object.insert()

	return device


@router.get("/{device_id}/readings")
async def get_readings(device_id: PydanticObjectId, start_timestamp: int, end_timestamp: int, vars: str):
	device = await Device.get(device_id)

	if not device:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with ID {device_id} not found")

	start_datetime = datetime.fromtimestamp(start_timestamp)
	end_datetime = datetime.fromtimestamp(end_timestamp)
	var_list = vars.split(",")

	data_points = await DeviceData.find(
		DeviceData.device_id == device.device_serial_id,
		DeviceData.timestamp >= start_datetime,
		DeviceData.timestamp <= end_datetime,
	).sort(DeviceData.timestamp).to_list()

	grouped_data = dict()
	for data_point in data_points:
		if data_point.name in var_list:
			timestamp_str = data_point.timestamp.isoformat()
			if timestamp_str not in grouped_data:
				grouped_data[timestamp_str] = {
					"timestamp": data_point.timestamp,
					"variables": {}
				}
			grouped_data[timestamp_str]["variables"][data_point.name] = data_point.value

	response = list(grouped_data.values())

	return response"""
