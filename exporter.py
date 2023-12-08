from prometheus_client import start_http_server, Gauge
import random
import time
import requests
import os

PER_PAGE = 20

DEVICEAUTH_BASE_URI = "http://%s:%s" % (
    os.getenv("DEVICEAUTH_FQDN", "mender-device-auth"),
    os.getenv("DEVICEAUTH_PORT", "8080")
)

TENANTADM_BASE_URI = "http://%s:%s" % (
    os.getenv("TENANTADM_FQDN", "mender-tenantadm"),
    os.getenv("TENANTADM_PORT", "8080")
)

TENANT_COUNT = Gauge('mender_tenant_count', 'Number of currently active temants', ["group"])
DEVICES_COUNT = Gauge('mender_devices_count', 'Number of devices', ["tenant"])

def tenant_count():
    count = 0
    trial_count = 0
    active_count = 0
    inactive_count = 0
    ent_count = 0
    pro_count = 0
    other_count = 0
    headers = {
      'Accept': 'application/json'
    }
    page = 1
    while True:
        try:
            response = requests.get(
                    TENANTADM_BASE_URI + f"/api/internal/v1/tenantadm/tenants",
                    params = {
                        "page": page,
                        "per_page": PER_PAGE
                    },
                    headers = headers
            )

            for item in response.json():
                if item['status'] == "active":
                    active_count += 1

                    if item['trial'] == True:
                        trial_count += 1
                    if item['plan'] == "enterprise":
                        ent_count += 1
                    elif item['plan'] == "professional":
                        pro_count += 1
                    else:
                        other_count += 1

                else:
                    inactive_count += 1

            if len(response.json()) == 0:
                TENANT_COUNT.labels(group="total").set(count)
                TENANT_COUNT.labels(group="trial").set(trial_count)
                TENANT_COUNT.labels(group="active").set(active_count)
                TENANT_COUNT.labels(group="inactive").set(inactive_count)
                TENANT_COUNT.labels(group="professional").set(pro_count)
                TENANT_COUNT.labels(group="enterprise").set(ent_count)
                TENANT_COUNT.labels(group="other").set(other_count)
                break
            count = count + len(response.json())

        except Exception as e:
            print("ERROR - exception: ", e)
        else:
            page += 1

def devices_count():
    headers = {
      'Accept': 'application/json'
    }
    page = 1
    while True:
        try:
            response = requests.get(
                    TENANTADM_BASE_URI + f"/api/internal/v1/tenantadm/tenants",
                    params = {
                        "page": page,
                        "per_page": PER_PAGE
                    },
                    headers = headers
            )

            for item in response.json():
                if item['status'] != "suspended":
                    tenant_id = item["id"]
                    devices_count_by_tenant(tenant_id)

            if len(response.json()) == 0:
                break

        except Exception as e:
            print("ERROR - exception: ", e)
        else:
            page += 1

def devices_count_by_tenant(tenant_id):
    headers = {
      'Accept': 'application/json'
    }
    try:
        response = requests.get(
                DEVICEAUTH_BASE_URI + f"/api/internal/v1/devauth/tenants/" + 
                                        str(tenant_id) + 
                                        "/devices/count",
                headers = headers
        )
        number_of_devices = (response.json()["count"])
        if type(number_of_devices) == int:
            DEVICES_COUNT.labels(tenant=str(tenant_id)).set(number_of_devices)

    except Exception as e:
        print("ERROR - exception: ", e)


if __name__ == '__main__':
    start_http_server(8000)
    while True:
        tenant_count()
        devices_count()
        time.sleep(10)

