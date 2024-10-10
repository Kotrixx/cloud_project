from fastapi import HTTPException
from starlette import status
from starlette.requests import Request

"""from app.api_app.models.models import DeviceData, Device, ReadingMetadata
from app.api_app.routes.readings import router
from app.api_app.utils.payload_utils import get_mapped_value, get_timestamp, extract_value


@router.post("/")
async def add_reading(request: Request):
	try:
		payload = await request.json()
		# dev_id = payload.get("records", [{}])[0].get("devId")
		dev_id = extract_value(payload, ["records", 0, "devId"])
		device = await Device.find_one(Device.device_serial_id == dev_id)
		if not device:
			raise HTTPException(status_code=404, detail={"status": "error", "message": "Device not found"})
		extracted_data = {}
		for mapping in device.data_mapping:
			value = get_mapped_value(payload, mapping.path, mapping.type)
			timestamp = get_timestamp(payload, device.timestamp_mapping.path, device.timestamp_mapping.format)
			dev_data = DeviceData(
				device_id=dev_id,
				value=value,
				name=mapping.variable_name,
				timestamp=timestamp,
			)
			await dev_data.insert()
		print(f"Received payload: {payload}")
		return {"status": "success", "message": "Payload received and processed successfully"}
	except Exception as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"status": "error", "message": str(e)})"""
