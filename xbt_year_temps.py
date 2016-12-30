# -*- coding: utf-8 -*-

import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata


def in_circle(center_x, center_y, radius, x, y):
    square_dist = (center_x - x) ** 2 + (center_y - y) ** 2
    return square_dist <= radius ** 2


def progress(count, total, suffix=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
    sys.stdout.flush()

Latitude = 0
Longitude = 0

Year = []
Month = 0
Day = 0
depth_range = range(0, 2500, 5)

location = {'Bismark': [-64.866794, -63.650144]}

# Each degree of latitude is approximately 69 miles (111 kilometers) apart.
radius = 1.5
location_name = "Bismark"
print "Distance around", location_name, "(", location[location_name], "):", radius * 111.045, "km"

count_data_sets = 0
# main dictionary for whole dataset
data_dic = {}
##########################################################################
# Main data extraction function


def extract_temp_depth_data(file_in, location, radius):
    print "Working on:", file_in
    print ""

    total_line = sum(1 for line in open(file_in, "r"))
    count = 0
    depth_temp = {}
    for line in open(file_in, "r"):
        progress(count, total_line, suffix='')
        count += 1
        line = line.strip('\n')
        line = line.replace(' ', '')
        line = line.split(',')

        if line[0] == 'Latitude':
            global Latitude
            Latitude = line[2]
            continue

        elif line[0] == 'Longitude':
            global Longitude
            Longitude = line[2]
            continue

        elif line[0] == 'Year':
            global Year
            Year = line[2]
            continue

        elif line[0] == 'Month':
            global Month
            Month = line[2]
            continue

        elif line[0] == 'Day':
            global Day
            Day = line[2]
            continue

        elif line[1][0:-1].isdigit():
            # print line[1]
            if int(line[1][0:-1]) in depth_range:
                # print line[4]
                try:
                    depth_temp[int(line[1][0:-1])] = float(line[4])
                    continue
                except ValueError:
                    continue

        elif line[0] == 'ENDOFVARIABLESSECTION':
            # print Latitude, Longitude, Month, depth_temp
            # print depth_temp.items()
            if in_circle(float(location[location_name][0]), float(location[location_name][1]), float(radius), float(Latitude), float(Longitude)):
                for depth_key in depth_temp.keys():
                    global data_dic
                    data_dic[Month] = data_dic.get(Month, {})
                    data_dic[Month][depth_key] = data_dic[Month].get(
                        depth_key, [])
                    data_dic[Month][depth_key].append(depth_temp[depth_key])

                # clear out for next vals
                Latitude = 0
                Longitude = 0
                Month = 0
                Day = 0
                depth_temp = {}
                global count_data_sets
                count_data_sets += 1
                continue
            else:
                # clear out for next vals if values not in r radius around catch
                # sites
                Latitude = 0
                Longitude = 0
                Month = 0
                Day = 0
                depth_temp = {}
                continue
##########################################################################
# Xbt data
file_in_1 = "./WOD.27428.XBT.csv"
extract_temp_depth_data(file_in_1, location, radius)
print ""

# CTD data
file_in_2 = "./WOD.27428.CTD.csv"
extract_temp_depth_data(file_in_2, location, radius)
print ""
print "Data set spans from  year ", min(Year), "to", max(Year)
print "Months covered with data:"
for i in sorted(data_dic.keys()):
    print i
print ""
print "Number of xbt casts used:", count_data_sets


def make_grid_graph(data_dictionary, stat, location_name, radius):
    # Convert from pandas dataframes to numpy arrays
    X, Y, Z = np.array([]), np.array([]), np.array([])

    if stat == "count":
        for month_key in sorted(data_dictionary.keys()):
            for depth_key in sorted(data_dictionary[month_key].keys()):
                X = np.append(X, int(month_key))
                Y = np.append(Y, int(depth_key))
                Z = np.append(Z, len(data_dictionary[month_key][depth_key]))

        # create x-y points to be used in heatmap
        xi = np.linspace(X.min(), X.max() + 1, 100)
        yi = np.linspace(Y.min(), Y.max(), 100)

        # Z is a matrix of x-y values
        zi = griddata((X, Y), Z, (xi[None, :], yi[:, None]), method='cubic')

        # I control the range of my colorbar by removing data
        # outside of my range of interest
        zmin = 0
        # zmax = 10000
        # zi[(zi < zmin) | (zi > zmax)] = None

        # Create the contour plot
        CS = plt.contourf(xi, yi, zi, 15, cmap='plasma')
        # vmax=zmax, vmin=zmin)

        ax = plt.gca()
        plt.xticks(np.arange(0, 12 + 1, 1.0))

        zc = CS.collections[6]
        plt.setp(zc, linewidth=4)
        ax.invert_yaxis()
        ax.grid(True)
        ax.set_xlabel('Month')
        ax.set_ylabel('Depth (m)')
        ax.set_title("Monthly Temperature vs Depth \n Location: %s (%s) with radius: %s" % (
            location_name, location[location_name], radius))
        cb = plt.colorbar()
        cb.set_label("Temperature (C)")

    else:
        for month_key in sorted(data_dictionary.keys()):
            for depth_key in sorted(data_dictionary[month_key].keys()):
                X = np.append(X, int(month_key))
                Y = np.append(Y, int(depth_key))
                Z = np.append(Z, np.average(
                    data_dictionary[month_key][depth_key]))
        # create x-y points to be used in heatmap
        xi = np.linspace(X.min(), X.max() + 1, 100)
        yi = np.linspace(Y.min(), Y.max(), 100)

        # Z is a matrix of x-y values
        zi = griddata((X, Y), Z, (xi[None, :], yi[:, None]), method='cubic')

        # I control the range of my colorbar by removing data
        # outside of my range of interest
        zmin = -3
        zmax = 3
        zi[(zi < zmin) | (zi > zmax)] = None

        # Create the contour plot
        CS = plt.contourf(xi, yi, zi, 15, cmap='bwr',
                          vmax=zmax, vmin=zmin)

        ax = plt.gca()
        plt.xticks(np.arange(0, 12 + 1, 1.0))

        zc = CS.collections[6]
        plt.setp(zc, linewidth=4)
        ax.invert_yaxis()
        ax.grid(True)
        ax.set_xlabel('Month')
        ax.set_ylabel('Depth (m)')
        ax.set_title("Monthly Temperature vs Depth \n Location: %s (%s) with radius: %s" % (
            location_name, location[location_name], radius))
        cb = plt.colorbar()
        cb.set_label("Temperature (C)")

    output_dir = "./"
    plt.savefig(output_dir +
                "Monthly_Temp_v_Depth_%s_radius_%s__stat_%s_km.png" % (location_name, stat, radius * 111.045))
    plt.close()

make_grid_graph(data_dic, "stat", location_name, 1.5)

make_grid_graph(data_dic, "count", location_name, 1.5)
