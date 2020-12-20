import io
import pandas as pd
from bokeh.models import ColumnDataSource, HoverTool, SaveTool, CDSView, GroupFilter
from bokeh.models.widgets import TextInput, Button
from bokeh.plotting import figure, curdoc
from bokeh.layouts import row, column, layout
from bokeh.io import output_file, show
from bokeh.models.widgets import RadioButtonGroup, CheckboxButtonGroup
from datetime import datetime
import json
import random

####################
# Definitions and constants
####################

meta_values = ["MachineID", "TimeStamp"]
source = ColumnDataSource({'MachineID': [],
        'TimeStamp': [], 
        'sensor': [],
        'value': []})
select_machine = None
select_sensors = None

source_dict ={}
datasource_dict = {}

#Initial values
ROLLOVER = 1000

# Generate data
def getJsonData():
    json_dict ={
    "MachineID": "Machine 1" if random.uniform(0, 1)> 0.5 else "Machine 2", 
    "TimeStamp":datetime.now().timestamp(),
    "OilTemperature":random.randrange(180,230),
    "IntakeTemperature":  True if random.uniform(0, 1)> 0.5 else False,
    "CoolantTemperature": random.randrange(170,220),
    "MegaSensor": random.randrange(170,220),
    "Random1": random.randrange(170,220),
    "Random2": random.randrange(170,220),
    "Random3": random.randrange(170,220),
    "Random4": random.randrange(170,220),
    "BackgroundPressureChamber1": random.randrange(180,230),
    "BackgroundPressureChamber2": random.randrange(170,220),
    "BackgroundPressureChamber3": random.randrange(170,220),
    "ChamberCompressed": True if random.uniform(0, 1)> 0.5 else False,
    "ChamberSeparated": random.randrange(170,220),
    "LoadlockPressure": random.randrange(170,220)
    }
    print(json_dict)
    if json_dict['MachineID'] == "Machine 1":
        json_dict.update({"ChamberRotated": random.randrange(170,220)})
    else:
        json_dict.update({"Flow": random.randrange(170,220)})
    
    # Convert and return JSON
    data_json = json.dumps(json_dict)
    print(data_json)
    return data_json

allowed_variables =[
    "OilTemperature",
    "IntakeTemperature",
    "CoolantTemperature",
    "MegaSensor",
    "ChamberRotated",
    "Flow"
    ] + meta_values

####################
# Setup view
####################


# Setup Machine selector
machine_selector = RadioButtonGroup(
        labels=[], active=None)

# Setup sensor selector
sensor_selector = CheckboxButtonGroup(
        labels=[], active=[])

####################
# Update data
####################

def update_machine():
    # Finds list of machines, creates selctors for all machines
    global machine_list
    machine_list = sorted(datasource_dict.keys())
    machine_selector.labels = machine_list
    return

def update_sensor():
    global select_machine
    sensor_list = sorted(datasource_dict[select_machine].keys())
    sensor_selector.labels = sensor_list
    # Clears select sensors
    sensor_selector.active = []
    return


# Define widget actions
def machine_selector_change(attrname, old, new):
    global machine_list
    global select_machine
    machine_list = None
    update_machine()
    select_machine = machine_list[new]
    # Update sensors
    update_sensor()
    update()
    return


def plot_from_view(sensor_name, CDSdata):
    p = figure(title=sensor_name, x_axis_type='datetime')
    p.line(x='TimeStamp', y='value', source=CDSdata)
    hover = HoverTool(tooltips = [('Time', '@TimeStamp'),
                             ('Value', '@value')])
    p.add_tools(hover)
    return p

def update_plots(select_machine, select_sensors):
    for key,value in datasource_dict[select_machine].items():
        # If key in "added"
        if key in select_sensors:
            p = plot_from_view(key,value)
            plots.children.insert(+1,p)
        


def sensor_selector_change(attrname, old, new):
    del(plots.children[:])
    added = list(set(new)-set(old))
    removed = list(set(old)-set(new))
    select_sensors = [sensor_selector.labels[x] for x in new]
    update_plots(select_machine, select_sensors)
    return

def update():
    machine_value, sensor_value = machine_selector.active, sensor_selector.active
    return

def update_sensor_data(sensor_data):
    this_machine = sensor_data['MachineID']
    # Check if dict containing CDS with sensor data exists
    if this_machine not in datasource_dict.keys():
        datasource_dict[this_machine] = {}
    # Now when machine-dict exists, check if it contains the sensor CDS
    if sensor_data['sensor'] not in datasource_dict[this_machine].keys():
        datasource_dict[this_machine][sensor_data['sensor']] = ColumnDataSource(dict(MachineID=[], TimeStamp=[], sensor=[], value=[]))

    datasource_dict[this_machine][sensor_data['sensor']].stream(dict(
        MachineID=[sensor_data['MachineID']],
        TimeStamp = [sensor_data['TimeStamp']],
        sensor=[sensor_data['sensor']],
        value=[sensor_data['value']]
        )
        ,ROLLOVER)
    return

def update_data():
    jsonData = getJsonData()
    insert_in_buffer(jsonData)
    update_machine()

# Setup widget actions
machine_selector.on_change('active',machine_selector_change)
sensor_selector.on_change('active',sensor_selector_change)


####################
# Receive data
####################

def insert_in_buffer(jsonData):
    print(jsonData)
    data_dict = json.loads(jsonData)
    MachineID = data_dict["MachineID"] 
    del data_dict["MachineID"]
    TimeStamp = data_dict['TimeStamp']
    del data_dict["TimeStamp"]
    for dict_key in data_dict:
        if dict_key in allowed_variables:
            row_key = MachineID + "|" + str(TimeStamp) + "|" + dict_key
            sensor_data = dict(key=row_key,
            MachineID= MachineID, 
            TimeStamp= TimeStamp, 
            sensor = dict_key, 
            value=data_dict[dict_key])
            update_sensor_data(sensor_data)
    return



###################
# Run the dashboard
####################

# initialize
update_machine()

# Setup layout
plots = column()


layout = layout(
        children=[
            [column(machine_selector, sensor_selector, sizing_mode='fixed')], plots
        ],
        sizing_mode='fixed',
    )

curdoc().add_root(layout)
curdoc().title = "Test Dashboard"
curdoc().add_periodic_callback(update_data,50)

