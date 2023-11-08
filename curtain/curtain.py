from machine import SoftI2C,Pin
from lcd_api import LcdApi
from i2c_lcd import I2cLcd
import machine
import utime
import network
import ntptime
import ujson
import urandom
import time
from umqtt.simple import MQTTClient
import dht


# WiFi ve NTP ayarları
WIFI_SSID = ''
WIFI_PASSWORD = ''
NTP_SERVER = "pool.ntp.org"


motorA1 = Pin(12, Pin.OUT)
motorA2 = Pin(13, Pin.OUT)
motorB1 = Pin(26, Pin.OUT)
motorB2 = Pin(25, Pin.OUT)
# Saat dilimini ayarla
TIMEZONE = 3  # Örneğin, Türkiye için GMT+3

# MQTT broker ayarları
MQTT_ALARM_TOPIC  = b"alarm"
MQTT_STATUS_TOPIC = b"alarm/status"
MQTT_BED_TOPIC    = b"coffee"
MQTT_CURTAIN_STATUS_TOPIC = b"curtain/status"

# Alarm saat ve dakikalarını tutacak değişkenler
alarm_hour = 0
alarm_minute = 0
alarm_active = False
curtain_hour = 0
curtain_minute= 0


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
    global alarm_hour, alarm_minute, alarm_active, curtain_hour, curtain_minute

    if topic == MQTT_ALARM_TOPIC:
        msg_str = msg.decode('utf-8') # bytes'i str'ye dönüştür
        msg_str  = msg_str.split(":") # ['20','52']
        alarm_hour = int(msg_str[0])
        alarm_minute = int(msg_str[1])
        curtain_hour= alarm_hour
        curtain_minute = alarm_minute
        if curtain_minute >= 30:
            curtain_minute -= 30
        else:
            curtain_hour -= 1
            curtain_minute += 30
        
        print("Alarm ayarlandı:", alarm_hour, ":", alarm_minute)
    elif topic == MQTT_STATUS_TOPIC:
        msg_str = msg.decode("utf-8")  # bytes'i str'ye dönüştür
        if msg_str == "1":
            alarm_active = True
            print("Alarm aktif!")
        elif msg_str == "0":
            alarm_active = False
            print("Alarm deaktif!")
    
    elif topic == MQTT_CURTAIN_STATUS_TOPIC:
        msg_str = msg.decode("utf-8")
        if msg_str == "1":
            open_curtain()
            print("perde aciliyor")
            
        elif msg_str == "0":
            close_curtain()
            print("perde kapaniyor")
            
            
def open_curtain():
    # Set motor direction
    motorA1.value(1)
    motorA2.value(0)
    motorB1.value(1)
    motorB2.value(0)

    # Wait for 30 seconds
    time.sleep(10)

    # Stop motors
    motorA1.value(0)
    motorA2.value(0)
    motorB1.value(0)
    motorB2.value(0)


def close_curtain():
    # Set motor direction
    motorA1.value(0)
    motorA2.value(1)
    motorB1.value(0)
    motorB2.value(1)

    # Wait for 30 seconds
    time.sleep(10)

    # Stop motors
    motorA1.value(0)
    motorA2.value(0)
    motorB1.value(0)
    motorB2.value(0)

def check_curtain():
    current_datetime = get_datetime()
    if alarm_active and current_datetime.split()[1] == "{:02d}:{:02d}:00".format(curtain_hour, curtain_minute):
        open_curtain()
        print("perdeler aciliyor")
        


# MQTT bağlantısını yap
def connect_to_mqtt():
    client = MQTTClient(client_id='esp32/3',
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
    client.subscribe(MQTT_CURTAIN_STATUS_TOPIC)
    print("MQTT bağlantısı başarılı!")
    return client


# MQTT mesajlarını kontrol et
def check_mqtt_messages(client):
    client.check_msg()



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
    check_curtain()
    time.sleep(1)
    print(curtain_hour)
    print(curtain_minute)

    




