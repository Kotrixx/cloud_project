import traceback
from datetime import datetime, timezone
from statistics import mean, stdev

from beanie import PydanticObjectId
from fastapi import FastAPI, HTTPException, Request
from starlette import status

from app.api_app.models.models import Worker, WorkerUsage, Topology
from app.api_app.models.schemas import WorkerCreationInput, WorkerUsageInput, RingTopologyInput, WorkerUsageOutput
from app.api_app.routes.linux_cluster import router
from app.utils.headnode_utils import create_ring_topology
from app.utils.limpiar_headnode1 import conectar_ssh, limpiar_headnode
from app.utils.limpiar_worker import limpiar_worker
from app.utils.llenar_headnode_paramiko import configurar_headnode
from app.utils.llenar_worker import configurar_worker
from app.utils.llenar_worker_new import procesar_workers
from app.utils.monitoring import get_cpu_usage, get_ram_usage, get_disk_usage, get_ram_info, get_cpu_cores_info


@router.get("/workers")
async def get_workers():
    workers = await Worker.all().to_list()

    return workers


@router.get("/topologies")
async def get_topologies():
    topologies = await Topology.all().to_list()
    return topologies


@router.get("/workers/usage/now")
async def get_workers_usage():
    workers = await Worker.all().to_list()  # Obtener todos los trabajadores desde la base de datos
    usage_list = []  # Lista para almacenar los datos de uso por cada worker

    for worker in workers:
        print(f'Monitoreando el worker: {worker.hostname} ({worker.ip})')

        # Obtener el histórico de los últimos N registros de uso del worker
        historical_data = await WorkerUsage.filter(worker_id=worker.id, timestamp__gte=datetime.utcnow() - timedelta(days=30)).all()

        # Extraer los valores históricos de uso
        cpu_usages = [data.cpu_usage for data in historical_data]
        ram_usages = [data.ram_usage_percentage for data in historical_data]
        ram_totals = [data.ram_total_gb for data in historical_data]
        ram_avails = [data.ram_available_gb for data in historical_data]
        cpu_cores = [data.total_cores for data in historical_data]
        idle_cores = [data.idle_cores_percentage for data in historical_data]
        disk_usages = [data.disk_usage for data in historical_data]

        # Calcular el promedio y desviación estándar de los valores históricos
        cpu_usage_avg = mean(cpu_usages) if cpu_usages else 0
        cpu_usage_stdev = stdev(cpu_usages) if len(cpu_usages) > 1 else 0

        ram_usage_avg = mean(ram_usages) if ram_usages else 0
        ram_usage_stdev = stdev(ram_usages) if len(ram_usages) > 1 else 0

        ram_total_avg = mean(ram_totals) if ram_totals else 0
        ram_available_avg = mean(ram_avails) if ram_avails else 0

        cpu_cores_avg = mean(cpu_cores) if cpu_cores else 0
        idle_cores_avg = mean(idle_cores) if idle_cores else 0

        disk_usage_avg = mean(disk_usages) if disk_usages else 0

        # Obtener los datos de uso actuales
        username = worker.hostname  # Asignar el hostname como username (ajustar si es diferente)
        password = worker.password_hashed  # Obtener la contraseña del worker

        # Obtener los datos de CPU, RAM, discos y núcleos
        cpu_usage = get_cpu_usage(worker.ip, username, password)
        ram_usage_percentage = get_ram_usage(worker.ip, username, password)
        ram_info = get_ram_info(worker.ip, username, password)
        disk_usage = get_disk_usage(worker.ip, username, password)
        cpu_cores_info = get_cpu_cores_info(worker.ip, username, password)

        # Estimar si el valor de consumo actual es coherente con los valores históricos
        cpu_usage_normalized = abs(cpu_usage - cpu_usage_avg) <= cpu_usage_stdev
        ram_usage_normalized = abs(ram_usage_percentage - ram_usage_avg) <= ram_usage_stdev
        disk_usage_normalized = abs(disk_usage - disk_usage_avg) <= (disk_usage_avg * 0.1)  # 10% tolerancia

        # Estructurar los datos obtenidos para este worker
        worker_usage_data = {
            'worker_id': str(worker.id),
            'hostname': worker.hostname,
            'ip': worker.ip,
            'cpu_usage': float(cpu_usage),
            'ram_usage_percentage': float(ram_usage_percentage),
            'ram_total_gb': ram_info['total_gb'],
            'ram_available_gb': ram_info['available_gb'],
            'total_cores': cpu_cores_info['total_cores'],
            'idle_cores_percentage': float(cpu_cores_info['idle_cores_percentage']),
            'disk_usage': disk_usage,  # Lista de diccionarios con información del disco
            'timestamp': datetime.utcnow().isoformat(),
            'cpu_usage_normalized': cpu_usage_normalized,
            'ram_usage_normalized': ram_usage_normalized,
            'disk_usage_normalized': disk_usage_normalized
        }

        # Añadir los datos del worker a la lista de uso
        usage_list.append(worker_usage_data)

    # Devolver la lista de uso de workers
    return usage_list


@router.post("/monitoring")
async def insert_monitoring_record(record: WorkerUsageOutput):
    worker_id = record.worker_id

    # Insertar el registro en la base de datos
    monitoring_record = WorkerUsage(
        worker_id=worker_id,
        cpu_usage=record.cpu_usage,
        ram_usage=record.ram_usage,
        disk_usage=record.disk_usage,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    result = await WorkerUsage.insert_one(monitoring_record)
    return {"status": "success", "result": str(result)}


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


@router.post("/configurar")
async def configurar(request: Request):
    try:
        # Leer el cuerpo del request y convertirlo a JSON
        json_data = await request.json()

        # Llamar a las funciones con los datos del JSON
        usuario = "ubuntu"
        contrasena = "ubuntu"
        configurar_headnode(json_data, usuario, contrasena, '10.20.12.238')
        procesar_workers(json_data, usuario, contrasena)
        return {"message": "Configuración completada con éxito"}
    except Exception as e:
        error_message = f"Error al procesar la solicitud: {str(e)}"
        error_traceback = traceback.format_exc()  # Obtiene la traza completa del error
        raise HTTPException(status_code=400, detail=f"{error_message}\nTraceback: {error_traceback}")


@router.post("/configurar_headnode")
async def configurar(request: Request):
    try:
        # Leer el cuerpo del request y convertirlo a JSON
        json_data = await request.json()

        # Llamar a las funciones con los datos del JSON
        usuario = "ubuntu"
        contrasena = 'ubuntu'
        contrasena2 = "kotrix123"
        configurar_headnode(json_data, usuario, contrasena2, '10.0.10.2')
        procesar_workers(json_data, usuario, contrasena)
        return {"message": "Configuración completada con éxito"}
    except Exception as e:
        error_message = f"Error al procesar la solicitud: {str(e)}"
        error_traceback = traceback.format_exc()  # Obtiene la traza completa del error
        raise HTTPException(status_code=400, detail=f"{error_message}\nTraceback: {error_traceback}")


@router.post("/limpiar_headnode")
async def limpiar_topo():
    try:
        usuario = "ubuntu"
        contrasena2 = "kotrix123"

        ssh_client = conectar_ssh("10.0.10.2", usuario, contrasena2)
        limpiar_headnode(ssh_client, contrasena2)
        ssh_client.close()
        return {"message": "Configuración completada con éxito"}
    except Exception as e:
        error_message = f"Error al procesar la solicitud: {str(e)}"
        error_traceback = traceback.format_exc()  # Obtiene la traza completa del error
        raise HTTPException(status_code=400, detail=f"{error_message}\nTraceback: {error_traceback}")


@router.post("/limpiar_worker")
async def limpiar_topo():
    try:
        limpiar_worker(1)
        limpiar_worker(2)
        limpiar_worker(3)
        return {"message": "Configuración completada con éxito"}
    except Exception as e:
        error_message = f"Error al procesar la solicitud: {str(e)}"
        error_traceback = traceback.format_exc()  # Obtiene la traza completa del error
        raise HTTPException(status_code=400, detail=f"{error_message}\nTraceback: {error_traceback}")


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
