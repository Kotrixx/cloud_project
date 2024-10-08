from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import HTTPException
from starlette import status

from app.api_app.models.models import Worker, WorkerUsage, Topology
from app.api_app.models.schemas import WorkerCreationInput, WorkerUsageInput, RingTopologyInput
from app.api_app.routes.linux_cluster import router
from app.utils.headnode_utils import create_ring_topology
from app.utils.llenar_worker import configurar_worker


@router.get("/workers")
async def get_workers():
    workers = await Worker.all().to_list()

    return workers


@router.get("/topologies")
async def get_topologies():
    topologies = await Topology.all().to_list()
    return topologies


@router.get("/workers_usage")
async def get_workers_usage():
    usage = await WorkerUsage.last().to_list()

    return usage


@router.post("/ring")
async def create_device(topology: RingTopologyInput):
    if topology.nodes != len(topology.node_networks):
        raise HTTPException(
            status_code=400,
            detail=f"node_networks must contain {topology.nodes} entries"
        )

    if topology.nodes != len(topology.dhcp_settings):
        raise HTTPException(
            status_code=400,
            detail=f"dhcp_settings must contain {topology.nodes} entries"
        )

    ring_topology_object = Topology(
        nodes=topology.nodes,
        topology_name=topology.name,
        node_networks=topology.node_networks,
        dhcp_settings=topology.dhcp_settings,
        vlan_settings=topology.vlan_settings,
        creation_timestamp=datetime.fromisoformat(topology.creation_timestamp),
        topology_type="ring"
    )
    topology_data = topology.dict()

    # Call the function that configures the topology
    create_ring_topology_from_json(topology_data)
    print("asdsadasd")
    await ring_topology_object.insert()

    return {"message": "Topology created successfully"}


@router.post("/vms")
async def create_device(
        worker: int
):
    print(worker)
    configurar_worker(worker)
    # configurar_worker(2)
    # configurar_worker(3)
    return {"message": "Topology created successfully"}


def create_ring_topology_from_json(data: dict):
    create_ring_topology(
        ovs_br_name='br-int',
        namespaces=data['namespaces'],
        veth_pairs=data['veth_pairs'],
        subinterfaces=data['subinterfaces'],
        gateway_ips=data['gateway_ips'],
        dnsmasq_configs=data['dnsmasq_configs'],
        vlan_tags=data['vlan_tags'],
        network_name=data['name']
    )


"""
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
