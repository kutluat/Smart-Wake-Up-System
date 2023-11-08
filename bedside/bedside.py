from machine import SoftI2C,Pin
import machine
import utime
import network
import ntptime
import ujson
import urandom
import time
from umqtt.simple import MQTTClient

coffee =Pin(13, machine.Pin.OUT)
coffee.on()

# WiFi ve NTP ayarları
WIFI_SSID = ''
WIFI_PASSWORD = ''
NTP_SERVER = "pool.ntp.org"


# Saat dilimini ayarla
TIMEZONE = 3  # Örneğin, Türkiye için GMT+3

# MQTT broker ayarları
MQTT_ALARM_TOPIC  = b"alarm"
MQTT_STATUS_TOPIC = b"alarm/status"
MQTT_BED_TOPIC    = b"coffee"


# Alarm saat ve dakikalarını tutacak değişkenler
alarm_hour = 0
alarm_minute = 0
alarm_active = False


# WiFi bağlantısını yap
def connect_to_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    if not wifi.isconnected():
        print("WiFi bağlanılıyor...")
        wifi.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wifi.isconnected():
            pass
    print("WiFi bağlantısı başarılı!")
    print("IP adresi:", wifi.ifconfig()[0])

# NTP sunucusuna senkronize ol
def sync_ntp_time():
    ntptime.host = NTP_SERVER
    ntptime.settime()

# Saat ve tarih bilgisini çek
def get_datetime():
    datetime = utime.localtime(utime.time() + TIMEZONE * 3600)
    year = datetime[0]
    month = datetime[1]
    day = datetime[2]
    hour = datetime[3]
    minute = datetime[4]
    second = datetime[5]
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(year, month, day, hour, minute, second)

# MQTT mesajlarını işle
def handle_mqtt_message(topic, msg):
    global alarm_hour, alarm_minute, alarm_active
    

    if topic == MQTT_ALARM_TOPIC:
        msg_str = msg.decode('utf-8') # bytes'i str'ye dönüştür
        msg_str  = msg_str.split(":") # ['20','52']
        alarm_hour = int(msg_str[0])
        alarm_minute = int(msg_str[1])       
        print("Alarm ayarlandı:", alarm_hour, ":", alarm_minute)
        
        
    elif topic == MQTT_STATUS_TOPIC:
        msg_str = msg.decode("utf-8")  # bytes'i str'ye dönüştür
        if msg_str == "1":
            alarm_active = True
            print("Alarm aktif!")
        elif msg_str == "0":
            alarm_active = False
            print("Alarm deaktif!")
            
            
    elif topic == MQTT_BED_TOPIC:
        msg_str = msg.decode("utf-8")  # bytes'i str'ye dönüştür
        if msg_str == "0":
            brew_coffee()
# MQTT bağlantısını yap
def connect_to_mqtt():
    client = MQTTClient(client_id='esp32/2',
                        server= b'',
                        port=0,
                        user= b'',
                        password = b'',
                        keepalive = 7200,
                        ssl = True,
                        ssl_params={''})
    client.set_callback(handle_mqtt_message)
    client.connect()
    client.subscribe(MQTT_ALARM_TOPIC)
    client.subscribe(MQTT_STATUS_TOPIC)
    client.subscribe(MQTT_BED_TOPIC)
    print("MQTT bağlantısı başarılı!")
    return client


# MQTT mesajlarını kontrol et
def check_mqtt_messages(client):
    client.check_msg()


def brew_coffee():
    coffee.off()
    time.sleep(10)
    coffee.on()

# WiFi'ı bağlan
connect_to_wifi()

# NTP sunucusuna senkronize ol
sync_ntp_time()

# MQTT bağlantısını yap
mqtt_client = connect_to_mqtt()

# Ana döngü
while True:
    # MQTT mesajlarını kontrol et
    check_mqtt_messages(mqtt_client)
    # Alarm kontrolünü yap

    time.sleep(1)

    






