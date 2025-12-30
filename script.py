# -*- coding: utf-8 -*-
#py3
from resources.lib import kodiutils
from resources.lib import kodilogging
import io
import os
import sys
import time
import zipfile
import urllib
import urllib.request
import logging
import xbmcaddon
import xbmcgui
import xbmc,xbmcvfs,base64
import shutil


       
ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))


class Canceled(Exception):
    pass


class MyProgressDialog():
    def __init__(self, process):
        self.dp = xbmcgui.DialogProgress()
        self.dp.create("Build Installer", "[CR]".join((process, '', 'Bitte warten...')))

    def __call__(self, block_num, block_size, total_size):
        if self.dp.iscanceled():
            self.dp.close()
            raise Canceled
        percent = (block_num * block_size * 100) / total_size
        if percent < total_size:
            self.dp.update(int(percent))
        else:
            self.dp.close()

def exists(path):
    try:
        f = urllib.request.urlopen(path).getcode()
        return True
    except:
        return False



def read(response, progress_dialog):
    data = b""
    total_size = response.getheader('Content-Length').strip()
    total_size = int(total_size)
    bytes_so_far = 0
    chunk_size = 1024 * 1024
    reader = lambda: response.read(chunk_size)
    for index, chunk in enumerate(iter(reader, b"")):
        data += chunk
        progress_dialog(index, chunk_size, total_size)
    return data


def extract(zip_file, output_directory, progress_dialog):
    try:
        fav = xbmcvfs.translatePath('special://home/userdata/favourites.xml')
        favNew = xbmcvfs.translatePath('special://home/favourites.xml')
        shutil.move(fav,favNew)
    except:
        pass
    zin = zipfile.ZipFile(zip_file)
    files_number = len(zin.infolist())
    for index, item in enumerate(zin.infolist()):
        try:
            progress_dialog(index, 1, files_number)
        except Canceled:
            return False
        else:
            zin.extract(item, output_directory)
    return True


def get_update(version):
    addon_name = ADDON.getAddonInfo('name')
    bundleURL = "https://drive.usercontent.google.com/download?id=1SfsmWAF-sBTqkY-V5UC62XLL2ASI7hV5&export=download&authuser=5&confirm=t&uuid=619383cd-cd7e-49d7-8078-c45c3f77e0de&at=ANTm3czjVnze4Ct8XM65TXgSCCiO:1767094894850"
    yesnowindow = xbmcgui.Dialog().yesno('Build Installer', 'Ein Installation ist verfügbar![CR]Möchtest du  installieren?', yeslabel='JA', nolabel='SPÄTER')
    dialog = xbmcgui.Dialog()
    succ = False
    zipped = False
    if yesnowindow == 1:
    
        if not exists(bundleURL):
            xbmcgui.Dialog().ok('Build Installer [B][COLORred]OFFLINE[/COLOR][/B]','Aktuell leider nicht verfügbar.Versuche es später nochmal...' )
            sys.exit() 
           
        try:
            url = bundleURL
            response = urllib.request.urlopen(url)
        except:
            xbmcgui.Dialog().ok('Build Installer [B][COLORred]OFFLINE[/COLOR][/B]','Aktuell leider nicht verfügbar.Versuche es später nochmal...' )
            sys.exit()
        try:
            data = read(response, MyProgressDialog("Installation wird heruntergeladen ..."))
        except Canceled:
            message = "Download abgebrochen );"
        else:
            addon_folder = xbmcvfs.translatePath(os.path.join('special://', 'home'))
            zipped = True
            if extract(io.BytesIO(data), addon_folder, MyProgressDialog("Installation...")):
                message = "Installation erfolgreich abgeschlossen."
                succ = True
            else:
                message = "Die Installation wurde abgebrochen );"

        if succ:
            d = open(os.path.join(xbmcvfs.translatePath('special://home'), 'version'), "w")
            d.write(str(version))
            d.close()
        if zipped:
            try:
                fav = xbmcvfs.translatePath('special://home/userdata/favourites.xml')
                favNew = xbmcvfs.translatePath('special://home/favourites.xml')
                shutil.rmtree(fav, ignore_errors=True)
                shutil.move(favNew,fav)
            except:
                pass
        dialog = xbmcgui.Dialog()
        dialog.ok(addon_name, "%s. Kodi wird beendet, um den Vorgang abzuschliessen....." % message)
        os._exit(0)
    else:
        dialog.ok('Build Installer','Update nicht durchgeführt!...')
