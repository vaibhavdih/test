trucks = []
HARD_STOP_TIME = 120  # minutes
SAME_TEHSIL_EXTRA_ALLOWABLE_DISTANCE = 5
SALES_ORDER_FIELDS = [
    "name",
    "so_id",
    "timestamp",
    "city",
    "state",
    "district",
    "tehsil",
    "delivery_point",
    "product",
    "order_qty",
    "qty",
    "channel",
    "plant",
    "location_id",
    "status",
    "is_clubbed",
    "is_unserviceable",
    "clubbed_order",
    "customer_",
]
CLUBBED_ORDER_FIELDS = [
    "name",
    "naming_series",
    "locs",
    "delivery_points",
    "customer",
    "tehsils",
    "qty",
    "channel",
    "plant",
    "timestamp",
    "latest_timestamp",
    "available_vehicles",
    "fulfilled",
    "is_unserviceable",
    "order_count",
    "status",
    "fulfillment_time",
    "vehicle_size",
]
VEHICLE_TYPES = {
    "42-46 MT": {"size": "42-46 MT", "name": "Trailer", "min": 42, "max": 46},
    "31-42 MT": {"size": "31-42 MT", "name": "Trailer", "min": 31, "max": 42},
    "25-31 MT": {"size": "25-31 MT", "name": "Turbo", "min": 25, "max": 31},
    "12-25 MT": {"size": "12-25 MT", "name": "Trucks", "min": 12, "max": 25},
}
PLANT_CODE_MAP = {
    "115004": {
        "name": "AGU",
        "latitude": 28.060612197020337,
        "longitude": 77.9465303542308,
        "city": "Aligarh",
        "state": "Uttar Pradesh",
    },
    "110004": {
        "name": "BGU",
        "latitude": 23.052228086246476,
        "longitude": 75.252294406142,
        "city": "Badnawar",
        "state": "Madhya Pradesh",
    },
    "111004": {
        "name": "DGU",
        "latitude": 20.892685419188687,
        "longitude": 74.78359024674248,
        "city": "Dhule",
        "state": "Maharashtra",
    },
    "113004": {
        "name": "JGU",
        "latitude": 28.477592849725927,
        "longitude": 76.40578253349013,
        "city": "Jhajjar",
        "state": "Haryana",
    },
    "102004": {
        "name": "NBH",
        "latitude": 28.49074996008648,
        "longitude": 76.40401871748006,
        "city": "Nimbera",
        "state": "Rajasthan",
    },
    "117004": {
        "name": "TGU",
        "latitude": 22.764691089439086,
        "longitude": 73.38906249685648,
        "city": "Tulsigam",
        "state": "Gujarat",
    },
}
PLANT_DISTANCE_VEHICLE_SIZE_MATRIX = {
    "115004": {
        "42-46 MT": [">", 100],
        "31-42 MT": [">", 100],
        "25-31 MT": ["<", 300],
        "12-25 MT": ["<", 200],
    },
    "110004": {
        "42-46 MT": [">", 150],
        "31-42 MT": [">", 150],
        "25-31 MT": ["<", 350],
        "12-25 MT": ["<", 300],
    },
    "111004": {
        "42-46 MT": [">", 100],
        "31-42 MT": [">", 100],
        "25-31 MT": ["<", 350],
        "12-25 MT": ["<", 200],
    },
    "113004": {
        "42-46 MT": [">", 50],
        "31-42 MT": [">", 50],
        "25-31 MT": ["<", 300],
        "12-25 MT": ["<", 300],
    },
    "102004": {
        "42-46 MT": [">", 150],
        "31-42 MT": [">", 150],
        "25-31 MT": ["<", 350],
        "12-25 MT": ["<", 150],
    },
    "117004": {
        "42-46 MT": [">", 100],
        "31-42 MT": [">", 100],
        "25-31 MT": ["<", 350],
        "12-25 MT": ["<", 150],
    },
}


def compare(a, b, operator_str):
    if operator_str == ">":
        return a >= b
    elif operator_str == "<":
        return a <= b


def get_matrix_constants():
    files = frappe.get_all(
        "File",
        filters={
            "file_name": [
                "in",
                [
                    "taluka-vehicle-size-matrix.json",
                    "dp-lat-lng-master.json",
                    "district-clubbing-distance-matrix.json",
                ],
            ]
        },
        fields=["file_url", "file_name"],
    )

    constants = {}
    for file in files:
        data = frappe.make_get_request(url=file["file_url"], verify=False)
        if file.file_name == "taluka-vehicle-size-matrix.json":
            constants["TALUKA_VEHICLE_SIZE_MATRIX"] = data

        if file.file_name == "dp-lat-lng-master.json":
            constants["DP_LAT_LNG_MASTER"] = data

        if file.file_name == "district-clubbing-distance-matrix.json":
            constants["DISTRICT_CLUBBING_DISTANCE_MATRIX"] = data

    return constants


constants = get_matrix_constants()
DISTRICT_CLUBBING_DISTANCE_MATRIX = constants["DISTRICT_CLUBBING_DISTANCE_MATRIX"]
TALUKA_VEHICLE_SIZE_MATRIX = constants["TALUKA_VEHICLE_SIZE_MATRIX"]
DP_LAT_LNG_MASTER = constants["DP_LAT_LNG_MASTER"]


def calculate_dp_distance(dp1, dp2):
    dp1lat = DP_LAT_LNG_MASTER[dp1]["latitude"]
    dp1lng = DP_LAT_LNG_MASTER[dp1]["longitude"]
    dp2lat = DP_LAT_LNG_MASTER[dp2]["latitude"]
    dp2lng = DP_LAT_LNG_MASTER[dp2]["longitude"]
    return haversine((dp1lat, dp1lng), (dp2lat, dp2lng))


def calculate_plant_dp_distance(plant, dp):
    plant_lat = PLANT_CODE_MAP[plant]["latitude"]
    plant_lng = PLANT_CODE_MAP[plant]["longitude"]
    dp_lat = DP_LAT_LNG_MASTER[dp]["latitude"]
    dp_lng = DP_LAT_LNG_MASTER[dp]["longitude"]
    return haversine((plant_lat, plant_lng), (dp_lat, dp_lng))


def get_available_vehicles_by_plant_and_distance(plant, dp):
    distance = calculate_plant_dp_distance(plant, dp)
    vehicles = []
    for i, _ in PLANT_DISTANCE_VEHICLE_SIZE_MATRIX[plant].items():
        if compare(distance, _[-1], f"{_[0]}"):
            vehicles.append(i)
    return vehicles


def order__get_available_vehicles(order):
    vehicles = set(TALUKA_VEHICLE_SIZE_MATRIX[order.tehsil]["vehicles"])
    vehicles_by_plant = set(
        get_available_vehicles_by_plant_and_distance(
            order["plant"], order["delivery_point"]
        )
    )
    return vehicles.intersection(vehicles_by_plant)


def order__split(order, available_vehicles):
    def split(num, ranges):
        x = None
        for i, j in ranges:
            m = round(num / i, 2)
            n = round(num / j, 2)
            if m == int(m) or n == int(n) or int(m) != int(n):
                x = math.ceil(n)
                break

        if x is None:
            if num < ranges[-1][0]:
                return []
            elif num > ranges[0][1]:
                return [ranges[0][1]]

        d = divmod(j * x - num, x)
        k = d[0]
        l = d[1]
        results = [j - k] * x
        for _ in range(math.floor(l)):
            results[_] = results[_] - 1
        results[-1] = results[-1] - (l % 1)
        return results

    vehicle_wt_range = [
        (VEHICLE_TYPES[i]["min"], VEHICLE_TYPES[i]["max"])
        for i in sorted(
            list(available_vehicles),
            reverse=True,
        )
    ]

    qties = split(order["qty"], vehicle_wt_range)
    if len(qties) == 0:
        frappe.db.set_value(
            "Sales Order",
            order["name"],
            {
                "status": "Unserviceable",
                "is_unserviceable": True,
                "unserviceable_remarks": "CANT_SPLIT_ORDER",
                "clubbed_order": "",
            },
        )
        return True

    for q in qties:
        new_so = frappe.get_doc(
            {
                "so_id": order["so_id"],
                "doctype": "Sales Order",
                "timestamp": order["timestamp"],
                "city": order["city"],
                "district": order["district"],
                "tehsil": order["tehsil"],
                "delivery_point": order["delivery_point"],
                "state": order["state"],
                "product": order["product"],
                "order_qty": order["order_qty"],
                "qty": q,
                "channel": order["channel"],
                "plant": order["plant"],
                "location_id": order["location_id"],
                "customer_": order["customer_"],
            }
        )
        new_so.insert()

    frappe.delete_doc("Sales Order", order["name"])


def truck__add(order, truck_idx):
    truck = trucks[truck_idx]

    truck_available_vehicles = truck["available_vehicles"]
    available_vehicles = list(
        truck_available_vehicles.intersection(
            set(TALUKA_VEHICLE_SIZE_MATRIX[order["tehsil"]]["vehicles"])
        )
    )
    truck["available_vehicles"] = available_vehicles

    locs = truck["locs"]
    locs.add(order["location_id"])
    truck["locs"] = locs

    tehsils = truck["tehsils"]
    tehsils.add(order["tehsil"])
    truck["tehsils"] = tehsils

    dps = truck["delivery_points"]
    dps.add(order["delivery_point"])
    truck["delivery_points"] = dps

    customers = truck["customer"]
    customers.add(order["customer_"])
    truck["customer"] = customers

    truck["qty"] = float(truck["qty"]) + float(order["qty"])

    truck["orders"].append(
        {
            {
                "doctype": "Sales Orders Table",
                "parent": truck["name"],
                "parenttype": "Clubbed Order",
                "parentfield": "orders",
                "sales_order": order["name"],
                "qty": order["qty"],
                "city": order["city"],
                "state": order["state"],
                "order_time": order["timestamp"],
            }
        }
    )

    trucks[truck_idx] = truck


def truck__check_and_fulfill(truck_idx, l_ts):
    truck = trucks[truck_idx]
    delay = divmod(((l_ts) - (truck["timestamp"])).total_seconds(), 60)[0]
    allowable_vehicles_by_time = []
    for i, j in {
        70: {"42-46 MT"},
        100: {"42-46 MT", "31-42 MT"},
        110: {"42-46 MT", "31-42 MT", "25-31 MT"},
    }.items():
        if delay <= i:
            allowable_vehicles_by_time = j
            break
    else:
        allowable_vehicles_by_time = {
            "42-46 MT",
            "31-42 MT",
            "25-31 MT",
            "12-25 MT",
        }

    vehicles = sorted(
        truck["available_vehicles"].intersection(allowable_vehicles_by_time)
    )

    vehicle_size = None
    for i in vehicles:
        threshold = 0.95
        if VEHICLE_TYPES[i]["min"] >= 31:
            threshold = 0.90
        if (
            truck["qty"] >= threshold * VEHICLE_TYPES[i]["min"]
            and truck["qty"] <= VEHICLE_TYPES[i]["max"]
        ):
            vehicle_size = i
            break

    if vehicle_size is None:
        return False

    # frappe.db.set_value(
    #     "Clubbed Order",
    #     truck.name,
    #     {
    #         "vehicle_size": vehicle_size,
    #         "fulfilled": True,
    #         "status": "Completed",
    #         "fulfillment_time": l_ts,
    #     },
    # )

    new_truck = frappe.get_doc(
        {
            "doctype": "Clubbed Order",
            "channel": truck["channel"],
            "plant": truck["plant"],
            "available_vehicles": json.dumps(list(truck["available_vehicles"])),
            "qty": truck["qty"],
            "locs": json.dumps(list(truck["locs"])),
            "tehsils": json.dumps(list(truck["tehsils"])),
            "delivery_points": json.dumps(list(truck["delivery_points"])),
            "customer": json.dumps(list(truck["customer"])),
            "fulfilled": True,
            "status": "Completed",
            "fulfillment_time": l_ts,
            "vehicle_size": vehicle_size
        }
    )
    new_truck.insert(ignore_permissions=True)

    tss = []
    for order in truck["orders"]:
        new_child_order = frappe.get_doc({
            "doctype": "Sales Orders Table",
            "parent": new_truck.name,
            "parenttype": "Clubbed Order",
            "parentfield": "orders",
            "sales_order": order["name"],
            "qty": order["qty"],
            "city": order["city"],
            "state": order["state"],
            "order_time": order["timestamp"]
        })
        new_child_order.insert(ignore_permissions=True)

        frappe.db.set_value(
            "Sales Order",
            order["name"],
            {
                "status": "Clubbed",
                "clubbed_order": truck["name"],
                "clubbing_time": l_ts,
            },
        )
        tss.append(order["timestamp"])

    min_ts = min(tss)  # ts
    max_ts = max(tss)  # l_ts
    o_count = len(truck["orders"])

    frappe.db.set_value("Clubbed Order", new_truck.name, {
        "timestamp": min_ts,
        "latest_timestamp": max_ts,
        "order_count": o_count
    })

    trucks[truck_idx]["active"] = False
    return True

def engine__get_orders(l_ts):
    query = """SELECT 
        customer_ AS customer,
        JSON_ARRAYAGG(
            JSON_OBJECT(
                'name', name,
                'so_id', so_id,
                'timestamp', `timestamp`,
                'city', city,
                'state', state,
                'district', district,
                'tehsil', tehsil,
                'delivery_point', delivery_point,
                'product', product,
                'order_qty', order_qty,
                'qty', qty,
                'channel', channel,
                'plant', plant,
                'location_id', location_id,
                'status', status,
                'is_clubbed', is_clubbed,
                'is_unserviceable', is_unserviceable,
                'clubbed_order', clubbed_order,
                'customer_', customer_
            )
        ) AS grouped_orders,
        COUNT(*) AS order_count
    FROM 
        `tabSales Order`
    WHERE status = "Confirmed"
    GROUP BY 
        customer_
    ORDER BY 
        order_count DESC;
    """
    query_result = frappe.db.sql(query, as_dict=True) or []

    if query_result == []:
        return {}

    result = {
        item["customer"]: json.loads(item["grouped_orders"]) for item in query_result
    }
    return result


def engine__check_constraints(order, truck):

    if order["plant"] != truck["plant"]:
        return False

    if order["channel"] != truck["channel"]:
        return False

    if len(trucks["locs"].union({order["location_id"]})) > 2:
        return False

    if len(truck["customers"].union({order["customer_"]})) > 2:
        return False

    dps = list(truck["delivery_points"])
    distance = calculate_dp_distance(order["delivery_point"], dps[0])
    allowable_distance = DISTRICT_CLUBBING_DISTANCE_MATRIX[order["district"]]
    if order.tehsil in truck["tehsils"]:
        allowable_distance = allowable_distance + SAME_TEHSIL_EXTRA_ALLOWABLE_DISTANCE

    if distance > allowable_distance:
        return False

    available_vehicles = truck["available_vehicles"].intersection(
        TALUKA_VEHICLE_SIZE_MATRIX[order["tehsil"]]
    )

    if truck["qty"] + order["qty"] > VEHICLE_TYPES[max(available_vehicles)]["max"]:
        return False

    return True


def engine_label_old_orders_to_unserviceable(l_ts):
    orders = engine__get_orders(l_ts)
    delay_point = frappe.utils.add_to_date(l_ts, minutes=-(HARD_STOP_TIME + 5))
    for customer, sales_orders in orders.items():
        for order in sales_orders:
            timestamp = frappe.utils.get_datetime(order["timestamp"])
            if timestamp < delay_point:
                frappe.db.set_value(
                    "Sales Order",
                    order["name"],
                    {
                        "status": "Unserviceable",
                        "is_unserviceable": True,
                        "unserviceable_remarks": "TIME_LIMIT_EXCEEDED",
                        "clubbed_order": "",
                    },
                )


def engine__main(l_ts):
    engine_label_old_orders_to_unserviceable(l_ts)
    sales_orders = engine__get_orders(l_ts)

    for customer, orders in sales_orders.items():
        for order in orders:
            if (
                order["tehsil"] not in TALUKA_VEHICLE_SIZE_MATRIX
                or order["district"] not in DISTRICT_CLUBBING_DISTANCE_MATRIX
                or order["delivery_point"] not in DP_LAT_LNG_MASTER
            ):
                frappe.db.set_value(
                    "Sales Order",
                    order["name"],
                    {
                        "status": "Unserviceable",
                        "is_unserviceable": True,
                        "unserviceable_remarks": "DATA_NOT_FOUND_IN_MASTER",
                        "clubbed_order": "",
                    },
                )
                continue

            available_vehicles = order__get_available_vehicles(order)
            if len(available_vehicles) == 0:
                frappe.db.set_value(
                    "Sales Order",
                    order["name"],
                    {
                        "status": "Unserviceable",
                        "is_unserviceable": True,
                        "unserviceable_remarks": "NO_ALLOWABLE_VEHICLES",
                        "clubbed_order": "",
                    },
                )
                continue

            mx_weight = VEHICLE_TYPES[max(available_vehicles)]["max"]
            if order["qty"] > mx_weight:
                order__split(order, available_vehicles)
                continue

            global trucks

            if len(trucks) == 0:
                trucks.append(
                    {
                        "timestamp": order["timestamp"],
                        "channel": order["channel"],
                        "plant": order["plant"],
                        "available_vehicles": available_vehicles,
                        "locs": set(),
                        "tehsils": set(),
                        "delivery_points": set(),
                        "customers": set(),
                        "qty": 0,
                        "active": True
                    }
                )
                truck__add(order, len(trucks) - 1)
                truck__check_and_fulfill(truck_idx, l_ts)
                continue

            truck_found = False
            truck_idx = None
            for idx, truck in enumerate(trucks):
                if not truck["active"]:
                    continue
                if not engine__check_constraints(order, truck):
                    continue

                truck_found = True
                truck_idx = idx
                break

            if not truck_found:
                trucks.append(
                    {
                        "timestamp": order["timestamp"],
                        "channel": order["channel"],
                        "plant": order["plant"],
                        "available_vehicles": available_vehicles,
                        "locs": set(),
                        "tehsils": set(),
                        "delivery_points": set(),
                        "customers": set(),
                        "qty": 0,
                        "active": True
                    }
                )
                truck_idx = len(trucks) - 1

            truck__add(order, truck_idx)
            truck__check_and_fulfill(truck_idx, l_ts)


engine_run_time = frappe.form_dict.l_ts
if not engine_run_time:
    engine_run_time = frappe.utils.add_to_date(
        frappe.get_doc("FTP-Import-Config").last_engine_run_time, minutes=5
    )

engine__main(engine_run_time)

ftp_config = frappe.get_doc("FTP-Import-Config")
ftp_config.last_engine_run_time = engine_run_time
ftp_config.save(ignore_permissions=True)
