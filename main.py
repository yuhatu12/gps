import matplotlib
matplotlib.use('TkAgg')
import requests
import sys
import time
from io import BytesIO
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from PIL import Image
import pandas as pd
from http.client import IncompleteRead
from flask import Flask, render_template, request
from werkzeug import secure_filename
import os

# constants
# min/max circle size of plot
MIN_SIZE = 20
MAX_SIZE = 200

app = Flask(__name__)

@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/', methods = ['GET', 'POST'])
def upload_file1():
    print("test")
    if request.method == 'POST':

      mapping_gps_data(request.files['file'])
      return render_template('img.html',titlename="helloworld")

# get OpenStreetMap image
def get_osm_img(minlat, minlon, maxlat, maxlon, scale=60000, img_format='png'):
    url = 'http://maps.googleapis.com/maps/api/staticmap?sensor=false&size=400x400&maptype=satellite&visible=%10lf,%10lf&visible=%10lf,%10lf'% (minlon,minlat,maxlon,maxlat)
    payload = {
        'mapnik_format': img_format,
        'mapnik_scale': scale,
        'minlon': minlon,
        'minlat': minlat,
        'maxlon': maxlon,
        'maxlat': maxlat,
        'format': 'mapnik'
    }
    response = requests.post(url)
    return Image.open(BytesIO(response.content))


# load arduino GPS row txt data
# and return formatted data
def load_txt(file):
    col_names = ['c{0:02d}'.format(i) for i in range(50)]
    data = pd.read_csv(file, names=col_names)
    data = data[data.c00 == '$GPGGA']
    data.columns = ['id', 'time', 'longitude', 'NorS', 'latitude', 'EorW'] + col_names[6:]
    # print(data.head(4))
    # print(data.latitude.apply(lambda x: x.split('.')[0][:-2] + '.' + str(float(x.split('.')[0][-2:])/60 + float(x.split('.')[1])/60)).head(5))
    # print(data.latitude.apply(lambda x: x.split('.')[0][:-2]).head(5))
    # print(data.latitude.apply(lambda x: float(x.split('.')[0][:-2]) + float(x.split('.')[0][-2:] + "." + x.split('.')[1])/60).head(5))
    data.latitude = data.latitude.apply(
        lambda x: float(x.split('.')[0][:-2]) + float(x.split('.')[0][-2:] + "." + x.split('.')[1]) / 60)
    # print(data.head(5))
    data.longitude = data.longitude.apply(
        lambda x: float(x.split('.')[0][:-2]) + float(x.split('.')[0][-2:] + "." + x.split('.')[1]) / 60)
    # print(data.head(5))
    data.time = data.time.apply(
        lambda x: float(x))
    # print(min(data.latitude))
    # print(max(data.latitude))
    result = {
        'lat': data.latitude,
        'lon': data.longitude,
        'passenger': data.time
    }
    return result


# main mapping function
def mapping_gps_data(file):
    fig = plt.figure(figsize=(15, 15))
    data = load_txt(file)

    print(min(data['passenger']))
    print(max(data['passenger']))
    print(min(data['lat']))
    print(max(data['lat']))
    print(min(data['lon']))
    print(max(data['lon']))
    cen_lat = (min(data['lat'])+max(data['lat']))/2
    cen_lon = (min(data['lon'])+max(data['lon']))/2
    print(cen_lat)
    print(cen_lon)

    minlat, minlon, maxlat, maxlon = min(data['lon']),min(data['lat']),max(data['lon']),max(data['lat'])
    bmap = Basemap(projection='merc', llcrnrlat=minlat, urcrnrlat=maxlat, llcrnrlon=minlon, urcrnrlon=maxlon, lat_ts=0, resolution='l')
    x, y = bmap(data['lat'].values, data['lon'].values)



    file_name = 'osm_new.png'

    bg_img = None
    bg_img = get_osm_img(minlat=minlat, minlon=minlon, maxlat=maxlat, maxlon=maxlon, scale=12000)
    try:
        bg_img = Image.open(file_name)
    except FileNotFoundError as fnfe:
        bg_img = get_osm_img(minlat=minlat, minlon=minlon, maxlat=maxlat, maxlon=maxlon, scale=12000)
        bg_img.save(file_name)

    bmap.imshow(bg_img, origin='upper')
    bmap.scatter(x, y,
                 c=data['passenger'],
                 cmap=plt.cm.get_cmap('seismic'),
                 alpha=0.5,
                 s=data['passenger'].map(
                     lambda x: (x - data['passenger'].min()) / (data['passenger'].max() - data['passenger'].min()) * (MAX_SIZE - MIN_SIZE) + MIN_SIZE)
                 )
    # bmap.scatter(x, y, c='r', marker='o', s=80, alpha=1.0)

    plt.colorbar()
    plt.xlabel('Latitude')
    plt.ylabel('Longitude')
    plt.savefig('static/plotted.png', dpi=300)
    print('plot started')


def main():
    os.remove('osm_new.png')
    os.remove('static/plotted.png')
    mapping_gps_data()


if __name__ == '__main__':
   app.run(host="0.0.0.0", port=5000, debug=True)