#Pillow version: 9.5
import copy
import math
import socket
import sqlite3
import os
import time
import threading
import datetime


from statistics import mean

import requests
from kivy.graphics import Rectangle, Color, Line
from kivy.uix.floatlayout import FloatLayout
#import matplotlib.pyplot as plt
import kivy

import xlsxwriter
from flask import Flask, request

from kivy.uix.image import Image
from kivy.app import App
from kivy.core.audio import SoundLoader
from kivy.properties import ListProperty, NumericProperty, DictProperty, StringProperty
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import sp
from kivy.metrics import dp
from kivy.graphics import Rectangle, Color
from kivy.uix.spinner import Spinner


from kivy.uix.scrollview import ScrollView
from kivy.properties import BooleanProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.slider import Slider
from kivy.clock import Clock
#from backend_kivyagg import FigureCanvasKivyAgg
from kivy import platform



if platform == "android":
    from android.permissions import Permission, request_permissions, check_permission
    permissions = [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]
    request_permissions(permissions)

    # Check if permissions are granted
    for permission in permissions:
        if not check_permission(permission):
            # Handle the case where permission is not granted
            print(f"Permission {permission} not granted.")






global db_file
db_file = 'monitoring_database.db'

global connecttoESP
connecttoESP = False






kivy.require("2.1.0")













class MainWindow(Screen): #Main screen
    stop_event = threading.Event()
    testing_enabled = False
    switch = False
    global flag
    flag = False
    global temp_dict
    global flow_dict
    global pressure_dict
    global batt_dict
    global data
    global add_interval
    global interval_time
    global notification_val
    global ringing
    global msg_box, StartStopFont, MultiplierStartStop, NotificationFontSize, MultiplierNotification
    global activelist
    add_interval = ''
    '''global temp
    global flow
    global pressure
    global batt
'''
    notification_val = {}
    temp_dict = {}
    flow_dict = {}
    pressure_dict = {}
    batt_dict = {}
    data = {}
    ringing = False
    msg_box = None
    activelist = []

    table_names = ListProperty([])
    switch_data = BooleanProperty(False)
    no_batt = StringProperty('')
    no_temp = StringProperty('')
    no_flow = StringProperty('')
    no_pressure = StringProperty('')
    temp_color = ListProperty([0, 0, 0, 1])
    remarks_temp = StringProperty('No Data')

    current_time = ''
    batt = NumericProperty(0)
    temp = NumericProperty(0)

    no_temp_color = ListProperty([0, 0, 0, 1])
    no_remarks_temp = StringProperty('No Data')
    no_flow_color = ListProperty([0, 0, 0, 1])
    no_remarks_flow = StringProperty('No Data')
    no_pressure_color = ListProperty([0, 0, 0, 1])
    no_remarks_pressure = StringProperty('No Data')



    ######################################
    Mainfontsize = NumericProperty(sp(20)) ##editable Main window font size
    PagePicSize = NumericProperty(180)
    MainButtonfontsize = NumericProperty(sp(15))
    #FontLayoutsize = NumericProperty(sp(20), sp(20))
    displayhint = NumericProperty(0.1)
    StartStopFont = sp(17)
    MultiplierStartStop = 2.75
    NotificationFontSize = sp(20)
    MultiplierNotification = 2.75




    ######################################



    flow = NumericProperty(0)
    flow_color = ListProperty([0, 0, 0, 1])
    remarks_flow = StringProperty('No Data')


    pressure = NumericProperty(0)
    pressure_color = ListProperty([0, 0, 0, 1])
    remarks_pressure = StringProperty('No Data')

    interval_time = ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00',
                     '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00',
                     '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00']
    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)  # White color in RGBA format
            self.rect = Rectangle(size=self.size, pos=self.pos)

        # Bind the size and position of the white background to the widget's size and position
        self.bind(size=self._update_rect, pos=self._update_rect)
        self.scheduled_interval = None  # To store the reference to the scheduled interval
        self.worker_thread = None

        '''self.start_button = Button(text='Start', on_release=self.start_testing)
        self.stop_button = Button(text='Stop', on_release=self.stop_testing)
        self.add_widget(self.start_button)
        self.add_widget(self.stop_button)'''

    def _update_rect(self, instance, value):
        # Update the size and position of the white background
        self.rect.size = instance.size
        self.rect.pos = instance.pos




    def main_guide(self, instance):
        image_content = Image(source='MAIN_guide.png', size=(200, 300), allow_stretch=True)

        # Create the popup with the image content
        popup = Popup(title='Main Page Guide', size_hint=(0.8, 0.9), background_color=(0, 0, 0.7, 0.8))

        # Close the popup when the close button is pressed
        close_button = Button(text='Close', size_hint=(0.25, 0.1), background_color=(0.8, 0, 0, 0.8), pos_hint={'center_x': 0.5})
        close_button.bind(on_press=lambda x: popup.dismiss())

        # Add the image content and close button to the popup content
        content_layout = BoxLayout(orientation='vertical')
        content_layout.add_widget(image_content)
        content_layout.add_widget(close_button)

        popup.content = content_layout
        popup.open()





    def sum_consecutive(self, lst):
        if not lst:
            return 0  # Return 0 for an empty list

        current_number = lst[0]
        current_count = 1
        max_number = current_number
        max_count = current_count

        for num in lst[1:]:
            if num == current_number:
                current_count += 1
            else:
                current_number = num
                current_count = 1

            if current_count > max_count:
                max_count = current_count
                max_number = current_number

        return max_number * max_count


    def notif_data(self):
        global notification_val, temperatures_sum, flows_sum, pressures_sum, ringing
        global notif_temperatures, notif_flows, notif_pressures, notif_battery


        notif_temperatures = []
        notif_flows = []
        notif_pressures = []
        notif_battery = []
        trigger = 600

        # Iterate through the dictionary
        for time, values in notification_val.items():
            if values['temperature'] is None:
                notif_temperatures.append(0)
            else:
                notif_temperatures.append(-1 if values['temperature'] <= 38.8 else 1 if values['temperature'] >= 41.2 else 0)

            if values['flow'] is None:
                notif_temperatures.append(0)
            else:
                notif_flows.append(-1 if values['flow'] <= 14.55 else 1 if values['flow'] >= 15 else 0)

            if values['pressure'] is None:
                notif_temperatures.append(0)
            else:
                notif_pressures.append(-1 if values['pressure'] <= 38.8 else 1 if values['pressure'] >= 41.2 else 0)

            notif_battery.append(values['battery'])

        temperatures_sum = self.sum_consecutive(notif_temperatures)
        flows_sum = self.sum_consecutive(notif_flows)
        pressures_sum = self.sum_consecutive(notif_pressures)

        print(f"/////////Temperatures: {notif_temperatures} : the sum: {temperatures_sum}")
        print(f"/////////Flows: {notif_flows}: the sum: {flows_sum}")
        print(f"/////////Pressures: {notif_pressures}: the sum: {pressures_sum}")
        print(f"/////////Batteries: {notif_battery}")
        if (abs(temperatures_sum * 10) > trigger or abs(flows_sum * 10) > trigger or abs(pressures_sum * 10) > trigger) and ringing is False:
            ringing = True
            self.play_ringtone(instance=None)
               #(abs(temperatures_sum * 10) > trigger or abs(flows_sum * 10) > trigger or abs(pressures_sum * 10) > trigger)
        else:
            print('condition not met')
            print(f'Temperature: {abs(temperatures_sum * 10)}')
            print(f'flow: {abs(flows_sum * 10)}')
            print(f'pressure: {abs(pressures_sum * 10)}')
            print(f'the ring is {ringing}')






    def play_ringtone(self, instance):
        global sound, sw_ring
        sw_ring = True
        # Assuming self.load_ringtone() returns a sound object
        sound = SoundLoader.load('ringtone.mp3')

        def play_sound():
            if sound:
                #while sw_ring is True:

                sound.play()



        # Create a thread and start it
        thread = threading.Thread(target=play_sound)
        thread.start()

    def ringing_error(self, instance):
        content = Label(text='Error, Ringtone is not Activated!')
        popup = Popup(title='Ringtone', content=content, size_hint=(None, None), size=(300*MultiplierNotification, 200*MultiplierNotification),background_color=(0.5, 0.5, 0.8, 0.7))
        popup.open()

    def stop_ringtone(self, instance):
        try:
            global ringing, sound, temperatures_sum, flows_sum, pressures_sum, sw_ring
            global notif_temperatures, notif_flows, notif_pressures, notification_val
            notif_temperatures = []
            notif_flows = []
            notif_pressures = []
            notification_val = {}

            temperatures_sum = 0
            flows_sum = 0
            pressures_sum = 0
            sw_ring = False
            sound.stop()
            threading.current_thread().running = False
            ringing = False
            # Schedule the stopping of the sound on the main thread
            Clock.schedule_once(lambda dt: sound.stop(), 0)
        except:
            # Show an error popup
            self.ringing_error(instance)




    def notification(self, instance):
        global temperatures_sum, flows_sum, pressures_sum, connecttoESP
        global notif_temperatures, notif_flows, notif_pressures, notif_battery
        global msg_box
        fsize = sp(15)
        val_limit = 0

        # Check if the variables are defined
        if 'temperatures_sum' not in globals() or 'flows_sum' not in globals() or 'pressures_sum' not in globals():
            # If not defined, call notif_data to initialize them
            self.notif_data()

        # Create a BoxLayout to hold the notification content
        content_layout = BoxLayout(orientation='vertical')

        # Add labels for temperature sum, flow sum, and pressure sum to the content layout
        if temperatures_sum < 0:

            content_layout.add_widget(Label(text=f'Temperature is Low for: {temperatures_sum * -10} second(s).', font_size=fsize))

        elif temperatures_sum > 0:

            content_layout.add_widget(Label(text=f'Temperature is High for: {temperatures_sum * 10} second(s).', font_size=fsize))
        else:
            if not notif_temperatures:
                content_layout.add_widget(Label(text=f'Temperature: No Data', font_size=fsize))
            else:
                content_layout.add_widget(Label(text=f'Temperature is Normal', font_size=fsize))

        if flows_sum < 0:

            content_layout.add_widget(Label(text=f'Flow is Low for: {flows_sum * -10} second(s).', font_size=fsize))
        elif flows_sum > 0:

            content_layout.add_widget(Label(text=f'Flow is High for: {flows_sum * 10} second(s).', font_size=fsize))
        else:
            if not notif_flows:
                content_layout.add_widget(Label(text=f'Flow: No Data', font_size=fsize))
            else:
                content_layout.add_widget(Label(text=f'Flow is Normal', font_size=fsize))

        if pressures_sum < 0:

            content_layout.add_widget(Label(text=f'Pressure is Low for: {pressures_sum * -10} second(s).', font_size=fsize))
        elif pressures_sum > 0:

            content_layout.add_widget(Label(text=f'Pressure is High for: {pressures_sum * 10} second(s).', font_size=fsize))
        else:
            if not notif_pressures:
                content_layout.add_widget(Label(text=f'Pressure: No Data', font_size=fsize))
            else:
                content_layout.add_widget(Label(text=f'Pressure is Normal', font_size=fsize))
        print(pressures_sum)
        print(flows_sum)
        print(temperatures_sum)
        if connecttoESP is True:
            if msg_box is None:
                msg_box = ''

                #Column 1
            elif pressures_sum > val_limit and flows_sum > val_limit:
                msg_box = 'OPTIMAL CONDITION'
            elif pressures_sum == 0 and flows_sum > val_limit:
                msg_box = 'Adequate pressure, good\nflow for most applications'
            elif pressures_sum < val_limit and flows_sum > val_limit:
                msg_box = 'Insufficient pressure, good\nflow indicates\nunderutilization'

                #Column 2
            elif pressures_sum > val_limit and flows_sum == 0:
                msg_box = 'Efficient, but not at\nmaximum capacity'
            elif pressures_sum == 0 and flows_sum == 0:

                msg_box = 'Balanced performance,\nmoderate efficiency'

            elif pressures_sum < val_limit and flows_sum == 0:
                msg_box = 'Insufficient pressure and\nflow, potential for system\nissues'

            #Column 3
            elif pressures_sum > val_limit and flows_sum < val_limit:
                msg_box = 'Potential issues, system\nmay not be performing well'
            elif pressures_sum == 0 and flows_sum < val_limit:
                msg_box = 'Adequate pressure, but low\nflow may impact performance'
            elif pressures_sum < val_limit and flows_sum < val_limit:
                msg_box = 'Critical issues, system\nmay not operate as intended'
            else:
                msg_box = ''
        else:
            msg_box = ''

        # Create a Label for the main notification message
        main_message = Label(text='Longest Recorded Value', font_size=NotificationFontSize)
        msg_label = Label(text=f'System:\n{msg_box}', font_size=NotificationFontSize,color=(0, 0, 0, 1),bold=True)

        # Set size hints for labels
        main_message.size_hint = (1, 0.3)  # 30% of the height
        msg_label.size_hint = (1, 0.2)  # 20% of the height

        # Create buttons
        button = Button(
            text='Stop Ringtone',
            size_hint=(1, None),
            size=(120*MultiplierNotification, 50*MultiplierNotification),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            on_release=self.stop_ringtone,
            background_color=(0, 0.7, 0, 0.7)
        )

        button2 = Button(
            text='Cancel',
            size_hint=(1, None),
            size=(120 * MultiplierNotification, 50 * MultiplierNotification),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            on_release=self.cancel,
            background_color=(0.7, 0, 0, 0.7)
        )

        # Create layouts
        main_layout = GridLayout(cols=1, spacing=10)
        msg_layout = GridLayout(cols=1, spacing=10)
        buttons_layout = GridLayout(cols=2, spacing=10)
        msg_layout_color = Color(0.8,0.8,0.8,0.5)  # Adjust the color values as needed
        msg_layout_background = Rectangle(pos=msg_layout.pos, size=msg_layout.size)

        def update_msg_layout_background(instance, value):
            msg_layout_background.pos = instance.pos
            msg_layout_background.size = instance.size

        msg_layout.bind(pos=update_msg_layout_background, size=update_msg_layout_background)

        msg_layout.canvas.before.add(msg_layout_color)
        msg_layout.canvas.before.add(msg_layout_background)

        # Add widgets to layouts
        msg_layout.add_widget(msg_label)
        buttons_layout.add_widget(button)
        buttons_layout.add_widget(button2)

        # Add layouts to the main layout
        main_layout.add_widget(main_message)
        main_layout.add_widget(content_layout)  # Assuming content_layout is defined somewhere
        main_layout.add_widget(msg_layout)
        main_layout.add_widget(buttons_layout)

        # Create the Popup with the main layout
        popup = Popup(
            title='Notification',
            content=main_layout,
            size_hint=(None, None),
            size=(300*MultiplierNotification, 500*MultiplierNotification),
            auto_dismiss=True,
            background_color=(0, 0.533, 0.62, 0.5),
            separator_color=(1, 1, 1, 1)
        )

        self.popup = popup
        popup.open()

    def cancel(self, instance):
        print("Ringtone stopped")
        # Dismiss the popup
        self.popup.dismiss()

    def start_testing(self, instance):
        if MainWindow.testing_enabled is False:
            MainWindow.testing_enabled = True
            self.worker_thread = threading.Thread(target=self.testing_thread, daemon = True)
            self.worker_thread.start()  # Schedule the testing function
            if MainWindow.switch is True:
                MainWindow.switch = False



    def stop_testing(self, instance):
        if MainWindow.testing_enabled is True:
            self.worker_thread = None
            MainWindow.testing_enabled = False

            print(MainWindow.testing_enabled)
            MainWindow.switch = True

    def delayed_call(self):
        # Using lambda to delay the call of testing_thread for 3 seconds
        delayed_function = lambda: time.sleep(3) or self.testing_thread()
        delayed_function()



    def testing_thread(self):
        global temp, flow, pressure, batt, current_time
        global temp1, flow1, pressure1, batt1, temptest, active1, activelist, data_transfer
        error_count = 0
        while MainWindow.switch is False:
            if MainWindow.testing_enabled is True:
                try:
                    activelist.append(active1)
                    if len(activelist) > 10:
                        activelist.pop(0)
                    print(activelist)
                    x = all(item == activelist[0] for item in activelist)
                    print(f"are all the same: {x}")

                    if x is False or len(activelist) < 7:
                        temp = float(temp1)

                        flow = float(flow1)
                        #flow = min(flow, 60)

                        pressure = float(pressure1)
                        pressure = min(pressure, 60)

                        batt = float(batt1)
                        data_transfer = True
                        current_time = datetime.datetime.now().time()
                        self.update_data(temp, flow, pressure, batt, current_time)
                        MainWindow.delayed_call()
                    else:
                        temp = 0
                        flow = 0
                        pressure = 0
                        batt = 0
                        self.stop_testing(instance=None)
                        data_transfer = False
                        current_time = datetime.datetime.now().time()
                        self.update_data(temp, flow, pressure, batt, current_time)
                        self.testing_thread()

                except Exception as e:
                    MainWindow.switch = True
                    if error_count == 0:
                        print(f"Error: {e}")
                        error_count += 1
                        


                        #MainWindow.testing_enabled = False



                threading.Event().wait(1)




        while MainWindow.switch is True:
            if MainWindow.testing_enabled is False:

                temp = None
                flow = None
                pressure = None
                batt = None
                current_time = datetime.datetime.now().time()


                self.update_data(temp, flow, pressure, batt, current_time)
                threading.Event().wait(1)

                print('repeat')
                print(MainWindow.testing_enabled)




    def update_data(self, temp, flow, pressure, batt, current_time):
        global notification_val

        if MainWindow.testing_enabled is True:
            self.switch_data = False



            self.temp = temp
            self.flow = flow
            self.pressure = pressure
            self.batt = batt
            self.current_time = current_time

            self.switch_data = self.switch_data
            self.no_temp = self.no_temp
            self.no_flow = self.no_flow
            self.no_pressure = self.no_pressure
            self.no_batt = self.no_batt
            #temp
            if 38.8 >= self.temp:
                self.temp_color = [1, 0, 0, 1]  # Red color
                self.remarks_temp = 'LOW'

            elif self.temp >= 41.2:
                self.temp_color = [1, 0, 0, 1]  # Red color
                self.remarks_temp = 'HIGH'

            else:
                self.temp_color = [0, 0.5, 0, 1]  # Green color
                self.remarks_temp = 'NORMAL'

            # flow
            if self.flow <= 14.55:
                self.flow_color = [1, 0, 0, 1]  # Red color
                self.remarks_flow = 'LOW'

            elif self.flow > 15:
                self.flow_color = [1, 0, 0, 1]  # Red color
                self.remarks_flow = 'HIGH'

            else:
                self.flow_color = [0, 0.5, 0, 1]  # Green color
                self.remarks_flow = 'NORMAL'

            #pressure
            if self.pressure <= 38.8:
                self.pressure_color = [1, 0, 0, 1]  # Red color
                self.remarks_pressure = 'LOW'

            elif self.pressure >= 41.2:
                self.pressure_color = [1, 0, 0, 1]  # Red color
                self.remarks_pressure = 'HIGH'

            else:
                self.pressure_color = [0, 0.5, 0, 1]  # Green color
                self.remarks_pressure = 'NORMAL'

        if MainWindow.testing_enabled is False:
            self.switch_data = True
            self.no_temp = 'No Data'
            self.no_flow = 'No Data'
            self.no_pressure = 'No Data'
            self.no_batt = 'No Data'

            self.no_temp_color = [0, 0, 0, 1]
            self.no_remarks_temp = 'No Data'
            self.no_flow_color = [0, 0, 0, 1]
            self.no_remarks_flow = 'No Data'
            self.no_pressure_color = [0, 0, 0, 1]
            self.no_remarks_pressure = 'No Data'

        #write.to_database(temp, flow, pressure, batt, current_time)

        '''temp_dict[current_time] = temp
        flow_dict[current_time] = flow
        pressure_dict[current_time] = pressure
        batt_dict[current_time] = batt'''
#############################################################################333

        interval_start = datetime.datetime(1, 1, 1, 0, 0, 0)
        original_interval_end = datetime.datetime(1, 1, 1, 0, 0, 10)
        interval_end = original_interval_end
        second_step = 10
        time_step = datetime.timedelta(seconds=second_step)

        global data

        while True:
            global add_interval
            current_time = datetime.datetime.now().time()
            is_within_interval = False

            interval = int(86400 / second_step)

            for _ in range(interval):
                current_time_seconds = current_time.hour * 3600 + current_time.minute * 60 + current_time.second
                interval_start_seconds = interval_start.time().hour * 3600 + interval_start.time().minute * 60 + interval_start.time().second
                original_interval_end_seconds = original_interval_end.time().hour * 3600 + original_interval_end.time().minute * 60 + original_interval_end.time().second

                if interval_start_seconds <= current_time_seconds <= original_interval_end_seconds:
                    is_within_interval = True
                    break  # Exit the loop if the current time is found within an interval
                # Update the interval start and end for the next iteration
                interval_start += time_step
                original_interval_end += time_step
                interval_end = original_interval_end

            if is_within_interval:
                current_time_formatted = current_time.strftime("%H:%M:%S")
                interval_start_formatted = interval_start.time().strftime("%H:%M:%S")
                interval_end_formatted = interval_end.time().strftime("%H:%M:%S")

                print(f"Interval start: {interval_start.time()}, End of interval: {interval_end.time()}")
                print(f"Time: {current_time}")
                add_interval = interval_end.time()
                print(f'add: {type(add_interval)}')

                try:
                    if MainWindow.switch is False:
                        random_temperature = temp  # Example random temperature
                        random_flow = flow  # Example random flow
                        random_pressure = pressure  # Example random pressure
                        random_battery = batt  # Example random battery
                    else:
                        random_temperature = None  # Example random temperature
                        random_flow = None  # Example random flow
                        random_pressure = None  # Example random pressure
                        random_battery = None
                    data[current_time_formatted] = {
                        'temperature': random_temperature,
                        'flow': random_flow,
                        'pressure': random_pressure,
                        'battery': random_battery
                    }

                except Exception as e:
                    print(f"An error occurred: {e}")
                    if current_time_formatted in data:
                        del data[current_time_formatted]

                def validate(key, value, data):
                    if isinstance(value, (int, float)):
                        print(f"Random Number ({key}): {value}")
                        data[current_time_formatted][key] = value
                    else:
                        print(f"Random Number ({key}) is not a valid number.")
                        # If it's not a valid number, remove the entry.
                        data[current_time_formatted][key] = None

                validate('temperature', random_temperature, data)
                validate('flow', random_flow, data)
                validate('pressure', random_pressure, data)
                validate('battery', random_battery, data)

                print(data)
                print('                                    ')
                print('                                    ')
                if current_time_seconds == original_interval_end_seconds:
                    try:
                        try:

                            list_temperature = []
                            list_flow = []
                            list_pressure = []
                            list_battery = []

                            for timestamp, parameters in data.items():
                                list_temperature.append(parameters['temperature'])
                                list_flow.append(parameters['flow'])
                                list_pressure.append(parameters['pressure'])
                                list_battery.append(parameters['battery'])

                            total_temperature = [value for value in list_temperature if value is not None]
                            total_flow = [value for value in list_flow if value is not None]
                            total_pressure = [value for value in list_pressure if value is not None]
                            total_battery = [value for value in list_battery if value is not None]

                            count_temperature = len(total_temperature)
                            count_flow = len(total_flow)
                            count_pressure = len(total_pressure)
                            count_battery = len(total_battery)

                            if count_temperature > 0:
                                average_temperature = round(sum(total_temperature) / count_temperature, 2)
                            else:
                                average_temperature = None

                            if count_flow > 0:
                                average_flow = round(sum(total_flow) / count_flow, 2)
                            else:
                                average_flow = None

                            if count_pressure > 0:
                                average_pressure = round(sum(total_pressure) / count_pressure, 2)
                            else:
                                average_pressure = None

                            if count_battery > 0:
                                average_battery = round(sum(total_battery) / count_battery, 2)
                            else:
                                average_battery = None

                            current_time = datetime.datetime.now()
                            whole_number_time = current_time.hour * 3600 + current_time.minute * 60 + current_time.second


                            time_int = int(whole_number_time)

                            average_data = {
                                interval_end_formatted: {
                                    'id': time_int,
                                    'temperature': average_temperature,
                                    'flow': average_flow,
                                    'pressure': average_pressure,
                                    'battery': average_battery
                                }
                            }

                            current_date = datetime.date.today().strftime("Data_%B_%d_%Y")
                            connection = sqlite3.connect(db_file, isolation_level=None)
                            cursor = connection.cursor()
                            print("Connected to the database.")

                            table_name = f'{current_date}'
                            create_table_query = f'''
                                        CREATE TABLE IF NOT EXISTS {table_name} (
                                            time TEXT PRIMARY KEY,
                                            id REAL,
                                            temperature REAL NULL,
                                            flow REAL NULL,
                                            pressure REAL NULL,
                                            battery INTEGER NULL
                                        )
                                    '''
                            cursor.execute(create_table_query)

                            for time_key, values in average_data.items():
                                # Check if the time already exists in the table
                                cursor.execute(f'SELECT * FROM {table_name} WHERE time = ?', (time_key,))
                                existing_record = cursor.fetchone()

                                if existing_record:
                                    # Time exists, update the record
                                    update_query = f'''
                                        UPDATE {table_name}
                                        SET id=?, temperature=?, flow=?, pressure=?, battery=?
                                        WHERE time=?
                                    '''
                                    cursor.execute(update_query, (
                                    values['id'], values['temperature'], values['flow'], values['pressure'], values['battery'],
                                    time_key))
                                else:
                                    # Time doesn't exist, insert a new record
                                    insert_query = f'''
                                        INSERT INTO {table_name} (time, id, temperature, flow, pressure, battery)
                                        VALUES (?, ?, ?, ?, ?, ?)
                                    '''
                                    cursor.execute(insert_query, (
                                    time_key, values['id'], values['temperature'], values['flow'], values['pressure'],
                                    values['battery']))

                            # Commit the changes and close the connection
                            connection.commit()
                            connection.close()
                            print(f"Data inserted into {table_name}")
                            print(f"Data  {average_data}")
                            print(type(average_data))
                            #if any(val is None for nested_dict in data.values() for val in nested_dict.values()):
                            #    pass
                            #else:
                            notification_val.update(average_data)
                            self.notif_data()
                            data.clear()
                            average_data.clear()
                        except sqlite3.Error as e:
                            print(f"An error occurred: {e}")
                    except Exception as e:
                        print(f"An error occurred: {e}")
            else:
                print("The current time is outside all 5-second intervals.")

            wait_start = datetime.datetime.now()

            while (datetime.datetime.now() - wait_start).total_seconds() < 1:
                pass
            self.testing_thread()


    def active_temp(self, instance):
        global temp_active, n, interval_time, temp_sum
        self.ids.temp_layout.clear_widgets()
        fig, ax = plt.subplots()

        x_values = list(temp_active.keys())
        x_values = [str(datetime.timedelta(seconds=x)).zfill(8)[:5] for x in x_values]
        y_values = list(temp_active.values())

        high_y_value = 41.2
        plt.axhline(y=high_y_value, color='red', linestyle='dashed', alpha=0.35, linewidth=1, dashes=(8, 8))

        low_y_value = 38.8
        plt.axhline(y=low_y_value, color='red', linestyle='dashed', alpha=0.35, linewidth=1, dashes=(8, 8))

        # Set a smaller label font size and lower opacity for the legend


        # Set a smaller label font size



        # Plot the line for y-values
        ax.plot(x_values, y_values, color='blue')

        # Plot dummy points for x-axis labels, only use x-axis tick labels for visualization
        for x_value in x_values:
            if x_value not in interval_time:
                ax.plot([x_value], [0], color='white', marker='', linestyle='')

        # Rotate x-axis labels for better readability if needed
        plt.xticks(rotation=r)

        # Set the color and font size of x-axis tick labels
        x_ticks = ax.get_xticklabels()
        for tick in x_ticks:
            if tick.get_text() not in interval_time:
                tick.set_color('white')
                tick.set_fontsize(1)  # Adjust the font size as needed for visibility
            else:
                tick.set_color('black')
                tick.set_rotation(25)
                tick.set_fontsize(7)

        ax.grid(True)
        ax.legend()
        self.matplotlib_canvas = FigureCanvasKivyAgg(figure=fig)
        self.ids.temp_layout.add_widget(self.matplotlib_canvas)
        #temp_sum = temp_dict
        temp_active = {}



    def active_flow(self, instance):
        global flow_active, n, interval_time, flow_sum
        self.ids.flow_layout.clear_widgets()
        fig, ax = plt.subplots()

        x_values = list(flow_active.keys())
        x_values = [str(datetime.timedelta(seconds=x)).zfill(8)[:5] for x in x_values]
        y_values = list(flow_active.values())

        high_y_value = 15
        plt.axhline(y=high_y_value, color='red', linestyle='dashed', alpha=0.35, linewidth=1, dashes=(8, 8))

        low_y_value = 14.55
        plt.axhline(y=low_y_value, color='red', linestyle='dashed', alpha=0.35, linewidth=1, dashes=(8, 8))

        # Plot the line for y-values
        ax.plot(x_values, y_values, color='blue')

        # Plot dummy points for x-axis labels, only use x-axis tick labels for visualization
        for x_value in x_values:
            if x_value not in interval_time:
                ax.plot([x_value], [0], color='white', marker='', linestyle='')

        # Rotate x-axis labels for better readability if needed
        plt.xticks(rotation=r)

        # Set the color and font size of x-axis tick labels
        x_ticks = ax.get_xticklabels()
        for tick in x_ticks:
            if tick.get_text() not in interval_time:
                tick.set_color('white')
                tick.set_fontsize(1)  # Adjust the font size as needed for visibility
            else:
                tick.set_color('black')
                tick.set_rotation(25)
                tick.set_fontsize(7)

        ax.grid(True)
        ax.legend()
        self.matplotlib_canvas = FigureCanvasKivyAgg(figure=fig)
        self.ids.flow_layout.add_widget(self.matplotlib_canvas)
        #flow_sum = flow_dict
        flow_active = {}



    def active_pressure(self, instance):
        global pressure_active, n, interval_time, pressure_sum
        self.ids.pressure_layout.clear_widgets()
        fig, ax = plt.subplots()

        x_values = list(pressure_active.keys())
        x_values = [str(datetime.timedelta(seconds=x)).zfill(8)[:5] for x in x_values]
        y_values = list(pressure_active.values())

        high_y_value = 41.2
        plt.axhline(y=high_y_value, color='red', linestyle='dashed', alpha=0.35, linewidth=1, dashes=(8, 8))

        low_y_value = 38.8
        plt.axhline(y=low_y_value, color='red', linestyle='dashed', alpha=0.35, linewidth=1, dashes=(8, 8))
        # Plot the line for y-values
        ax.plot(x_values, y_values, color='blue')

        # Plot dummy points for x-axis labels, only use x-axis tick labels for visualization
        for x_value in x_values:
            if x_value not in interval_time:
                ax.plot([x_value], [0], color='white', marker='', linestyle='')

        # Rotate x-axis labels for better readability if needed
        plt.xticks(rotation=r)

        # Set the color and font size of x-axis tick labels
        x_ticks = ax.get_xticklabels()
        for tick in x_ticks:
            if tick.get_text() not in interval_time:
                tick.set_color('white')
                tick.set_fontsize(1)  # Adjust the font size as needed for visibility
            else:
                tick.set_color('black')
                tick.set_rotation(25)
                tick.set_fontsize(7)

        ax.grid(True)
        ax.legend()
        self.matplotlib_canvas = FigureCanvasKivyAgg(figure=fig)
        self.ids.pressure_layout.add_widget(self.matplotlib_canvas)
        #pressure_sum = pressure_dict
        pressure_active = {}



    def active_batt(self, instance):
        global batt_active, n, interval_time
        self.ids.batt_layout.clear_widgets()
        fig, ax = plt.subplots()

        x_values = list(batt_active.keys())
        x_values = [str(datetime.timedelta(seconds=x)).zfill(8)[:5] for x in x_values]
        y_values = list(batt_active.values())



        # Plot the line for y-values
        ax.plot(x_values, y_values, color='blue')

        # Plot dummy points for x-axis labels, only use x-axis tick labels for visualization
        for x_value in x_values:
            if x_value not in interval_time:
                ax.plot([x_value], [0], color='white', marker='', linestyle='')

        # Rotate x-axis labels for better readability if needed
        plt.xticks(rotation=r)

        # Set the color and font size of x-axis tick labels
        x_ticks = ax.get_xticklabels()
        for tick in x_ticks:
            if tick.get_text() not in interval_time:
                tick.set_color('white')
                tick.set_fontsize(1)  # Adjust the font size as needed for visibility
            else:
                tick.set_color('black')
                tick.set_rotation(25)
                tick.set_fontsize(7)

        ax.grid(True)
        ax.legend()
        self.matplotlib_canvas = FigureCanvasKivyAgg(figure=fig)
        self.ids.batt_layout.add_widget(self.matplotlib_canvas)
        batt_active = {}






    def active_graph(self, instance):

        repeat = 1
        interval_time = ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00',
                         '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00',
                         '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00']
        global temp_active, flow_active, pressure_active, batt_active
        temp_active = {}
        flow_active = {}
        pressure_active = {}
        batt_active = {}


        connection = sqlite3.connect(db_file, isolation_level=None)
        cursor = connection.cursor()
        data = datetime.datetime.now().strftime("Data_%B_%d_%Y")


        print(f'the date: {data}')


        for i in range(0, 86400, 3600):
            start_id = i
            end_id = i + 3600
            query = f"""
                SELECT AVG(temperature) as avg_temp, AVG(flow) as avg_flow, AVG(pressure) as avg_pressure, AVG(battery) as avg_batt 
                FROM {data} 
                WHERE id BETWEEN {start_id} AND {end_id}
            """
            try:
                cursor.execute(query)
                results = cursor.fetchall()
                print(f'the result: {results}')
                for row in results:
                    avg_temp, avg_flow, avg_pressure, avg_batt = row
                    temp_active[end_id] = avg_temp
                    flow_active[end_id] = avg_flow
                    pressure_active[end_id] = avg_pressure
                    batt_active[end_id] = avg_batt
            except:
                print('Date does not exist!')

        print(temp_active)
        print(flow_active)
        print(pressure_active)
        print(batt_active)








        today = datetime.datetime.now().strftime("%B %d %Y")
        try:
            if today:
                print("It is today")


                self.show_temp(instance)
                self.show_flow(instance)
                self.show_pressure(instance)
                self.show_batt(instance)

            else:


                self.show_temp(instance)
                self.show_flow(instance)
                self.show_pressure(instance)
                self.show_batt(instance)
        except:
            print("Date does not exist!")

        connection.commit()
        connection.close()




    def show_temp(self, instance):

        self.ids.temp_layout.clear_widgets()

        global temp_active, n, interval_time, temp_sum
        drawY = []


        # Add a blue rectangle to the canvas
        image = Image(source='graph-background.png', width=self.ids.temp_layout.width, size_hint_x=1)

        # Add the Image widget to the BoxLayout
        self.ids.temp_layout.add_widget(image)

        with self.ids.temp_layout.canvas:

            # Calculate line coordinates based on listX and listY
            listX = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
            listY = list(temp_active.values())
            print(f"the y values: {listY} and lenY {len(listY)} and lenX {len(listX)}")



            drawY = copy.copy(listY)
            print(f'the drawY: {drawY}')
            min_value = min(filter(lambda x: x is not None and x != 0, listY), default=None)

            # Replace every None or 0 with the minimum value
            listY = [min_value if x is None or x == 0 else x for x in listY]
            print(f"every listY{listY}")


            # Replace None values with 0
            for i in range(1, len(listY)):
                if listY[i] is None:
                    listY[i] = listY[i - 1]
            print(f"after convert{listY}")



            position_offset = (self.ids.temp_layout.width * (0.038), self.ids.temp_layout.height * 0.25) #changes!
            try:
                full = round(max(listY), 1)
                quarter = round(max(listY) / 4, 1)
                half = round(max(listY) / 2, 1)
                quarter2 = round(max(listY)*3/4, 1)
                zero = 0
                listY = [round(item, 1) for item in listY]
            except:
                full = 4
                quarter = 1
                half = 2
                quarter2 = 3
                zero = 0


            line_listY = [zero, quarter, half, quarter2, full]




            for y in line_listY:
                if y is not None:
                    line_color = Color(1, 1, 1, 1)  # Red line, fully opaque
                    line_position_x = self.ids.temp_layout.x + position_offset[0] + self.ids.temp_layout.width * (1 / max(listX)) * (0.5) + 2
                    line_position_y = (self.ids.temp_layout.y + position_offset[1] + 90 +
                                       self.ids.temp_layout.height * (y / max(line_listY)) * 0.515) - 2
                    line_length = self.ids.temp_layout.width * 1
                    line_points = [line_position_x, line_position_y,
                                   line_position_x + line_length, line_position_y]
                    Line(points=line_points, width=1, color=line_color)

            ################################
            temp_layout = self.ids.temp_layout

            # Create a new FloatLayout for floating labels
            float_layout = FloatLayout(size_hint=(None, None))
            temp_layout.add_widget(float_layout)
            for y in line_listY:
                if y is not None:
                    label_color = Color(0, 0, 0, 1)  # Black color, fully opaque
                    label_position_x = temp_layout.x + position_offset[0]
                    label_position_y = (
                            temp_layout.y
                            + position_offset[1]
                            + temp_layout.height * (y / max(line_listY)) * 0.5
                    )

                    label = Label(
                        text=str(y),
                        pos=(label_position_x - 50, (label_position_y * 0.985)+70),
                        color=label_color.rgb,
                        font_size=sp(7),
                    )

                    # Add the label to the new FloatLayout
                    float_layout.add_widget(label)








                    # Draw the label on the canvas with a colored rectangle





                    # Draw the label on the canvas
            print(f"the draw:{listY}")


            # Create a list of points by interleaving x and y coordinates
            points = []
            for x, y in zip(listX, listY):
                points.extend([
                    self.ids.temp_layout.x + position_offset[0] + self.ids.temp_layout.width * (x / max(listX)) * (0.94)-20,
                    self.ids.temp_layout.y + position_offset[1] + 80 + self.ids.temp_layout.height * (y / max(listY)) * 0.54
                ])
            for x, y in zip(listX, listY):
                x_pos = self.ids.temp_layout.x + position_offset[0] + self.ids.temp_layout.width * (x / max(listX)) * (
                    0.925)
                y_pos = self.ids.temp_layout.y + position_offset[1] + self.ids.temp_layout.height * (
                            y / max(listY)) * 0.7



            self.line_color = Color(0, 0, 1)
            self.line = Line(
                points=points,
                width=2.5  # Set line width (adjust as needed)
            )
            print(drawY)




            try:
                if drawY[0] is None:
                    drawY[0] = 0
                    self.draw_rectangle(0)
                for i in range(1, 24):
                    if drawY[i] is None:
                        self.draw_rectangle(i)
            except:
                print("No Database!")



            # Bind line points to update dynamically when the layout size changes


    def draw_rectangle(self, listypos):
        x1 = 0.088
        x2 = 0.0352
        resize_factor = x1  # per hour 0.037
        height_factor = 0.515
        heightposition_factor = 0.74
        position_factor = 0.788 - (2.02 * (listypos * x2))

        Color(0, 0, 0, 1)  # Set color to blue with alpha (RGB values + alpha)
        self.rectangle = Rectangle(
            pos=(self.ids.temp_layout.x + (self.ids.temp_layout.width * (1 - position_factor)) / 2 -55,
                 self.ids.temp_layout.y + (self.ids.temp_layout.height * ((1 - heightposition_factor)) / 0.63)),
            size=(self.ids.temp_layout.width * resize_factor, self.ids.temp_layout.height * height_factor+10))





    def show_flow(self, instance):

        self.ids.flow_layout.clear_widgets()
        global flow_active, n, interval_time, flow_sum
        drawY = []


        # Add a blue rectangle to the canvas
        image = Image(source='graph1-background.png', width=self.ids.flow_layout.width, size_hint_x=1)

        # Add the Image widget to the BoxLayout
        self.ids.flow_layout.add_widget(image)

        with self.ids.flow_layout.canvas:

            # Calculate line coordinates based on listX and listY
            listX = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
            listY = list(flow_active.values())
            print(f"the y values: {listY} and lenY {len(listY)} and lenX {len(listX)}")
            #listY = [max(0, x) for x in listY]


            drawY = copy.copy(listY)
            print(f'the drawY: {drawY}')
            min_value = min(filter(lambda x: x is not None and x != 0, listY), default=None)

            # Replace every None or 0 with the minimum value
            listY = [min_value if x is None or x == 0 else x for x in listY]
            print(f"every listY{listY}")


            # Replace None values with 0
            for i in range(1, len(listY)):
                if listY[i] is None:
                    listY[i] = listY[i - 1]
            print(f"after convert{listY}")



            position_offset = (self.ids.flow_layout.width * (0.038), self.ids.flow_layout.height * 0.25)

            try:
                full = round(max(listY), 1)
                quarter = round(max(listY) / 4, 1)
                half = round(max(listY) / 2, 1)
                quarter2 = round(max(listY)*3/4, 1)
                zero = 0
                listY = [round(item, 1) for item in listY]
            except:
                full = 4
                quarter = 1
                half = 2
                quarter2 = 3
                zero = 0
            line_listY = [zero, quarter, half, quarter2, full]



            for y in line_listY:
                if y is not None:
                    line_color = Color(1, 1, 1, 1)  # Red line, fully opaque
                    line_position_x = self.ids.flow_layout.x + position_offset[0] + self.ids.flow_layout.width * (1 / max(listX)) * (0.5) + 2
                    line_position_y = (self.ids.flow_layout.y + position_offset[1] + 90 +
                                       self.ids.flow_layout.height * (y / max(line_listY)) * 0.515) - 2
                    line_length = self.ids.flow_layout.width * 1  # Adjust the length as needed
                    line_points = [line_position_x, line_position_y,
                                   line_position_x + line_length, line_position_y]
                    Line(points=line_points, width=1, color=line_color)

            ################################
            flow_layout = self.ids.flow_layout

            # Create a new FloatLayout for floating labels
            float_layout = FloatLayout(size_hint=(None, None))
            flow_layout.add_widget(float_layout)
            for y in line_listY:
                if y is not None:
                    label_color = Color(0, 0, 0, 1)  # Black color, fully opaque
                    label_position_x = flow_layout.x + position_offset[0]
                    label_position_y = (
                            flow_layout.y
                            + position_offset[1]
                            + flow_layout.height * (y / max(line_listY)) * 0.5
                    )

                    label = Label(
                        text=str(y),
                        pos=(label_position_x - 50, (label_position_y * 0.985)+60),
                        color=label_color.rgb,
                        font_size=sp(7),
                    )

                    # Add the label to the new FloatLayout
                    float_layout.add_widget(label)



                    # Draw the label on the canvas with a colored rectangle





                    # Draw the label on the canvas
            print(f"the draw:{listY}")


            # Create a list of points by interleaving x and y coordinates
            points = []
            for x, y in zip(listX, listY):
                points.extend([
                    self.ids.flow_layout.x + position_offset[0] + self.ids.flow_layout.width * (x / max(listX)) * (0.94)-20,
                    self.ids.flow_layout.y + position_offset[1] + 80 + self.ids.flow_layout.height * (y / max(listY)) * 0.54
                ])
            for x, y in zip(listX, listY):
                x_pos = self.ids.flow_layout.x + position_offset[0] + self.ids.flow_layout.width * (x / max(listX)) * (
                    0.925)
                y_pos = self.ids.flow_layout.y + position_offset[1] + self.ids.flow_layout.height * (
                            y / max(listY)) * 0.7



            self.line_color = Color(0, 0, 1)
            self.line = Line(
                points=points,
                width=2.5  # Set line width (adjust as needed)
            )
            print(drawY)





            try:
                if drawY[0] is None:
                    drawY[0] = 0
                    self.draw_rectangle1(0)
                for i in range(1, 24):
                    if drawY[i] is None:
                        self.draw_rectangle1(i)
            except:
                print("No Database!")



            # Bind line points to update dynamically when the layout size changes


    def draw_rectangle1(self, listypos):
        x1 = 0.088
        x2 = 0.0352
        resize_factor = x1  # per hour 0.037
        height_factor = 0.515
        heightposition_factor = 0.74
        position_factor = 0.788 - (2.02 * (listypos * x2))

        Color(0, 0, 0, 1)  # Set color to blue with alpha (RGB values + alpha)
        self.rectangle = Rectangle(
            pos=(self.ids.flow_layout.x + (self.ids.flow_layout.width * (1 - position_factor)) / 2 -55,
                 self.ids.flow_layout.y + (self.ids.flow_layout.height * ((1 - heightposition_factor)) / 0.63)),
            size=(self.ids.flow_layout.width * resize_factor, self.ids.flow_layout.height * height_factor+10))




    def show_pressure(self, instance):

        self.ids.pressure_layout.clear_widgets()
        global pressure_active, n, interval_time, pressure_sum
        drawY = []


        # Add a blue rectangle to the canvas
        image = Image(source='graph2-background.png', width=self.ids.pressure_layout.width, size_hint_x=1)

        # Add the Image widget to the BoxLayout
        self.ids.pressure_layout.add_widget(image)

        with self.ids.pressure_layout.canvas:

            # Calculate line coordinates based on listX and listY
            listX = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
            listY = list(pressure_active.values())
            print(f"the y values: {listY} and lenY {len(listY)} and lenX {len(listX)}")



            drawY = copy.copy(listY)
            print(f'the drawY: {drawY}')
            min_value = min(filter(lambda x: x is not None and x != 0, listY), default=None)

            # Replace every None or 0 with the minimum value
            listY = [min_value if x is None or x == 0 else x for x in listY]
            print(f"every listY{listY}")


            # Replace None values with 0
            for i in range(1, len(listY)):
                if listY[i] is None:
                    listY[i] = listY[i - 1]
            print(f"after convert{listY}")



            position_offset = (self.ids.pressure_layout.width * (0.038), self.ids.pressure_layout.height * 0.25)

            try:
                full = round(max(listY), 1)
                quarter = round(max(listY) / 4, 1)
                half = round(max(listY) / 2, 1)
                quarter2 = round(max(listY)*3/4, 1)
                zero = 0
                listY = [round(item, 1) for item in listY]
            except:
                full = 4
                quarter = 1
                half = 2
                quarter2 = 3
                zero = 0
            line_listY = [zero, quarter, half, quarter2, full]



            for y in line_listY:
                if y is not None:
                    line_color = Color(1, 1, 1, 1)  # Red line, fully opaque
                    line_position_x = self.ids.pressure_layout.x + position_offset[0] + self.ids.pressure_layout.width * (1 / max(listX)) * (0.5) + 2
                    line_position_y = (self.ids.pressure_layout.y + position_offset[1] + 90 +
                                       self.ids.pressure_layout.height * (y / max(line_listY)) * 0.515) - 2
                    line_length = self.ids.pressure_layout.width * 1  # Adjust the length as needed
                    line_points = [line_position_x, line_position_y,
                                   line_position_x + line_length, line_position_y]
                    Line(points=line_points, width=1, color=line_color)

            ################################
            pressure_layout = self.ids.pressure_layout

            # Create a new FloatLayout for floating labels
            float_layout = FloatLayout(size_hint=(None, None))
            pressure_layout.add_widget(float_layout)
            for y in line_listY:
                if y is not None:
                    label_color = Color(0, 0, 0, 1)  # Black color, fully opaque
                    label_position_x = pressure_layout.x + position_offset[0]
                    label_position_y = (
                            pressure_layout.y
                            + position_offset[1]
                            + pressure_layout.height * (y / max(line_listY)) * 0.5
                    )

                    label = Label(
                        text=str(y),
                        pos=(label_position_x - 50, (label_position_y * 0.985)+50),
                        color=label_color.rgb,
                        font_size=sp(7),
                    )

                    # Add the label to the new FloatLayout
                    float_layout.add_widget(label)

                    # Draw the label on the canvas with a colored rectangle





                    # Draw the label on the canvas
            print(f"the draw:{listY}")


            # Create a list of points by interleaving x and y coordinates
            points = []
            for x, y in zip(listX, listY):
                points.extend([
                    self.ids.pressure_layout.x + position_offset[0] + self.ids.pressure_layout.width * (x / max(listX)) * (0.94)-20,
                    self.ids.pressure_layout.y + position_offset[1] + 80 + self.ids.pressure_layout.height * (y / max(listY)) * 0.54
                ])
            for x, y in zip(listX, listY):
                x_pos = self.ids.pressure_layout.x + position_offset[0] + self.ids.pressure_layout.width * (x / max(listX)) * (
                    0.925)
                y_pos = self.ids.pressure_layout.y + position_offset[1] + self.ids.pressure_layout.height * (
                            y / max(listY)) * 0.7



            self.line_color = Color(0, 0, 1)
            self.line = Line(
                points=points,
                width=2.5  # Set line width (adjust as needed)
            )
            print(drawY)





            try:
                if drawY[0] is None:
                    drawY[0] = 0
                    self.draw_rectangle2(0)
                for i in range(1, 24):
                    if drawY[i] is None:
                        self.draw_rectangle2(i)
            except:
                print("No Database!")



            # Bind line points to update dynamically when the layout size changes


    def draw_rectangle2(self, listypos):
        x1 = 0.088
        x2 = 0.0352
        resize_factor = x1  # per hour 0.037
        height_factor = 0.515
        heightposition_factor = 0.74
        position_factor = 0.788 - (2.02 * (listypos * x2))

        Color(0, 0, 0, 1)  # Set color to blue with alpha (RGB values + alpha)
        self.rectangle = Rectangle(
            pos=(self.ids.pressure_layout.x + (self.ids.pressure_layout.width * (1 - position_factor)) / 2 -55,
                 self.ids.pressure_layout.y + (self.ids.pressure_layout.height * ((1 - heightposition_factor)) / 0.63)),
            size=(self.ids.pressure_layout.width * resize_factor, self.ids.pressure_layout.height * height_factor+10))


    def show_batt(self, instance):

        self.ids.batt_layout.clear_widgets()

        global batt_active, n, interval_time, batt_sum
        drawY = []


        # Add a blue rectangle to the canvas
        image = Image(source='graph3-background.png', width=self.ids.batt_layout.width, size_hint_x=1)

        # Add the Image widget to the BoxLayout
        self.ids.batt_layout.add_widget(image)

        with self.ids.batt_layout.canvas:

            # Calculate line coordinates based on listX and listY
            listX = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
            listY = list(batt_active.values())
            print(f"the y values: {listY} and lenY {len(listY)} and lenX {len(listX)}")



            drawY = copy.copy(listY)
            print(f'the drawY: {drawY}')
            min_value = min(filter(lambda x: x is not None and x != 0, listY), default=None)

            # Replace every None or 0 with the minimum value
            listY = [98 if x is None or x == 0 else x for x in listY] #! change
            print(f"every listY{listY}")


            # Replace None values with 0
            for i in range(1, len(listY)):
                if listY[i] is None:
                    listY[i] = listY[i - 1]
            print(f"after convert{listY}")



            position_offset = (self.ids.batt_layout.width * (0.038), self.ids.batt_layout.height * 0.25)

            try:
                full = round(max(listY), 1)
                quarter = round(max(listY) / 4, 1)
                half = round(max(listY) / 2, 1)
                quarter2 = round(max(listY)*3/4, 1)
                zero = 0
                listY = [round(item, 1) for item in listY]
            except:
                full = 4
                quarter = 1
                half = 2
                quarter2 = 3
                zero = 0
            line_listY = [int(zero), int(quarter), int(half), int(quarter2), int(full)]



            for y in line_listY:
                if y is not None:
                    line_color = Color(1, 1, 1, 1)  # Red line, fully opaque
                    line_position_x = self.ids.batt_layout.x + position_offset[0] + self.ids.batt_layout.width * (1 / max(listX)) * (0.5) + 2
                    line_position_y = (self.ids.batt_layout.y + position_offset[1] + 90 +
                                       self.ids.batt_layout.height * (y / max(line_listY)) * 0.515) - 2
                    line_length = self.ids.batt_layout.width * 1  # Adjust the length as needed
                    line_points = [line_position_x, line_position_y,
                                   line_position_x + line_length, line_position_y]
                    Line(points=line_points, width=1, color=line_color)

            ################################
            batt_layout = self.ids.batt_layout

            # Create a new FloatLayout for floating labels
            float_layout = FloatLayout(size_hint=(None, None))
            batt_layout.add_widget(float_layout)
            for y in line_listY:
                if y is not None:
                    label_color = Color(0, 0, 0, 1)  # Black color, fully opaque
                    label_position_x = batt_layout.x + position_offset[0]
                    label_position_y = (
                            batt_layout.y
                            + position_offset[1]
                            + batt_layout.height * (y / max(line_listY)) * 0.5
                    )

                    label = Label(
                        text=str(y),
                        pos=(label_position_x - 50, (label_position_y * 0.985)+45),
                        color=label_color.rgb,
                        font_size=sp(7),
                    )

                    # Add the label to the new FloatLayout
                    float_layout.add_widget(label)

                    # Draw the label on the canvas with a colored rectangle





                    # Draw the label on the canvas
            print(f"the draw:{listY}")


            # Create a list of points by interleaving x and y coordinates
            points = []
            for x, y in zip(listX, listY):
                points.extend([
                    self.ids.batt_layout.x + position_offset[0] + self.ids.batt_layout.width * (x / max(listX)) * (0.94)-20,
                    self.ids.batt_layout.y + position_offset[1] + 80 + self.ids.batt_layout.height * (y / max(listY)) * 0.54
                ])
            for x, y in zip(listX, listY):
                x_pos = self.ids.batt_layout.x + position_offset[0] + self.ids.batt_layout.width * (x / max(listX)) * (
                    0.925)
                y_pos = self.ids.batt_layout.y + position_offset[1] + self.ids.batt_layout.height * (
                            y / max(listY)) * 0.7



            self.line_color = Color(0, 0, 1)
            self.line = Line(
                points=points,
                width=2.5  # Set line width (adjust as needed)
            )
            print(drawY)





            try:
                if drawY[0] is None:
                    drawY[0] = 0
                    self.draw_rectangle3(0)
                for i in range(1, 24):
                    if drawY[i] is None:
                        self.draw_rectangle3(i)
            except:
                print("No Database!")



            # Bind line points to update dynamically when the layout size changes

    def draw_rectangle3(self, listypos):
        x1 = 0.088
        x2 = 0.0352
        resize_factor = x1  # per hour 0.037
        height_factor = 0.515
        heightposition_factor = 0.74
        position_factor = 0.788 - (2.02 * (listypos * x2))

        Color(0, 0, 0, 1)  # Set color to blue with alpha (RGB values + alpha)
        self.rectangle = Rectangle(
            pos=(self.ids.batt_layout.x + (self.ids.batt_layout.width * (1 - position_factor)) / 2 -55,
                 self.ids.batt_layout.y + (self.ids.batt_layout.height * ((1 - heightposition_factor)) / 0.63)),
            size=(self.ids.batt_layout.width * resize_factor, self.ids.batt_layout.height * height_factor+10))
















    def stop_release_callback(self, instance):
        # Schedule the start_testing function with a delay of 1 second
        global connecttoESP, data_transfer
        if connecttoESP is True and data_transfer is True:
            Clock.schedule_once(lambda dt: self.stop_testing(instance), 1)

        else:
            layout = BoxLayout(orientation='vertical', spacing=10)
            label = Label(text='Stop Failed, No ESP8266 Connection', font_size=StartStopFont)
            cancel_button = Button(text='Dismiss', size_hint=(None,None), size=(120*MultiplierStartStop, 50*MultiplierStartStop),pos_hint={'center_x': 0.5, 'center_y': 0.5}, background_color=(1, 0, 0, 0.8))

            # Define the button callback to dismiss the popup
            def dismiss_popup(instance):
                connect_popup.dismiss()

            cancel_button.bind(on_press=dismiss_popup)

            # Add label and button to the layout
            layout.add_widget(label)
            layout.add_widget(cancel_button)

            # Create the popup
            connect_popup = Popup(title='', size_hint=(None, None), size=(300*MultiplierStartStop, 200*MultiplierStartStop),
                                  separator_color=(0, 0, 0, 0), background_color=(0.318, 0.749, 1, 0.8))
            connect_popup.content = layout

            # Open the popup
            connect_popup.open()


    def on_release_callback(self, instance):
        # Schedule the start_testing function with a delay of 1 second
        global connecttoESP, data_transfer
        if connecttoESP is True and data_transfer is True:
            Clock.schedule_once(lambda dt: self.start_testing(instance), 1)

        else:
            layout = BoxLayout(orientation='vertical', spacing=10)
            label = Label(text='Start Failed, No ESP8266 Connection', font_size=StartStopFont)
            cancel_button = Button(text='Dismiss', size_hint=(None,None), size=(120*MultiplierStartStop, 50*MultiplierStartStop),pos_hint={'center_x': 0.5, 'center_y': 0.5}, background_color=(1, 0, 0, 0.8))

            # Define the button callback to dismiss the popup
            def dismiss_popup(instance):
                connect_popup.dismiss()

            cancel_button.bind(on_press=dismiss_popup)

            # Add label and button to the layout
            layout.add_widget(label)
            layout.add_widget(cancel_button)

            # Create the popup
            connect_popup = Popup(title='', size_hint=(None,None), size=(300*MultiplierStartStop, 200*MultiplierStartStop),
                                  separator_color=(0, 0, 0, 0), background_color=(0.318, 0.749, 1, 0.8))
            connect_popup.content = layout

            # Open the popup
            connect_popup.open()



##################################################################




class ConnWindow(Screen):
    app_name_conn = StringProperty("Connection Setup")
    app_name_color_conn = ListProperty([1, 1, 1, 1])
    font_size_dp_conn = NumericProperty(40)
    background_color_conn = ListProperty([0.1, 0.2, 0.4, 0.8])
    flask_server = StringProperty()
    running_server = StringProperty()
    ESP_status = StringProperty()
    global data_transfer
    data_transfer = False
    global displayswitch
    displayswitch = True
    global MultiplierPortSelect, MultiplierDisplay, MultiplierServer, ServerFontSize
    global temptest
    temptest = None

    ##########################################
    ConnFontSize = NumericProperty(sp(25))
    MultiplierPortSelect = 2.75
    MultiplierDisplay = 1
    MultiplierServer = 2.75
    ServerFontSize = sp(17)
    ###########################################



    ###########################################

    def __init__(self, **kwargs):
        super(ConnWindow, self).__init__(**kwargs)
        self.app = Flask(__name__)
        self.temperature = None
        self.flow = None
        self.pressure = None
        self.battery = None
        self.active = None
        self.server_thread = None
        self.ESP_ip = None


        @self.app.route('/receive_data', methods=['GET'])
        def receive_data():

            global temp1, flow1, pressure1, batt1, active1
            global data_transfer, temptest, espip
            self.temperature = request.args.get('temperature')
            self.flow = request.args.get('flow')
            self.pressure = request.args.get('pressure')
            self.battery = request.args.get('battery')
            self.active = request.args.get('active')
            self.ESP_ip = request.args.get('ESP_ip')

            print(f"Received Data - Temperature: {self.temperature}, Flow: {self.flow}, Pressure: {self.pressure}, Battery: {self.battery}, Active: {self.active}, IP: {self.ESP_ip}")
            # Additional processing or database storage can be done here
            data_transfer = True
            temp1 = self.temperature
            flow1 = self.flow
            pressure1 = self.pressure
            batt1 = self.battery
            active1 = self.active
            espip = self.ESP_ip


            temptest = self.temperature

            return "Data Received"



    def conn_guide(self, instance):
        image_content = Image(source='CONN_guide.png', size=(200, 300), allow_stretch=True)

        # Create the popup with the image content
        popup = Popup(title='Connection Page Guide', size_hint=(0.8, 0.9), background_color=(0, 0, 0.7, 0.8))

        # Close the popup when the close button is pressed
        close_button = Button(text='Close', size_hint=(0.25, 0.1), background_color=(0.8, 0, 0, 0.8), pos_hint={'center_x': 0.5})
        close_button.bind(on_press=lambda x: popup.dismiss())

        # Add the image content and close button to the popup content
        content_layout = BoxLayout(orientation='vertical')
        content_layout.add_widget(image_content)
        content_layout.add_widget(close_button)

        popup.content = content_layout
        popup.open()

    def changewifi(self, instance):
        # Create a BoxLayout to hold the content and the buttons
        box_layout = BoxLayout(orientation='vertical')

        # Content of the popup (Labels and TextInputs)
        ssid_label = Label(text="SSID:")
        ssid_input = TextInput(multiline=False, hint_text='Enter WiFi Name for ESP8266')
        box_layout.add_widget(ssid_label)
        box_layout.add_widget(ssid_input)

        pass_label = Label(text="Password:")
        pass_input = TextInput(multiline=False, password=False, hint_text='Enter WiFi Password')
        box_layout.add_widget(pass_label)
        box_layout.add_widget(pass_input)

        ipdestination_label = Label(text="New IP Destination:")
        ipdestination_input = TextInput(multiline=False, hint_text='Enter the IP of the App')
        box_layout.add_widget(ipdestination_label)
        box_layout.add_widget(ipdestination_input)

        port_label = Label(text="Port Number:")
        port_input = TextInput(multiline=False, hint_text='Enter the port number of the App')
        box_layout.add_widget(port_label)
        box_layout.add_widget(port_input)

        ip_label = Label(text="ESP8266 IP:")
        ip_input = TextInput(multiline=False, hint_text='Enter the IP of the LCD in ESP8266')
        box_layout.add_widget(ip_label)
        box_layout.add_widget(ip_input)

        # Add a button to apply changes
        apply_button = Button(text="Apply Changes",
                              on_press=lambda x: self.apply_wifi_changes(ssid_input.text, pass_input.text,
                                                                         ip_input.text, ipdestination_input.text, port_input.text), background_color=(0, 0.8, 0, 0.8))
        box_layout.add_widget(apply_button)

        # Add a button to close the popup
        close_button = Button(text="Close", on_press=lambda x: wifi_popup.dismiss(), background_color=(0.8, 0, 0, 0.8))
        box_layout.add_widget(close_button)

        # Create and open the WiFiChangePopup
        if platform == "android":
            x = 350
            y = 500
        else:
            x = 300
            y = 200
        wifi_popup = Popup(title='ESP8266 WiFi Settings', content=box_layout, size_hint=(None, None), size=(x*2.75, y*2.75), background_color=(0.318, 0.749, 1, 0.8))
        wifi_popup.open()



    def apply_wifi_changes(self, ssid, password, ip, ipdestination, port):
        global port_number, host, result_message

        # Implement the logic to apply WiFi changes using ssid, password, and ip
        # For example, you can print them for now
        print("SSID:", ssid)
        print("Password:", password)
        print("Port Number: ", port)
        print("IP Destination: ", ipdestination)
        print("ESP8266 IP:",ip)

        try:

            esp8266_url = f"http://{ip}/update_wifi"

            payload = {'ssid': ssid, 'password': password, 'serverAddress': ipdestination, 'serverPort': port, 'Switch': True}
            response = requests.post(esp8266_url, data=payload)

            print(response.text)
            result_message = f"Success: {response.text}"
        except Exception as e:
            result_message = f"Failed to Update ESP8266!"
        self.show_result_popup(result_message)
    def show_result_popup(self, message):
        global result_message
        label = Label(text=message)

        # Create a close button
        close_button = Button(text='Close', size_hint=(None, None), size=(120*2.75, 50*2.75), pos_hint={'center_x': 0.5, 'center_y': 0.5}, background_color=(1, 0, 0, 0.8))
        close_button.bind(on_press=lambda instance: popup.dismiss())  # Bind the button press to dismiss the Popup

        # Create a layout to hold the label and close button
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(label)
        layout.add_widget(close_button)

        # Create the Popup with the layout as content
        popup = Popup(title='Update Result', content=layout, size_hint=(None, None), size=(300*2.75, 200*2.75), background_color=(0.318, 0.749, 1, 0.8))

        # Open the Popup
        popup.open()





    def display(self):
        global temp_dict, port_number, host, connecttoESP, displayswitch, temptest, data_transfer, espip

        print(temptest)
        try:
            print(espip)
        except:
            espip = None
        if displayswitch is True:
            try:
                if port_number is None or isinstance(port_number, str):
                    self.flask_server = 'OFF'
                    self.running_server = 'No Server'
                else:
                    if host is None:
                        self.flask_server = "OFF"
                        self.running_server = 'No Internet Connection'
                    else:
                        self.flask_server = "ON"
                        self.running_server = f'{host}:{port_number}'
            except:
                self.flask_server = 'OFF'
                self.running_server = 'No Server'
            displayswitch = False
        if data_transfer is True and espip is not None:

            self.ESP_status = f'CONNECTED: {espip}'
        else:

            self.ESP_status = "DISCONNECTED"


    def get_local_ip(self, instance):
        try:
            # Create a UDP socket to an external server (does not actually send data)
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp_socket.connect(("8.8.8.8", 80))  # Google's public DNS server
            local_ip = temp_socket.getsockname()[0]
            temp_socket.close()
            return local_ip
        except socket.error:
            return None

    def run_flask_server(self):
        global port_number, host
        host = self.get_local_ip(instance=None)

        # Run the Flask server in a separate thread
        server_thread = threading.Thread(target=self.app.run, kwargs={'host': '0.0.0.0', 'port': port_number})
        server_thread.start()

        return host


    def start_server(self):
        global connecttoESP, port_number, host, displayswitch
        try:
            if port_number is not None and not isinstance(port_number, str) and 0 < port_number <= 65535:
                if not self.server_thread or not self.server_thread.is_alive():
                    MainWindow.stop_testing(self,instance=None)
                    self.server_thread = threading.Thread(target=self.run_flask_server, daemon=True)
                    self.server_thread.start()
                    connecttoESP = True
                    displayswitch = True
                    print(connecttoESP)
                    layout = BoxLayout(orientation='vertical', spacing=10)
                    label = Label(text='Flask Server Successfully Created', font_size=ServerFontSize)
                    cancel_button = Button(text='Confirm', size_hint=(None, None), size=(120*MultiplierServer, 50*MultiplierServer),pos_hint={'center_x': 0.5, 'center_y': 0.5}, background_color=(0, 1, 0, 0.8))

                    # Define the button callback to dismiss the popup
                    def dismiss_popup(instance):
                        connect_popup.dismiss()

                    cancel_button.bind(on_press=dismiss_popup)

                    # Add label and button to the layout
                    layout.add_widget(label)
                    layout.add_widget(cancel_button)

                    # Create the popup
                    connect_popup = Popup(title='', size_hint=(None, None), size=(300*MultiplierServer, 200*MultiplierServer),
                                          separator_color=(0, 0, 0, 0), background_color=(0.318, 0.749, 1, 0.8))
                    connect_popup.content = layout

                    # Open the popup
                    connect_popup.open()
            else:
                x=1/0
                print(x)

        except Exception as e:
            # Replace 'print("hh")' with a Kivy popup
            layout = BoxLayout(orientation='vertical', spacing=10)
            label = Label(text='Server failed: No port number found', font_size=ServerFontSize)
            displayswitch = True

            cancel_button = Button(text='Confirm', size_hint=(None, None), size=(120*MultiplierServer, 50*MultiplierServer),pos_hint={'center_x': 0.5, 'center_y': 0.5}, background_color=(1, 0, 0, 0.8))

            # Define the button callback to dismiss the popup
            def dismiss_popup(instance):
                connect_popup.dismiss()

            cancel_button.bind(on_press=dismiss_popup)

            # Add label and button to the layout
            layout.add_widget(label)
            layout.add_widget(cancel_button)

            # Create the popup
            connect_popup = Popup(title='', size_hint=(None, None), size=(300*MultiplierServer, 200*MultiplierServer),
                                  separator_color=(0, 0, 0, 0), background_color=(0.318, 0.749, 1, 0.8))
            connect_popup.content = layout

            # Open the popup
            connect_popup.open()

    def stop_server(self):
        if self.server_thread and self.server_thread.is_alive():
            # Gracefully stop the Flask server
            self.app.shutdown()

    def port_selection(self, instance):
        # Your existing code for the 'port' method
        global port_number
        #port_number = None

        # Function to handle the "Submit" button click
        def on_submit(instance):
            global port_number
            port_number = text_input.text

            try:
                port_number = int(port_number)
                if 0 <= port_number <= 65535:
                    print(port_number)
                    popup_content = GridLayout(cols=1)  # Use a GridLayout with one column

                    # Add the label to the GridLayout
                    popup_content.add_widget(Label(text=f"Proceed with port {port_number}, Do you wish to continue?", pos_hint={'center_x': 0.5, 'center_y': 0.5}))

                    # Create a horizontal GridLayout for buttons
                    button_layout = GridLayout(cols=2)

                    # Add Confirm button
                    confirm_button = Button(text='Confirm', background_color=(0, 1, 0, 0.5), size=(120*2.75, 50*2.75),size_hint=(1, None))
                    button_layout.add_widget(confirm_button)
                    confirm_button.bind(on_press=lambda instance: popup.dismiss())

                    # Add Cancel button
                    cancel_button = Button(text='Cancel', background_color=(1, 0, 0, 0.5), size=(120*2.75, 50*2.75),size_hint=(1, None))
                    button_layout.add_widget(cancel_button)

                    # Bind the buttons to their respective actions
                    confirm_button.bind(on_press=on_cancel)
                    cancel_button.bind(on_press=lambda instance: popup.dismiss())

                    # Add the button layout to the main content layout
                    popup_content.add_widget(button_layout)

                    # Create the Popup with the modified content
                    popup = Popup(title='Port Number Confirmation', content=popup_content, size_hint=(None, None),
                                  size=(350*MultiplierPortSelect, 250*MultiplierPortSelect), background_color=(0.302, 0.922, 1, 1))

                    # Open the Popup
                    popup.open()
                else:
                    show_error_popup("Invalid Port Number", "Please enter a valid port number range (0-65535).")
                    port_number = None
            except ValueError:
                show_error_popup("Invalid Input", "Please enter a numeric value for the port.")
                port_number = None

        def on_cancel(instance):
            popup.dismiss()

        def deffault_port(instance):
            global port_number
            port_number = 8080
            print(port_number)
            popup.dismiss()

        def show_error_popup(title, content):
            # Create a BoxLayout for vertical alignment
            box_layout = BoxLayout(orientation='vertical')

            # Add a Label for the content with appropriate text alignment
            label = Label(text=content, halign='center', valign='middle')

            # Add an "OK" button to dismiss the popup
            ok_button = Button(text="CANCEL", size_hint=(None, None),pos_hint = {'center_x': 0.5, 'center_y': 0.5}, size = (120*MultiplierPortSelect, 50*MultiplierPortSelect), background_color=(0.7, 0, 0, 0.8))
            ok_button.bind(on_press=lambda instance: error_popup.dismiss())

            # Add the Label and Button to the BoxLayout
            box_layout.add_widget(label)
            box_layout.add_widget(ok_button)


            # Create the Popup with the BoxLayout as its content and set background color
            error_popup = Popup(title=title, content=box_layout, size_hint=(None, None), size=(300*MultiplierPortSelect,200*MultiplierPortSelect),
                                background_color=(0.302, 0.922, 1, 1))  # Adjust the color as needed

            # Display the Popup
            error_popup.open()

        # Creating the main GridLayout for the Popup content
        main_layout = GridLayout(cols=1, rows=3)  # Increase rows to 3

        # Adding a text input in the first row
        text_input = TextInput(hint_text='Enter Port Number')
        main_layout.add_widget(text_input)

        # Creating a sub-GridLayout for the first row with two columns
        sub_layout = GridLayout(cols=2)

        # Adding a button to the first column of the first row
        button1 = Button(text='Submit', background_color=(0, 0.7, 0, 0.8))
        button1.bind(on_press=on_submit)  # Bind the button to the submit function
        sub_layout.add_widget(button1)

        # Adding a button to the second column of the first row
        button2 = Button(text='Cancel', background_color=(0.7, 0, 0, 0.8))
        button2.bind(on_press=on_cancel)
        sub_layout.add_widget(button2)

        # Adding the sub-GridLayout to the main GridLayout
        main_layout.add_widget(sub_layout)

        # Creating the lower GridLayout with one column
        lower_layout = GridLayout(cols=1)

        # Adding a button to the lower GridLayout
        lower_button = Button(text='Default Port', background_color=(0.7, 0.7, 0.7, 0.8))
        lower_button.bind(on_press=deffault_port)
        lower_layout.add_widget(lower_button)

        # Adding the lower GridLayout to the main GridLayout
        main_layout.add_widget(lower_layout)

        # Creating the popup window with the main GridLayout as content
        popup_title = "Selection of Port Number"
        popup = Popup(title=popup_title, content=main_layout,
                      size_hint=(None, None), size=(300*MultiplierPortSelect, 200*MultiplierPortSelect),
                      background_color=(0.318, 0.749, 1, 0.729))
        popup.title_align = 'center'

        # Displaying the popup
        popup.open()

class GraphPopup(Popup):
    def __init__(self, fig, **kwargs):
        super(GraphPopup, self).__init__(**kwargs)
        self.size_hint = (None, None)  # Disable automatic sizing
        self.size = (500, 300)  # Set the desired size
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}  # Set the position to (0.5, 0.5)

        self.fig = fig
        self.graph_canvas = FigureCanvasKivyAgg(figure=self.fig)
        self.zoom_slider = Slider(min=0.1, max=2, value=1)
        self.zoom_slider.bind(value=self.on_zoom_slider)
        self.content = BoxLayout(orientation='vertical')
        self.content.add_widget(self.graph_canvas)
        self.content.add_widget(self.zoom_slider)

        self.graph_axes = self.fig.gca()
        self.graph_axes.grid(True)
    def on_zoom_slider(self, instance, value):
        self.graph_canvas.figure.set_size_inches(6 * value, 4 * value)
        self.graph_canvas.draw()


class GraphWindow(Screen): #3rd window
    global clear, r, selected_x
    global temp_sum, flow_sum, pressure_sum, batt_sum
    global Multiplier_ChooseDate, Multiplier_Confirmation,Multiplier_HighLow, Multiplier_Excel, Multiplier_Delete
    global HighLowFont, HighLowButtonFont
    Multiplier_ChooseDate = 2
    Multiplier_Confirmation = 2.75
    Multiplier_HighLow = 2
    Multiplier_Excel = 2.75
    Multiplier_Delete = 2.75

    temp_sum = {}
    flow_sum = {}
    pressure_sum = {}
    batt_sum = {}
    clear = 0

    r = 0
    table_list = ListProperty([])
    selected_table = StringProperty('None')


    LineWidth = NumericProperty(2) #kapal ng linya
    LineSpace = NumericProperty(1677) #distance
    SpaceMultiplier = NumericProperty(69.875)
    WidthDivider = NumericProperty(16)
    Y_Adjuster = NumericProperty(15)
    HighLowFont = sp(10)
    HighLowButtonFont = sp(10)

    #################################
    GraphPicSize = NumericProperty(150)
    DatabaseFontSize = NumericProperty(sp(25))


    #################################


    selected_x = ['00:00:00', '01:00:00', '02:00:00', '03:00:00', '04:00:00', '05:00:00', '06:00:00', '07:00:00',
                  '08:00:00', '09:00:00', '10:00:00', '11:00:00', '12:00:00', '13:00:00', '14:00:00', '15:00:00',
                  '16:00:00', '17:00:00', '18:00:00', '19:00:00', '20:00:00', '21:00:00', '22:00:00', '23:00:00']



    def graph_guide(self, instance):
        image_content = Image(source='GRAPH_guide.png', size=(200, 300), allow_stretch=True)

        # Create the popup with the image content
        popup = Popup(title='Graph Page Guide', size_hint=(0.8, 0.9), background_color=(0, 0, 0.7, 0.8))

        # Close the popup when the close button is pressed
        close_button = Button(text='Close', size_hint=(0.25, 0.1), background_color=(0.8, 0, 0, 0.8), pos_hint={'center_x': 0.5})
        close_button.bind(on_press=lambda x: popup.dismiss())

        # Add the image content and close button to the popup content
        content_layout = BoxLayout(orientation='vertical')
        content_layout.add_widget(image_content)
        content_layout.add_widget(close_button)

        popup.content = content_layout
        popup.open()




    def summary_popup(self):
        global temp_sum, flow_sum, pressure_sum, temp_dict, flow_dict, pressure_dict
        temp_sum = temp_dict
        flow_sum = flow_dict
        pressure_sum = pressure_dict



        temp_sum = {key: value for key, value in temp_sum.items() if value is not None and not 38.8 <= value <= 41.2}
        flow_sum = {key: value for key, value in flow_sum.items() if value is not None and not 14.55 <= value <= 15}
        pressure_sum = {key: value for key, value in pressure_sum.items() if value is not None and not 38.8 <= value <= 41.2}

        # Create a GridLayout with 4 columns and add widgets to it
        grid_layout = GridLayout(cols=3)
        temp_layout = GridLayout(cols=1)
        flow_layout = GridLayout(cols=1)
        pressure_layout = GridLayout(cols=1)

        button = Button(text=f'TEMPERATURE \n       SENSOR', size_hint=(0.5,0.25), font_size=HighLowFont, background_color=(0.5, 0.5, 0.8, 0.9))
        temp_layout.add_widget(button)
        temp_scroll_view = ScrollView()
        temp_layout.add_widget(temp_scroll_view)
        temp_scroll_grid = GridLayout(cols=1, size_hint_y=None)
        temp_scroll_grid.bind(minimum_height=temp_scroll_grid.setter('height'))

        for key, value in temp_sum.items():
            label_text = f'{key}: {value} {"Low" if value <= 38.8 else "High"}'
            button = Button(text=label_text, size_hint_y=None, height=40, background_color=(0.8, 0.5, 0.5, 0.7), font_size=HighLowButtonFont)
            temp_scroll_grid.add_widget(button)
        temp_scroll_view.add_widget(temp_scroll_grid)

        button = Button(text=f'  FLOW \nSENSOR', size_hint=(0.5,0.25), font_size=HighLowFont, background_color=(0.5, 0.5, 0.8, 0.9))
        flow_layout.add_widget(button)
        flow_scroll_view = ScrollView()
        flow_layout.add_widget(flow_scroll_view)
        flow_scroll_grid = GridLayout(cols=1, size_hint_y=None)
        flow_scroll_grid.bind(minimum_height=flow_scroll_grid.setter('height'))

        for key, value in flow_sum.items():
            label_text = f'{key}: {value} {"Low" if value <= 14.55 else "High"}'
            button = Button(text=label_text, size_hint_y=None, height=40, background_color=(0.8, 0.5, 0.5, 0.7), font_size=HighLowButtonFont)
            flow_scroll_grid.add_widget(button)
        flow_scroll_view.add_widget(flow_scroll_grid)

        button = Button(text=f'PRESSURE \n  SENSOR', size_hint=(0.5,0.25), font_size=HighLowFont,background_color=(0.5, 0.5, 0.8, 0.9))
        pressure_layout.add_widget(button)
        pressure_scroll_view = ScrollView()
        pressure_layout.add_widget(pressure_scroll_view)
        pressure_scroll_grid = GridLayout(cols=1, size_hint_y=None)
        pressure_scroll_grid.bind(minimum_height=pressure_scroll_grid.setter('height'))

        for key, value in pressure_sum.items():
            label_text = f'{key}: {value} {"Low" if value <= 38.8 else "High"}'
            button = Button(text=label_text, size_hint_y=None, height=40, background_color=(0.8, 0.5, 0.5, 0.7), font_size=HighLowButtonFont)
            pressure_scroll_grid.add_widget(button)

        pressure_scroll_view.add_widget(pressure_scroll_grid)

        grid_layout.add_widget(temp_layout)
        grid_layout.add_widget(flow_layout)
        grid_layout.add_widget(pressure_layout)

        # Create the Popup with the GridLayout as its content
        popup = Popup(title='High and Low Values',
                      title_align='center',
                      content=grid_layout,
                      size_hint=(None, None),
                      size=(500*Multiplier_HighLow, 800*Multiplier_HighLow),
                      background_color=(0.5, 0.5, 0.8, 0.7))

        # Bind the Popup size to the Window size
        popup.bind(size=lambda instance, value: setattr(popup, 'size', value))

        # Open the Popup
        popup.open()



    def save_popup(self, instance):
        # Create the layout for the popup
        layout = BoxLayout(orientation='vertical', padding=10)

        # Create the GridLayout for messages
        messages_layout = GridLayout(cols=2, rows=2, spacing=10, size_hint_y=0.5)
        messages_layout.bind(minimum_height=messages_layout.setter('height'))

        # Add messages to the GridLayout
        messages_layout.add_widget(Label(text='Do you want to save Graph as Excel?'))


        # Add the GridLayout to the main layout
        layout.add_widget(messages_layout)

        # Create a horizontal BoxLayout for buttons
        buttons_layout = BoxLayout(size_hint_y=0.3, height=50, spacing=10)

        # Add buttons to the buttons_layout
        buttons_layout.add_widget(
            Button(text='Save', on_release=lambda btn: self.save_to_excel_and_close(popup), size_hint=(1, None), size=(120*Multiplier_Excel, 50*Multiplier_Excel), background_color=(0, 0.5, 0, 0.7)))
        buttons_layout.add_widget(
            Button(text='Cancel', on_release=self.on_cancel_write, size_hint=(1, None), size=(120*Multiplier_Excel, 50*Multiplier_Excel),background_color=(0.5, 0, 0, 0.7)))

        # Add the buttons_layout to the main layout
        layout.add_widget(buttons_layout)

        # Create the popup and set its content
        popup = Popup(title='Save as Excel', content=layout, size_hint=(None, None), size=(300*Multiplier_Excel, 200*Multiplier_Excel),background_color=(0.5, 0.5, 0.8, 0.7))

        # Open the popup
        popup.open()













    def save_to_excel_and_close(self, popup):
        global absolute_path
        absolute_path = ''
        try:
            # Connect to SQLite database
            conn = sqlite3.connect(db_file, isolation_level=None)  # Replace 'your_database.db' with your database file
            cursor = conn.cursor()

            # Execute an SQL query to fetch data
            query = f"SELECT * FROM 'Data_{self.selected_table.replace(' ', '_')}';"
            cursor.execute(query)

            # Fetch all the data into a Pandas DataFrame
            columns = [description[0] for description in cursor.description]
            data = cursor.fetchall()
            list_of_dicts = [dict(zip(columns, row)) for row in data]

            # Create an Excel file
            excel_file = f"Data_{self.selected_table.replace(' ', '_')}.xlsx"

            # Use the appropriate path for the Downloads folder on Android
            downloads_folder = "/storage/emulated/0/Download"  # Adjust this path accordingly

            absolute_path = os.path.join(downloads_folder, excel_file)

            workbook = xlsxwriter.Workbook(absolute_path)
            worksheet = workbook.add_worksheet('Measurements')
            #absolute_path = os.path.abspath(excel_file)
            print(absolute_path)

            # Write headers
            for col_num, header in enumerate(columns):
                worksheet.write(0, col_num, header)

            # Write data
            for row_num, row_data in enumerate(list_of_dicts, 1):
                for col_num, cell_value in enumerate(columns):
                    worksheet.write(row_num, col_num, row_data.get(cell_value, ''))

            # Get the xlsxwriter workbook and worksheet objects
            worksheet.set_column('A:Z', 15)  # Adjust column width for better visibility

            # Add a border to all cells in the worksheet
            border_format = workbook.add_format({'border': 1})  # 1 represents a thin border
            worksheet.conditional_format(0, 0, len(list_of_dicts), len(columns) - 1,
                                         {'type': 'no_blanks', 'format': border_format})

            # Get the max row and column for the data
            max_row = len(list_of_dicts)
            max_col = len(columns)

            # CHART 2
            chart2 = workbook.add_chart({'type': 'line'})

            # Configure the series for the chart
            chart2.set_title({'name': 'Temperature Sensor', 'name_font': {'size': 50}})
            chart2.set_x_axis({'name': 'Time', 'name_font': {'size': 50}})
            chart2.set_y_axis({'name': 'Temperature', 'name_font': {'size': 50}})
            chart2.set_legend({'font': {'size': 25}})

            chart2.add_series({
                'name': 'Temperature',
                'name_font': {'size': 50, 'bold': True},
                'categories': f'=Measurements!$A$2:$A${max_row + 1}',
                'values': f'=Measurements!$C$2:$C${max_row + 1}',
            })
            chart2.set_size({'width': 10000, 'height': 1000})
            # Insert the chart into the worksheet
            worksheet2 = workbook.add_worksheet('Temperature Graph')
            worksheet2.insert_chart('C3', chart2)  # 'M2' is the top-left corner of the chart


            #CHART 3
            chart3 = workbook.add_chart({'type': 'line'})

            # Configure the series for the chart
            chart3.set_title({'name': 'Flow Sensor', 'name_font': {'size': 50}})
            chart3.set_x_axis({'name': 'Time', 'name_font': {'size': 50}})
            chart3.set_y_axis({'name': 'Flow', 'name_font': {'size': 50}})
            chart3.set_legend({'font': {'size': 25}})

            chart3.add_series({
                'name': 'Flow',
                'name_font': {'size': 50, 'bold': True},
                'categories': f'=Measurements!$A$2:$A${max_row + 1}',
                'values': f'=Measurements!$D$2:$D${max_row + 1}',
            })
            chart3.set_size({'width': 10000, 'height': 1000})
            # Insert the chart into the worksheet
            worksheet3 = workbook.add_worksheet('Flow Graph')
            worksheet3.insert_chart('C3', chart3)  # 'M2' is the top-left corner of the chart

            # CHART 4
            chart4 = workbook.add_chart({'type': 'line'})

            # Configure the series for the chart
            chart4.set_title({'name': 'Pressure Sensor', 'name_font': {'size': 50}})
            chart4.set_x_axis({'name': 'Time', 'name_font': {'size': 50}})
            chart4.set_y_axis({'name': 'Pressure', 'name_font': {'size': 50}})
            chart4.set_legend({'font': {'size': 25}})

            chart4.add_series({
                'name': 'Pressure',
                'name_font': {'size': 50, 'bold': True},
                'categories': f'=Measurements!$A$2:$A${max_row + 1}',
                'values': f'=Measurements!$E$2:$E${max_row + 1}',
            })
            chart4.set_size({'width': 10000, 'height': 1000})
            # Insert the chart into the worksheet
            worksheet4 = workbook.add_worksheet('Pressure Graph')
            worksheet4.insert_chart('C3', chart4)  # 'M2' is the top-left corner of the chart

            # CHART 5
            chart5 = workbook.add_chart({'type': 'line'})

            # Configure the series for the chart
            chart5.set_title({'name': 'Battery Sensor', 'name_font': {'size': 50}})
            chart5.set_x_axis({'name': 'Time', 'name_font': {'size': 50}})
            chart5.set_y_axis({'name': 'Battery Level', 'name_font': {'size': 50}})
            chart5.set_legend({'font': {'size': 25}})

            chart5.add_series({
                'name': 'Battery Meter',
                'name_font': {'size': 50, 'bold': True},
                'categories': f'=Measurements!$A$2:$A${max_row + 1}',
                'values': f'=Measurements!$F$2:$F${max_row + 1}',
            })
            chart5.set_size({'width': 10000, 'height': 1000})
            # Insert the chart into the worksheet
            worksheet5 = workbook.add_worksheet('Battery Meter Graph')
            worksheet5.insert_chart('C3', chart5)  # 'M2' is the top-left corner of the chart
            workbook.close()
            # Close the database connection
            conn.close()

            # Close the popup
            popup.dismiss()
            self.show_saving_popup()

        except Exception as e:
            # Display a popup with the exception message
            self.show_error_popup()
            print(e)

    def show_error_popup(self):
        content = Label(text=f'Please Try Again\n > Close any Excel Files \n > Select a date in the Set Graph\n > Delete Excel file with same name')
        popup = Popup(title='Error Saving', content=content, size_hint=(None, None), size=(300*Multiplier_Excel, 200*Multiplier_Excel), background_color=(0.5, 0.5, 0.8, 1))
        popup.open()
    def show_saving_popup(self):
        global absolute_path

        content = Label(text=f'Sucessfully Save to: Download Folder')
        print(absolute_path)
        popup = Popup(title='Successful Saving', content=content, size_hint=(None, None), size=(300*Multiplier_Excel, 200*Multiplier_Excel), background_color=(0.5, 0.5, 0.8, 1))
        popup.open()



    def active_graph(self, instance):
        try:
            repeat = 1
            interval_time = ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00',
                             '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00',
                             '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00']
            global temp_active, flow_active, pressure_active, batt_active
            temp_active = {}
            flow_active = {}
            pressure_active = {}
            batt_active = {}


            connection = sqlite3.connect(db_file, isolation_level=None)
            cursor = connection.cursor()
            #data = datetime.datetime.now().strftime("Data_%B_%d_%Y")

            data = f"Data_{self.selected_table.replace(' ', '_')}"
            print(f'the date: {data}')


            for i in range(0, 86400, 3600):
                start_id = i
                end_id = i + 3600
                query = f"""
                    SELECT AVG(temperature) as avg_temp, AVG(flow) as avg_flow, AVG(pressure) as avg_pressure, AVG(battery) as avg_batt 
                    FROM {data} 
                    WHERE id BETWEEN {start_id} AND {end_id}
                """
                try:
                    cursor.execute(query)
                    results = cursor.fetchall()
                    print(f'the result: {results}')
                    for row in results:
                        avg_temp, avg_flow, avg_pressure, avg_batt = row
                        temp_active[end_id] = avg_temp
                        flow_active[end_id] = avg_flow
                        pressure_active[end_id] = avg_pressure
                        batt_active[end_id] = avg_batt
                except:
                    print('Date does not exist!')

            print(temp_active)
            print(flow_active)
            print(pressure_active)
            print(batt_active)







            today = datetime.datetime.now().strftime("%B %d %Y")
            if self.selected_table == today:
                print("It is today")
                self.show_temp(instance)
                self.show_flow(instance)
                self.show_pressure(instance)
                self.show_batt(instance)

            else:
                self.show_temp(instance)
                self.show_flow(instance)
                self.show_pressure(instance)
                self.show_batt(instance)

            instance.parent.parent.parent.parent.parent.dismiss()
            connection.commit()
            connection.close()
        except:
            print("No Database!")
            self.ids.temp_layout.clear_widgets()
            self.ids.flow_layout.clear_widgets()
            self.ids.pressure_layout.clear_widgets()
            self.ids.batt_layout.clear_widgets()
            content = BoxLayout(orientation='vertical')
            label = Label(text="")
            close_button = Button(text="Close", background_color=(0.5, 0.5, 0.5, 0.8))
            content.add_widget(label)
            content.add_widget(close_button)

            success_popup = Popup(title="Reading Data Complete",
                                  content=content,
                                  size_hint=(None, None), size=(300 * Multiplier_Delete, 200 * Multiplier_Delete),
                                  auto_dismiss=True,
                                  background_color=(0.5, 0.5, 0.8, 0.7))

            close_button.bind(on_release=success_popup.dismiss)
            success_popup.open()




    def show_temp(self, instance):

        self.ids.temp_layout.clear_widgets()

        global temp_active, n, interval_time, temp_sum
        drawY = []


        # Add a blue rectangle to the canvas
        image = Image(source='graph-background.png', width=self.ids.temp_layout.width, size_hint_x=1)

        # Add the Image widget to the BoxLayout
        self.ids.temp_layout.add_widget(image)

        with self.ids.temp_layout.canvas:

            # Calculate line coordinates based on listX and listY
            listX = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
            listY = list(temp_active.values())
            print(f"the y values: {listY} and lenY {len(listY)} and lenX {len(listX)}")



            drawY = copy.copy(listY)
            print(f'the drawY: {drawY}')
            min_value = min(filter(lambda x: x is not None and x != 0, listY), default=None)

            # Replace every None or 0 with the minimum value
            listY = [min_value if x is None or x == 0 else x for x in listY]
            print(f"every listY{listY}")


            # Replace None values with 0
            for i in range(1, len(listY)):
                if listY[i] is None:
                    listY[i] = listY[i - 1]
            print(f"after convert{listY}")



            position_offset = (self.ids.temp_layout.width * (0.038), self.ids.temp_layout.height * 0.25) #changes!

            try:
                full = round(max(listY), 1)
                quarter = round(max(listY) / 4, 1)
                half = round(max(listY) / 2, 1)
                quarter2 = round(max(listY)*3/4, 1)
                zero = 0
            except:
                full = 4
                quarter = 1
                half = 2
                quarter2 = 3
                zero = 0
            line_listY = [zero, quarter, half, quarter2, full]

            listY = [round(item, 1) for item in listY]

            for y in line_listY:
                if y is not None:
                    line_color = Color(1, 1, 1, 1)  # Red line, fully opaque
                    line_position_x = self.ids.temp_layout.x + position_offset[0] + self.ids.temp_layout.width * (1 / max(listX)) * (0.5) #changes! 0.5
                    line_position_y = (self.ids.temp_layout.y + position_offset[1] +
                                       self.ids.temp_layout.height * (y / max(line_listY)) * 0.7)
                    line_length = self.ids.temp_layout.width * 0.9  # Adjust the length as needed
                    line_points = [line_position_x, line_position_y,
                                   line_position_x + line_length, line_position_y]
                    Line(points=line_points, width=1, color=line_color)

            ################################
            temp_layout = self.ids.temp_layout

            # Create a new FloatLayout for floating labels
            float_layout = FloatLayout(size_hint=(None, None))
            temp_layout.add_widget(float_layout)
            for y in line_listY:
                if y is not None:
                    label_color = Color(0, 0, 0, 1)  # Black color, fully opaque
                    label_position_x = temp_layout.x + position_offset[0]
                    label_position_y = (
                            temp_layout.y
                            + position_offset[1]
                            + temp_layout.height * (y / max(line_listY)) * 0.7
                    )

                    label = Label(
                        text=str(y),
                        pos=(label_position_x - 38, label_position_y * 0.985 -2),   #changes!
                        color=label_color.rgb,
                        font_size=sp(10),
                    )

                    # Add the label to the new FloatLayout
                    float_layout.add_widget(label)








                    # Draw the label on the canvas with a colored rectangle





                    # Draw the label on the canvas
            print(f"the draw:{listY}")


            # Create a list of points by interleaving x and y coordinates
            points = []
            for x, y in zip(listX, listY):
                points.extend([
                    self.ids.temp_layout.x + position_offset[0] + self.ids.temp_layout.width * (x / max(listX)) * (0.925)-40, #changes!
                    self.ids.temp_layout.y + position_offset[1] + self.ids.temp_layout.height * (y / max(listY)) * 0.7
                ])
            for x, y in zip(listX, listY):
                x_pos = self.ids.temp_layout.x + position_offset[0] + self.ids.temp_layout.width * (x / max(listX)) * (
                    0.925)
                y_pos = self.ids.temp_layout.y + position_offset[1] + self.ids.temp_layout.height * (
                            y / max(listY)) * 0.7



            self.line_color = Color(0, 0, 1)
            self.line = Line(
                points=points,
                width=5  # Set line width (adjust as needed)
            )
            print(drawY)

            try:
                if drawY[0] is None:
                    drawY[0] = 0
                    self.draw_rectangle(0)
                for i in range(1, 24):
                    if drawY[i] is None:
                        self.draw_rectangle(i)
            except:
                print("No Database!")



            # Bind line points to update dynamically when the layout size changes


    def draw_rectangle(self, listypos):
        x1 = 0.09
        x2 = 0.0352
        resize_factor = x1  # per hour 0.037
        height_factor = 0.7
        heightposition_factor = 0.84
        position_factor = 0.84 - (2 * (listypos * x2))  # hour position

        Color(0, 0, 0, 1)  # Set color to blue with alpha (RGB values + alpha)
        self.rectangle = Rectangle(
            pos=(self.ids.temp_layout.x + (self.ids.temp_layout.width * (1 - position_factor)) / 2 -55,
                 self.ids.temp_layout.y + (self.ids.temp_layout.height * ((1 - heightposition_factor)) / 0.63)),
            size=(self.ids.temp_layout.width * resize_factor, self.ids.temp_layout.height * height_factor+10))





    def show_flow(self, instance):

        self.ids.flow_layout.clear_widgets()
        global flow_active, n, interval_time, flow_sum
        drawY = []


        # Add a blue rectangle to the canvas
        image = Image(source='graph1-background.png', width=self.ids.flow_layout.width, size_hint_x=1)

        # Add the Image widget to the BoxLayout
        self.ids.flow_layout.add_widget(image)

        with self.ids.flow_layout.canvas:

            # Calculate line coordinates based on listX and listY
            listX = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
            listY = list(flow_active.values())
            print(f"the y values: {listY} and lenY {len(listY)} and lenX {len(listX)}")
            #listY = [max(0, x) for x in listY]


            drawY = copy.copy(listY)
            print(f'the drawY: {drawY}')
            min_value = min(filter(lambda x: x is not None and x != 0, listY), default=None)

            # Replace every None or 0 with the minimum value
            listY = [min_value if x is None or x == 0 else x for x in listY]
            print(f"every listY{listY}")


            # Replace None values with 0
            for i in range(1, len(listY)):
                if listY[i] is None:
                    listY[i] = listY[i - 1]
            print(f"after convert{listY}")



            position_offset = (self.ids.flow_layout.width * (0.038), self.ids.flow_layout.height * 0.25)

            try:
                full = round(max(listY), 1)
                quarter = round(max(listY) / 4, 1)
                half = round(max(listY) / 2, 1)
                quarter2 = round(max(listY)*3/4, 1)
                zero = 0
            except:
                full = 4
                quarter = 1
                half = 2
                quarter2 = 3
                zero = 0
            line_listY = [zero, quarter, half, quarter2, full]

            listY = [round(item, 1) for item in listY]

            for y in line_listY:
                if y is not None:
                    line_color = Color(1, 1, 1, 1)  # Red line, fully opaque
                    line_position_x = self.ids.flow_layout.x + position_offset[0] + self.ids.flow_layout.width * (1 / max(listX)) * (0.5)
                    line_position_y = (self.ids.flow_layout.y + position_offset[1] +
                                       self.ids.flow_layout.height * (y / max(line_listY)) * 0.7)
                    line_length = self.ids.flow_layout.width * 0.9  # Adjust the length as needed
                    line_points = [line_position_x, line_position_y,
                                   line_position_x + line_length, line_position_y]
                    Line(points=line_points, width=1, color=line_color)

            ################################
            flow_layout = self.ids.flow_layout

            # Create a new FloatLayout for floating labels
            float_layout = FloatLayout(size_hint=(None, None))
            flow_layout.add_widget(float_layout)
            for y in line_listY:
                if y is not None:
                    label_color = Color(0, 0, 0, 1)  # Black color, fully opaque
                    label_position_x = flow_layout.x + position_offset[0]
                    label_position_y = (
                            flow_layout.y
                            + position_offset[1]
                            + flow_layout.height * (y / max(line_listY)) * 0.7
                    )

                    label = Label(
                        text=str(y),
                        pos=(label_position_x - 38, label_position_y * 0.985 - 20),  # changes!
                        color=label_color.rgb,
                        font_size=sp(10),
                    )

                    # Add the label to the new FloatLayout
                    float_layout.add_widget(label)



                    # Draw the label on the canvas with a colored rectangle





                    # Draw the label on the canvas
            print(f"the draw:{listY}")


            # Create a list of points by interleaving x and y coordinates
            points = []
            for x, y in zip(listX, listY):
                points.extend([
                    self.ids.flow_layout.x + position_offset[0] + self.ids.flow_layout.width * (x / max(listX)) * (0.925)-40,
                    self.ids.flow_layout.y + position_offset[1] + self.ids.flow_layout.height * (y / max(listY)) * 0.7
                ])
            for x, y in zip(listX, listY):
                x_pos = self.ids.flow_layout.x + position_offset[0] + self.ids.flow_layout.width * (x / max(listX)) * (
                    0.925)
                y_pos = self.ids.flow_layout.y + position_offset[1] + self.ids.flow_layout.height * (
                            y / max(listY)) * 0.7



            self.line_color = Color(0, 0, 1)
            self.line = Line(
                points=points,
                width=5  # Set line width (adjust as needed)
            )
            print(drawY)

            try:
                if drawY[0] is None:
                    drawY[0] = 0
                    self.draw_rectangle1(0)
                for i in range(1, 24):
                    if drawY[i] is None:
                        self.draw_rectangle1(i)
            except:
                print("No Database!")



            # Bind line points to update dynamically when the layout size changes


    def draw_rectangle1(self, listypos):
        x1 = 0.09
        x2 = 0.0352
        resize_factor = x1  # per hour 0.037
        height_factor = 0.7
        heightposition_factor = 0.84
        position_factor = 0.84 - (2 * (listypos * x2))  # hour position

        Color(0, 0, 0, 1)  # Set color to blue with alpha (RGB values + alpha)
        self.rectangle = Rectangle(
            pos=(self.ids.flow_layout.x + (self.ids.flow_layout.width * (1 - position_factor)) / 2 -55,
                 self.ids.flow_layout.y + (self.ids.flow_layout.height * ((1 - heightposition_factor)) / 0.63)),
            size=(self.ids.flow_layout.width * resize_factor, self.ids.flow_layout.height * height_factor+10))




    def show_pressure(self, instance):

        self.ids.pressure_layout.clear_widgets()
        global pressure_active, n, interval_time, pressure_sum
        drawY = []


        # Add a blue rectangle to the canvas
        image = Image(source='graph2-background.png', width=self.ids.pressure_layout.width, size_hint_x=1)

        # Add the Image widget to the BoxLayout
        self.ids.pressure_layout.add_widget(image)

        with self.ids.pressure_layout.canvas:

            # Calculate line coordinates based on listX and listY
            listX = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
            listY = list(pressure_active.values())
            print(f"the y values: {listY} and lenY {len(listY)} and lenX {len(listX)}")



            drawY = copy.copy(listY)
            print(f'the drawY: {drawY}')
            min_value = min(filter(lambda x: x is not None and x != 0, listY), default=None)

            # Replace every None or 0 with the minimum value
            listY = [min_value if x is None or x == 0 else x for x in listY]
            print(f"every listY{listY}")


            # Replace None values with 0
            for i in range(1, len(listY)):
                if listY[i] is None:
                    listY[i] = listY[i - 1]
            print(f"after convert{listY}")



            position_offset = (self.ids.pressure_layout.width * (0.038), self.ids.pressure_layout.height * 0.25)

            try:
                full = round(max(listY), 1)
                quarter = round(max(listY) / 4, 1)
                half = round(max(listY) / 2, 1)
                quarter2 = round(max(listY)*3/4, 1)
                zero = 0
            except:
                full = 4
                quarter = 1
                half = 2
                quarter2 = 3
                zero = 0
            line_listY = [zero, quarter, half, quarter2, full]

            listY = [round(item, 1) for item in listY]


            for y in line_listY:
                if y is not None:
                    line_color = Color(1, 1, 1, 1)  # Red line, fully opaque
                    line_position_x = self.ids.pressure_layout.x + position_offset[0] + self.ids.pressure_layout.width * (1 / max(listX)) * (0.5)
                    line_position_y = (self.ids.pressure_layout.y + position_offset[1] +
                                       self.ids.pressure_layout.height * (y / max(line_listY)) * 0.7)
                    line_length = self.ids.pressure_layout.width * 0.9  # Adjust the length as needed
                    line_points = [line_position_x, line_position_y,
                                   line_position_x + line_length, line_position_y]
                    Line(points=line_points, width=1, color=line_color)

            ################################
            pressure_layout = self.ids.pressure_layout

            # Create a new FloatLayout for floating labels
            float_layout = FloatLayout(size_hint=(None, None))
            pressure_layout.add_widget(float_layout)
            for y in line_listY:
                if y is not None:
                    label_color = Color(0, 0, 0, 1)  # Black color, fully opaque
                    label_position_x = pressure_layout.x + position_offset[0]
                    label_position_y = (
                            pressure_layout.y
                            + position_offset[1]
                            + pressure_layout.height * (y / max(line_listY)) * 0.7
                    )

                    label = Label(
                        text=str(y),
                        pos=(label_position_x - 38, label_position_y * 0.985 - 25),  # changes!
                        color=label_color.rgb,
                        font_size=sp(10),
                    )

                    # Add the label to the new FloatLayout
                    float_layout.add_widget(label)

                    # Draw the label on the canvas with a colored rectangle





                    # Draw the label on the canvas
            print(f"the draw:{listY}")


            # Create a list of points by interleaving x and y coordinates
            points = []
            for x, y in zip(listX, listY):
                points.extend([
                    self.ids.pressure_layout.x + position_offset[0] + self.ids.pressure_layout.width * (x / max(listX)) * (0.925)-40,
                    self.ids.pressure_layout.y + position_offset[1] + self.ids.pressure_layout.height * (y / max(listY)) * 0.7
                ])
            for x, y in zip(listX, listY):
                x_pos = self.ids.pressure_layout.x + position_offset[0] + self.ids.pressure_layout.width * (x / max(listX)) * (
                    0.925)
                y_pos = self.ids.pressure_layout.y + position_offset[1] + self.ids.pressure_layout.height * (
                            y / max(listY)) * 0.7



            self.line_color = Color(0, 0, 1)
            self.line = Line(
                points=points,
                width=5  # Set line width (adjust as needed)
            )
            print(drawY)

            try:
                if drawY[0] is None:
                    drawY[0] = 0
                    self.draw_rectangle2(0)
                for i in range(1, 24):
                    if drawY[i] is None:
                        self.draw_rectangle2(i)
            except:
                print("No Database!")



            # Bind line points to update dynamically when the layout size changes


    def draw_rectangle2(self, listypos):
        x1 = 0.09
        x2 = 0.0352
        resize_factor = x1  # per hour 0.037
        height_factor = 0.7
        heightposition_factor = 0.84
        position_factor = 0.84 - (2 * (listypos * x2))  # hour position

        Color(0, 0, 0, 1)  # Set color to blue with alpha (RGB values + alpha)
        self.rectangle = Rectangle(
            pos=(self.ids.pressure_layout.x + (self.ids.pressure_layout.width * (1 - position_factor)) / 2 -55,
                 self.ids.pressure_layout.y + (self.ids.pressure_layout.height * ((1 - heightposition_factor)) / 0.63)),
            size=(self.ids.pressure_layout.width * resize_factor, self.ids.pressure_layout.height * height_factor+10))


    def show_batt(self, instance):

        self.ids.batt_layout.clear_widgets()

        global batt_active, n, interval_time, batt_sum
        drawY = []


        # Add a blue rectangle to the canvas
        image = Image(source='graph3-background.png', width=self.ids.batt_layout.width, size_hint_x=1)

        # Add the Image widget to the BoxLayout
        self.ids.batt_layout.add_widget(image)

        with self.ids.batt_layout.canvas:

            # Calculate line coordinates based on listX and listY
            listX = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
            listY = list(batt_active.values())
            print(f"the y values: {listY} and lenY {len(listY)} and lenX {len(listX)}")



            drawY = copy.copy(listY)
            print(f'the drawY: {drawY}')
            min_value = min(filter(lambda x: x is not None and x != 0, listY), default=None)

            # Replace every None or 0 with the minimum value
            listY = [min_value if x is None or x == 0 else x for x in listY] #! changes
            print(f"every listY{listY}")


            # Replace None values with 0
            for i in range(1, len(listY)):
                if listY[i] is None:
                    listY[i] = listY[i - 1]
            print(f"after convert{listY}")



            position_offset = (self.ids.batt_layout.width * (0.038), self.ids.batt_layout.height * 0.25)

            try:
                full = round(max(listY), 1)
                quarter = round(max(listY) / 4, 1)
                half = round(max(listY) / 2, 1)
                quarter2 = round(max(listY)*3/4, 1)
                zero = 0
            except:
                full = 4
                quarter = 1
                half = 2
                quarter2 = 3
                zero = 0
            line_listY = [int(zero), int(quarter), int(half), int(quarter2), int(full)]

            listY = [round(item, 1) for item in listY]

            for y in line_listY:
                if y is not None:
                    line_color = Color(1, 1, 1, 1)  # Red line, fully opaque
                    line_position_x = self.ids.batt_layout.x + position_offset[0] + self.ids.batt_layout.width * (1 / max(listX)) * (0.5)
                    line_position_y = (self.ids.batt_layout.y + position_offset[1] +
                                       self.ids.batt_layout.height * (y / max(line_listY)) * 0.7)
                    line_length = self.ids.batt_layout.width * 0.9  # Adjust the length as needed
                    line_points = [line_position_x, line_position_y,
                                   line_position_x + line_length, line_position_y]
                    Line(points=line_points, width=1, color=line_color)

            ################################
            batt_layout = self.ids.batt_layout

            # Create a new FloatLayout for floating labels
            float_layout = FloatLayout(size_hint=(None, None))
            batt_layout.add_widget(float_layout)
            for y in line_listY:
                if y is not None:
                    label_color = Color(0, 0, 0, 1)  # Black color, fully opaque
                    label_position_x = batt_layout.x + position_offset[0]
                    label_position_y = (
                            batt_layout.y
                            + position_offset[1]
                            + batt_layout.height * (y / max(line_listY)) * 0.7
                    )

                    label = Label(
                        text=str(y),
                        pos=(label_position_x - 38, label_position_y * 0.985 - 40),  # changes!
                        color=label_color.rgb,
                        font_size=sp(10),
                    )

                    # Add the label to the new FloatLayout
                    float_layout.add_widget(label)

                    # Draw the label on the canvas with a colored rectangle





                    # Draw the label on the canvas
            print(f"the draw:{listY}")


            # Create a list of points by interleaving x and y coordinates
            points = []
            for x, y in zip(listX, listY):
                points.extend([
                    self.ids.batt_layout.x + position_offset[0] + self.ids.batt_layout.width * (x / max(listX)) * (0.925)-40,
                    self.ids.batt_layout.y + position_offset[1] + self.ids.batt_layout.height * (y / max(listY)) * 0.7
                ])
            for x, y in zip(listX, listY):
                x_pos = self.ids.batt_layout.x + position_offset[0] + self.ids.batt_layout.width * (x / max(listX)) * (
                    0.925)
                y_pos = self.ids.batt_layout.y + position_offset[1] + self.ids.batt_layout.height * (
                            y / max(listY)) * 0.7



            self.line_color = Color(0, 0, 1)
            self.line = Line(
                points=points,
                width=5  # Set line width (adjust as needed)
            )
            print(drawY)

            try:
                if drawY[0] is None:
                    drawY[0] = 0
                    self.draw_rectangle3(0)
                for i in range(1, 24):
                    if drawY[i] is None:
                        self.draw_rectangle3(i)
                print(f"the None in drawy: {drawY}")
            except:
                print("No Database!")



            # Bind line points to update dynamically when the layout size changes

    def draw_rectangle3(self, listypos):
        x1 = 0.09
        x2 = 0.0352
        resize_factor = x1  # per hour 0.037
        height_factor = 0.7
        heightposition_factor = 0.84
        position_factor = 0.84 - (2 * (listypos * x2))  # hour position

        Color(0, 0, 0, 1)  # Set color to blue with alpha (RGB values + alpha)
        self.rectangle = Rectangle(
            pos=(self.ids.batt_layout.x + (self.ids.batt_layout.width * (1 - position_factor)) / 2 -55,
                 self.ids.batt_layout.y + (self.ids.batt_layout.height * ((1 - heightposition_factor)) / 0.63)),
            size=(self.ids.batt_layout.width * resize_factor, self.ids.batt_layout.height * height_factor+10))






#####################################################
    def read_graph(self, instance):
        try:

            content = BoxLayout(orientation='vertical', size_hint=(1, 0.75))

            connection = sqlite3.connect(db_file, isolation_level=None)
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            get_tables = cursor.fetchall()
            table_list = [str(table[0]) for table in get_tables]
            date_info = [(str(name.split('_')[3]), str(name.split('_')[1]), str(name.split('_')[2])) for name in table_list]

            date_dict = {}

            for year, month, day in date_info:
                if year not in date_dict:
                    date_dict[year] = {}
                if month not in date_dict[year]:
                    date_dict[year][month] = set()
                date_dict[year][month].add(day)

            year_list = list(date_dict.keys())
            month_list = []
            day_list = []

            year_spinner = Spinner(text='Select Year', values=year_list, size=(100, 30))
            month_spinner = Spinner(text='Select Month', values=month_list, size=(100, 30))
            day_spinner = Spinner(text='Select Day', values=day_list, size=(100, 30))

            def update_month_spinner(year):
                month_list = list(date_dict.get(year, {}).keys())
                month_spinner.values = month_list
                month_spinner.text = 'Select Month'
                update_day_spinner(year, month_spinner.text)

            def update_day_spinner(year, month):
                global Multiplier_ChooseDate
                day_list = list(date_dict.get(year, {}).get(month, set()))
                day_spinner.values = day_list
                day_spinner.text = 'Select Day'

            year_spinner.bind(text=lambda instance, text: update_month_spinner(text))
            month_spinner.bind(text=lambda instance, text: update_day_spinner(year_spinner.text, text))
            day_spinner.bind(text=self.on_day_select)

            content.add_widget(Label(text="Choose a database:", size_hint_y=0.1))
            table_grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
            table_grid.bind(minimum_height=table_grid.setter('height'))

            row1 = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40, size=(200*Multiplier_ChooseDate,50*Multiplier_ChooseDate))
            row1.add_widget(year_spinner)
            table_grid.add_widget(row1)

            row2 = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40, size=(200*Multiplier_ChooseDate,50*Multiplier_ChooseDate))
            row2.add_widget(month_spinner)
            table_grid.add_widget(row2)

            row3 = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40, size=(200*Multiplier_ChooseDate,50*Multiplier_ChooseDate))
            row3.add_widget(day_spinner)
            table_grid.add_widget(row3)

            scroll_view = ScrollView()
            scroll_view.add_widget(table_grid)

            confirm_button = Button(text='Confirm', size=(100, 30))
            confirm_button.bind(
                on_release=lambda instance: self.on_confirm_button_click(year_spinner.text, month_spinner.text,
                                                                         day_spinner.text))

            row4 = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40, size=(200*Multiplier_ChooseDate,50*Multiplier_ChooseDate))
            row4.add_widget(confirm_button)
            table_grid.add_widget(row4)
            content.add_widget(scroll_view)

            self.popup = Popup(
                title="Choose a Date",
                title_align='center',
                content=content,
                size_hint=(None, None),
                size=(400*Multiplier_ChooseDate, 500*Multiplier_ChooseDate),
                background_color=(0.5, 0.5, 0.8, 0.7),
            )

            self.popup.open()
            connection.close() #temporary added.
        except:
            content = BoxLayout(orientation='vertical')
            label = Label(text="")
            close_button = Button(text="Close", background_color=(0.5, 0, 0, 0.7))
            content.add_widget(label)
            content.add_widget(close_button)

            success_popup = Popup(title="Reading Data Complete",
                                  content=content,
                                  size_hint=(None, None), size=(300 * Multiplier_Delete, 200 * Multiplier_Delete),
                                  auto_dismiss=True,
                                  background_color=(0.5, 0.5, 0.8, 0.7))

            close_button.bind(on_release=success_popup.dismiss)
            success_popup.open()

    def on_month_select(self, instance, text):
        print("Selected Month:", text)

    def on_day_select(self, instance, text):
        print("Selected Day:", text)

    def on_confirm_button_click(self, year, month, day):
        global Multiplier_ChooseDate
        try:
            if year == 'Select Year' or month == 'Select Month' or day == 'Select Day':
                self.selected_table == None
                self.popup = Popup(
                    title="Date Selection Error",
                    title_align='center',
                    size_hint=(None, None),
                    size=(300*Multiplier_ChooseDate, 200*Multiplier_ChooseDate),
                    background_color=(0.5, 0.5, 0.5, 0.7),
                    separator_color=(1, 1, 1, 0)
                )
                content_layout = BoxLayout(orientation='vertical')
                error_label = Label(text="     Invalid date.\nPlease try again.", size_hint=(1, 1))

                # Create dismiss button
                dismiss_button = Button(text='Close', size_hint=(0.5, 0.4),background_color=(1, 0.5, 0.5, 0.7),  pos_hint={'center_x': 0.5, 'center_y': 0.5}, size=(100*Multiplier_ChooseDate, 50*Multiplier_ChooseDate))
                dismiss_button.bind(on_press=self.popup.dismiss)

                # Add widgets to content layout
                content_layout.add_widget(error_label)
                content_layout.add_widget(dismiss_button)

                # Set content layout for the Popup
                self.popup.content = content_layout

                # Open the Popup
                self.popup.open()
            else:
                self.selected_table = f'{month}_{day}_{year}'.replace("_", " ")
                print("Selected Table:", self.selected_table)
                self.popup.dismiss()

                connection = sqlite3.connect(db_file, isolation_level=None)
                cursor = connection.cursor()
                data = f'Data_{month}_{day}_{year}'
                query = f"SELECT * FROM {data}"
                cursor.execute(query)
                results = cursor.fetchall()
                for row in results:
                    current_time, id, temp, flow, pressure, batt = row
                    temp_dict[current_time] = temp
                    flow_dict[current_time] = flow
                    pressure_dict[current_time] = pressure
                    batt_dict[current_time] = batt

                print(f'the table: {self.selected_table}')


                interval_start = datetime.datetime(1, 1, 1, 0, 0, 0)
                original_interval_end = datetime.datetime(1, 1, 1, 23, 59, 59)
                second_step = 10
                time_step = datetime.timedelta(seconds=second_step)

                end_intervals = []

                while interval_start <= original_interval_end:
                    interval_end = interval_start + time_step
                    interval_end_formatted = interval_end.strftime("%H:%M:%S")
                    end_intervals.append(interval_end_formatted)
                    interval_start = interval_end

                cursor.execute(f"SELECT time FROM {data}")
                res = cursor.fetchall()

                time_with_id = [(interval, i * second_step + second_step) for i, interval in enumerate(end_intervals)]

                # Convert the result to datetime objects
                res = [datetime.datetime.strptime(item[0], "%H:%M:%S") for item in res]

                # Now you can format the datetime objects
                formatted_res = [item.strftime("%H:%M:%S") for item in res]

                # Check which intervals are missing in the database
                missing_intervals = [interval for interval in end_intervals if interval not in formatted_res]

                # Set the missing intervals to None in the database
                for item in time_with_id:
                    if item[0] in missing_intervals:
                        cursor.execute(
                            f"INSERT INTO {data} (id, time, temperature, flow, pressure, battery) VALUES (?, ?, ?, ?, ?, ?)",
                            (item[1], item[0], None, None, None, None)
                        )
                connection.commit()

                # Create a temporary table, drop the original, and rename the temporary table
                cursor.execute(f"CREATE TABLE temp_table AS SELECT * FROM {data} ORDER BY id ASC")
                cursor.execute(f"DROP TABLE {data}")
                cursor.execute(f"ALTER TABLE temp_table RENAME TO {data}")

                # Remove duplicate entries with NULL values in time, temperature, flow, pressure, and battery
                cursor.execute(f'''
                    DELETE FROM {data}
                    WHERE (time, temperature, flow, pressure, battery) IN (
                        SELECT time, temperature, flow, pressure, battery
                        FROM {data}
                        WHERE time IS NOT NULL
                        GROUP BY time, temperature, flow, pressure, battery
                        HAVING COUNT(*) > 1
                    ) 
                    AND temperature IS NULL
                    AND flow IS NULL
                    AND pressure IS NULL
                    AND battery IS NULL;
                ''')
                new_temperature = None
                new_flow = None
                new_pressure = None
                new_battery = None

                # Use an SQL query to update the rows with id = 5 and id = 86395
                update_query = f'''UPDATE {data}
                                  SET temperature = ?,
                                      flow = ?,
                                      pressure = ?,
                                      battery = ?
                                  WHERE id IN (?, ?)'''

                # Execute the query with the data
                cursor.execute(update_query, (new_temperature, new_flow, new_pressure, new_battery, 5, 10))
                cursor.execute(update_query, (new_temperature, new_flow, new_pressure, new_battery, 5, 86390))

                connection.commit()
                connection.close()
        except:
            content = BoxLayout(orientation='vertical')
            label = Label(text="")
            close_button = Button(text="Close", background_color=(0.5, 0, 0, 0.7))
            content.add_widget(label)
            content.add_widget(close_button)

            success_popup = Popup(title="Reading Data Complete",
                                  content=content,
                                  size_hint=(None, None), size=(300 * Multiplier_Delete, 200 * Multiplier_Delete),
                                  auto_dismiss=True,
                                  background_color=(0.5, 0.5, 0.8, 0.7))

            close_button.bind(on_release=success_popup.dismiss)
            success_popup.open()


    ########
    '''def on_table_select(self, table_name):
        # Handle the selected table here
        print("Selected table:", table_name)
        self.selected_table = table_name
        self.popup.dismiss()'''

    #####################################################

    def write_popup(self, instance):
        # Create the layout for the popup
        layout = BoxLayout(orientation='vertical', padding=10)

        # Create the GridLayout for messages
        messages_layout = GridLayout(cols=2, rows=2, spacing=10, size_hint_y=0.5)
        messages_layout.bind(minimum_height=messages_layout.setter('height'))

        # Add messages to the GridLayout
        messages_layout.add_widget(Label(text='Do you want to show graph?'))


        # Add the GridLayout to the main layout
        layout.add_widget(messages_layout)

        # Create a horizontal BoxLayout for buttons
        buttons_layout = BoxLayout(size_hint_y=0.3, height=50, spacing=10)

        # Add buttons to the buttons_layout
        buttons_layout.add_widget(
            Button(text='Confirm', on_press=self.active_graph, size_hint=(1, None), size=(120*Multiplier_Confirmation, 50*Multiplier_Confirmation), background_color=(0, 0.5, 0, 0.7)))
        buttons_layout.add_widget(
            Button(text='Cancel', on_press=self.on_cancel_write, size_hint=(1, None), size=(120*Multiplier_Confirmation, 50*Multiplier_Confirmation),background_color=(0.5, 0, 0, 0.7)))

        # Add the buttons_layout to the main layout
        layout.add_widget(buttons_layout)

        # Create the popup and set its content
        popup = Popup(title='Confirmation', content=layout, size_hint=(None, None), size=(300*Multiplier_Confirmation, 200*Multiplier_Confirmation),background_color=(0.5, 0.5, 0.8, 0.7))

        # Open the popup
        popup.open()



    def on_cancel_write(self, instance):
        # Dismiss the popup when the "Cancel" button is pressed
        instance.parent.parent.parent.parent.parent.dismiss()

    def open_reset_popup(self, instance):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text="Select Action for Database Deletion"))

        reset_button = Button(text=f"Delete: {self.selected_table}", size_hint=(1, 1),
                              size=(120 * Multiplier_Delete, 50 * Multiplier_Delete),
                              background_color=(0.5, 0, 0, 0.7),
                              pos_hint={'center_x': 0.5, 'center_y': 0.5})
        reset_button.bind(on_release=self.confirmation2) #self.delete_data

        cancel_button = Button(text="Delete All Data", size_hint=(1, 1),
                               size=(120 * Multiplier_Delete, 50 * Multiplier_Delete),
                               background_color=(0.5, 0, 0, 0.7),
                               pos_hint={'center_x': 0.5, 'center_y': 0.5})
        cancel_button.bind(on_release=self.confirmation)

        cancel_button2 = Button(text="Cancel", size_hint=(1, 1),
                                size=(120 * Multiplier_Delete, 50 * Multiplier_Delete),
                                background_color=(0.5, 0.5, 0.5, 0.8),
                                pos_hint={'center_x': 0.5, 'center_y': 0.5})
        cancel_button2.bind(on_release=self.on_cancel_button)

        button_layout = BoxLayout(orientation='vertical')
        button_layout.add_widget(reset_button)
        button_layout.add_widget(cancel_button)
        button_layout.add_widget(cancel_button2)
        content.add_widget(button_layout)

        self.main_popup = Popup(title='Database Deletion', content=content, size_hint=(None, None),
                                size=(300 * Multiplier_Delete, 200 * Multiplier_Delete),
                                background_color=(0.5, 0.5, 0.8, 0.7))
        self.main_popup.open()

    def on_reset_button(self, instance):
        global db_file
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"{db_file} has been deleted!.")
            self.show_success_popup()
        else:
            print(f"{db_file} does not exist, so create a new one!.")
            self.show_no_db_popup()

    def show_success_popup(self):
        content = BoxLayout(orientation='vertical')
        label = Label(text="A new database has been created.")
        close_button = Button(text="Close", background_color=(0.5, 0, 0, 0.7))
        content.add_widget(label)
        content.add_widget(close_button)

        success_popup = Popup(title="Deletion Successful",
                              content=content,
                              size_hint=(None, None), size=(300 * Multiplier_Delete, 200 * Multiplier_Delete),
                              auto_dismiss=True,
                              background_color=(0.5, 0.5, 0.8, 0.7))

        close_button.bind(on_release=success_popup.dismiss)
        success_popup.open()

    def show_no_db_popup(self):
        content = BoxLayout(orientation='vertical')
        label = Label(text="Resetting a New Database")
        close_button = Button(text="Close", background_color=(0.5, 0, 0, 0.7))
        content.add_widget(label)
        content.add_widget(close_button)

        no_db_popup = Popup(title="No Database Found",
                            content=content,
                            size_hint=(None, None), size=(300 * Multiplier_Delete, 200 * Multiplier_Delete),
                            auto_dismiss=True,
                            background_color=(0.5, 0.5, 0.8, 0.7))

        close_button.bind(on_release=no_db_popup.dismiss)
        no_db_popup.open()

    def confirmation(self, instance):


        cancel_button3 = Button(text="Cancel", size_hint=(1, None),
                                size=(120 * Multiplier_Delete, 50 * Multiplier_Delete),
                                background_color=(0.5, 0, 0, 0.7),
                                pos_hint={'center_x': 0.5, 'center_y': 0.5})
        cancel_button3.bind(on_release=self.confirmation_exit)

        okay_button = Button(text="Confirm", size_hint=(1, None),
                             size=(120 * Multiplier_Delete, 50 * Multiplier_Delete),
                             background_color=(0, 0.5, 0, 0.7),
                             pos_hint={'center_x': 0.5, 'center_y': 0.5})
        okay_button.bind(on_release=self.on_reset_button)

        confirm_layout = BoxLayout(orientation='horizontal')

        confirm_layout.add_widget(okay_button)
        confirm_layout.add_widget(cancel_button3)

        content = BoxLayout(orientation='vertical')
        content.add_widget(confirm_layout)

        self.confirmation_popup = Popup(title='Do you want to delete all database!', content=content, size_hint=(None, None),
                                        size=(300 * Multiplier_Delete, 200 * Multiplier_Delete),
                                        background_color=(0.5, 0.5, 0.8, 0.7))
        self.confirmation_popup.open()


    def confirmation2(self, instance):

        cancel_button3 = Button(text="Cancel", size_hint=(1, None),
                                size=(120 * Multiplier_Delete, 50 * Multiplier_Delete),
                                background_color=(0.5, 0, 0, 0.7),
                                pos_hint={'center_x': 0.5, 'center_y': 0.5})
        cancel_button3.bind(on_release=self.confirmation_exit)

        okay_button = Button(text="Confirm", size_hint=(1, None),
                             size=(120 * Multiplier_Delete, 50 * Multiplier_Delete),
                             background_color=(0, 0.5, 0, 0.7),
                             pos_hint={'center_x': 0.5, 'center_y': 0.5})
        okay_button.bind(on_release=self.delete_data)

        confirm_layout = BoxLayout(orientation='horizontal')

        confirm_layout.add_widget(okay_button)
        confirm_layout.add_widget(cancel_button3)

        content = BoxLayout(orientation='vertical')
        content.add_widget(confirm_layout)

        self.confirmation_popup = Popup(title=f'Do you want to delete: {self.selected_table}', content=content,
                                        size_hint=(None, None),
                                        size=(300 * Multiplier_Delete, 200 * Multiplier_Delete),
                                        background_color=(0.5, 0.5, 0.8, 0.7))
        if self.selected_table:
            self.confirmation_popup.open()
    def delete_data(self, instance):
        try:
            print(self.selected_table)
            if self.selected_table != 'None':
                # Connect to the SQLite database
                conn = sqlite3.connect(db_file, isolation_level=None)
                cursor = conn.cursor()

                # Example: Deleting all records from a table
                # Construct the DELETE query without specific conditions

                delete_query = f"DROP TABLE IF EXISTS Data_{self.selected_table.replace(' ', '_')};"

                # Execute the query
                cursor.execute(delete_query)

                # Commit the changes to the database
                conn.commit()

                # Close the cursor and connection
                cursor.close()
                conn.close()

                content = Button(text=f'{self.selected_table} Successfully Deleted!')
                popup = Popup(title='Deletion Success', content=content, size_hint=(None, None), size=(300*2.75, 200*2.75))
                content.bind(on_press=popup.dismiss)
                popup.open()
        except:
            print("Data does not exist!")








    def on_cancel_button(self, instance):
        self.main_popup.dismiss()
    def confirmation_exit(self, instance):
        self.confirmation_popup.dismiss()






class WindowManager(ScreenManager): #handle transition
    pass


class ErrorPopup(Popup):
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.title = "Error"
        self.size_hint = (0.7, 0.3)  # Adjust these values as needed

        # Create a box layout for the popup content
        content_layout = BoxLayout(orientation='vertical')

        # Create a horizontal box layout for the close button
        close_layout = BoxLayout(orientation='horizontal', size_hint=(None, None), size=(150, 50))

        # Add the close button to the close_layout
        close_button = Button(
            text='Close',
            size_hint=(None, None),
            size=(150, 50),
            background_color=(1, 0, 0, 1),  # Red background color (RGBA)
            color=(1, 1, 1, 1)  # White text color (RGBA)
        )
        close_button.bind(on_release=self.dismiss)
        close_layout.add_widget(close_button)

        # Add the message label to the content layout
        content_layout.add_widget(Label(text=message))

        # Add the close_layout to the content layout and center it
        content_layout.add_widget(close_layout)
        content_layout.bind(minimum_height=content_layout.setter('height'))

        # Set the content of the popup to the content layout
        self.content = content_layout

        # Position close_layout at the bottom center of the popup
        close_layout.pos_hint = {'center_x': 0.5, 'y': 0}

####################################################################





class MonitoringApp(App):

    def build(self):


        return Builder.load_file("monitoring.kv")

    def exit_app(self):
        App.get_running_app().stop()

if __name__ == "__main__":
    MonitoringApp().run()
