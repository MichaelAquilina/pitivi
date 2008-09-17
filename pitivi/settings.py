#!/usr/bin/python
# PiTiVi , Non-linear video editor
#
#       settings.py
#
# Copyright (c) 2005, Edward Hervey <bilboed@bilboed.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

"""
Multimedia settings
"""

import os
import gobject
import gst
import string

from serializable import Serializable, to_object_from_data_type

from gettext import gettext as _

def get_bool_env(name):
    """
    Checks the given env variable name and returns a boolean answer.
    If it exists AND contains something different from '' or 0, then this
    function will return True. Else it will return False.
    """
    var = os.getenv(name)
    if not var:
        return False
    if var == '0':
        return False
    return True

class GlobalSettings:
    """
    Global PiTiVi settings
    """

    # TODO : Improve this class to make it more flexible
    # * The settings should be discover-able by UI for ex
    # * plugins should be able to add some settings

    def __init__(self, **unused_kw):
        self._setDefaults()
        self._readSettings()

    def _setDefaults(self):
        self.advancedModeEnabled = True
        self.fileSupportEnabled = False

    def _readSettings(self):
        self._readSettingsFromGlobalConfiguration()
        self._readSettingsFromConfigurationFile()
        # env variables have the highest priority
        self._readSettingsFromEnvironmentVariables()

    def _readSettingsFromGlobalConfiguration(self):
        # ideally, this should read settings from GConf for ex
        pass

    def _readSettingsFromConfigurationFile(self):
        # This reads the configuration from the user configuration file
        pass

    def _readSettingsFromEnvironmentVariables(self):
        # reads some settings from environment variable
        #self.advancedModeEnabled =
        #get_bool_env("PITIVI_ADVANCED_MODE")
        #self.fileSupportEnabled = get_bool_env("PITIVI_FILE_SUPPORT")
        self.fileSupportEnabled = True
        pass

    def get_local_plugin_path(self, autocreate=True):
        """
        Compute the absolute path to local plugin repository

        @param autocreate: create the path if missing
        @return: the plugin repository path
        """

        pitivi_path = os.path.expanduser("~/.pitivi")
        if not os.path.exists(pitivi_path) and autocreate:
            os.mkdir(pitivi_path)

        repository_path = os.path.expanduser("~/.pitivi/plugins")
        if not os.path.exists(repository_path) and autocreate:
            os.mkdir(repository_path)

        return repository_path

    def get_plugin_settings_path(self, autocreate=True):
        """
        Compute the absolute path to local plugin settings' repository

        @param autocreate: create the path if missing
        @return: the plugin settings path
        """

        pitivi_path = os.path.expanduser("~/.pitivi")
        if not os.path.exists(pitivi_path) and autocreate:
            os.mkdir(pitivi_path)

        repository_path = os.path.expanduser("~/.pitivi/plugins-settings")
        if not os.path.exists(repository_path) and autocreate:
            os.mkdir(repository_path)

        return repository_path

class ExportSettings(gobject.GObject, Serializable):
    """
    Multimedia export settings

    Signals:

    'settings-changed' : the settings have changed
    'encoders-changed' : The encoders or muxer have changed
    """
    __gsignals__ = {
        "settings-changed" : ( gobject.SIGNAL_RUN_LAST,
                              gobject.TYPE_NONE,
                              (  )),
        "encoders-changed" : ( gobject.SIGNAL_RUN_LAST,
                               gobject.TYPE_NONE,
                               ( ))
        }

    __data_type__ = "export-settings"

    # Audio/Video settings for processing/export

    # TODO : Add PAR/DAR for video
    # TODO : switch to using GstFraction internally where appliable

    def __init__(self, **unused_kw):
        gobject.GObject.__init__(self)
        self.videowidth = 720
        self.videoheight = 576
        self.videorate = gst.Fraction(25,1)
        self.videopar = gst.Fraction(1,1)
        self.audiochannels = 2
        self.audiorate = 44100
        self.audiodepth = 16
        self.vencoder = "theoraenc"
        self.aencoder = "vorbisenc"
        self.muxer = "oggmux"
        self.containersettings = {}
        self.acodecsettings = {}
        self.vcodecsettings = {}
        self.muxers = available_muxers()
        self.vencoders = available_video_encoders()
        self.aencoders = available_audio_encoders()

    def __str__(self):
        msg = _("Export Settings\n")
        msg += _("Video :") + str(self.videowidth) + " " + str(self.videoheight) + " " + str(self.videorate) + " " + str (self.videopar)
        msg += "\n\t" + str(self.vencoder) + " " +str(self.vcodecsettings)
        msg += _("\nAudio :") + str(self.audiochannels) + " " + str(self.audiorate) + " " + str(self.audiodepth)
        msg += "\n\t" + str(self.aencoder) + " " + str(self.acodecsettings)
        msg += _("\nMuxer :") + str(self.muxer) + " " + str(self.containersettings)
        return msg

    def getVideoCaps(self):
        """ Returns the GstCaps corresponding to the video settings """
        astr = "width=%d,height=%d,pixel-aspect-ratio=%d/%d,framerate=%d/%d" % (self.videowidth, self.videoheight,
                                                                                self.videopar.num, self.videopar.denom,
                                                                                self.videorate.num, self.videorate.denom)
        vcaps = gst.caps_from_string("video/x-raw-yuv,%s;video/x-raw-rgb,%s" % (astr, astr))
        if self.vencoder:
            return get_compatible_sink_caps(self.vencoder, vcaps)
        return vcaps

    def getVideoDescription(self):
        """ Returns a human-readable markup-ed string describing the video properties """
        res = "%d x %d <i>pixels</i> at %.2f <i>fps</i> <i>(%s)</i>"
        return res % (self.videowidth, self.videoheight,
                      float(self.videorate), self.vencoder)

    def getAudioDescription(self):
        """ Returns a human-readable markup-ed string describing the audio properties """
        res = "%d channels at %d <i>Hz</i> (%d <i>bits</i>) <i>(%s)</i>"
        return res % (self.audiochannels, self.audiorate, self.audiodepth, self.aencoder)

    def getAudioCaps(self):
        """ Returns the GstCaps corresponding to the audio settings """
        astr = "rate=%d,channels=%d" % (self.audiorate, self.audiochannels)
        astrcaps = gst.caps_from_string("audio/x-raw-int,%s;audio/x-raw-float,%s" % (astr, astr))
        if self.aencoder:
            return get_compatible_sink_caps(self.aencoder, astrcaps)
        return astrcaps

        # interset with current audioencoder sink pad caps

    def setVideoProperties(self, width=-1, height=-1, framerate=-1, par=-1):
        """ Set the video width, height and framerate """
        gst.info("set_video_props %d x %d @ %r fps" % (width, height, framerate))
        changed = False
        if not width == -1 and not width == self.videowidth:
            self.videowidth = width
            changed = True
        if not height == -1 and not height == self.videoheight:
            self.videoheight = height
            changed = True
        if not framerate == -1 and not framerate == self.videorate:
            self.videorate = framerate
            changed = True
        if not par == -1 and not par == self.videopar:
            self.videopar = par
            changed = True
        if changed:
            self.emit("settings-changed")

    def setAudioProperties(self, nbchanns=-1, rate=-1, depth=-1):
        """ Set the number of audio channels, rate and depth """
        gst.info("%d x %dHz %dbits" % (nbchanns, rate, depth))
        changed = False
        if not nbchanns == -1 and not nbchanns == self.audiochannels:
            self.audiochannels = nbchanns
            changed = True
        if not rate == -1 and not rate == self.audiorate:
            self.audiorate = rate
            changed = True
        if not depth == -1 and not depth == self.audiodepth:
            self.audiodepth = depth
            changed = True
        if changed:
            self.emit("settings-changed")

    def setEncoders(self, muxer="", vencoder="", aencoder=""):
        """ Set the video/audio encoder and muxer """
        changed = False
        if not muxer == "" and not muxer == self.muxer:
            self.muxer = muxer
            changed = True
        if not vencoder == "" and not vencoder == self.vencoder:
            self.vencoder = vencoder
            changed = True
        if not aencoder == "" and not aencoder == self.aencoder:
            self.aencoder = aencoder
            changed = True
        if changed:
            self.emit("encoders-changed")

    ## Serializable methods

    def toDataFormat(self):
        ret = Serializable.toDataFormat(self)
        ret["video-width"] = self.videowidth
        ret["video-height"] = self.videoheight
        ret["video-rate"] = [ self.videorate.num,
                             self.videorate.denom ]
        ret["video-par"] = [ self.videopar.num,
                            self.videopar.denom ]
        ret["audio-channels"] = self.audiochannels
        ret["audio-rate"] = self.audiorate
        ret["audio-depth"] = self.audiodepth
        ret["video-encoder"] = self.vencoder
        ret["audio-encoder"] = self.aencoder
        ret["muxer"] = self.muxer
        if self.containersettings:
            ret["container-settings"] = self.containersettings
        if self.acodecsettings:
            ret["audio-encoder-settings"] = self.acodecsettings
        if self.vcodecsettings:
            ret["video-encoder-settings"] = self.vcodecsettings
        return ret

    def fromDataFormat(self, obj):
        Serializable.fromDataFormat(self, obj)
        self.videowidth = obj["video-width"]
        self.videoheight = obj["video-height"]
        self.videorate = gst.Fraction(*obj["video-rate"])
        self.videopar = gst.Fraction(*obj["video-par"])

        self.audiochannels = obj["audio-channels"]
        self.audiorate = obj["audio-rate"]
        self.audiodepth = obj["audio-depth"]

        # FIXME : check if the given encoder/muxer are available
        self.vencoder = obj["video-encoder"]
        self.aencoder = obj["audio-encoder"]
        self.muxer = obj["muxer"]
        if "container-settings" in obj:
            self.containersettings = obj["container-settings"]
        if "audio-encoder-settings" in obj:
            self.acodecsettings = obj["audio-encoder-settings"]
        if "video-encoder-settings" in obj:
            self.vcodecsettings = obj["video-encoder-settings"]

def get_compatible_sink_caps(factoryname, caps):
    """
    Returns the compatible caps between 'caps' and the sink pad caps of 'factoryname'
    """
    gst.log("factoryname : %s , caps : %s" % (factoryname, caps.to_string()))
    factory = gst.registry_get_default().lookup_feature(factoryname)
    if factory == None:
        gst.warning("%s is not a valid factoryname" % factoryname)
        return None

    res = []
    sinkcaps = [x.get_caps() for x in factory.get_static_pad_templates() if x.direction == gst.PAD_SINK]
    for c in sinkcaps:
        gst.log("sinkcaps %s" % c.to_string())
        inter = caps.intersect(c)
        gst.log("intersection %s" % inter.to_string())
        if inter:
            res.append(inter)

    if len(res) > 0:
        return res[0]
    return None

def list_compat(a, b):
    for x in a:
        if not x in b:
            return False
    return True

def my_can_sink_caps(muxer, ocaps):
    """ returns True if the given caps intersect with some of the muxer's
    sink pad templates' caps.
    """
    sinkcaps = [x.get_caps() for x in muxer.get_static_pad_templates() if x.direction == gst.PAD_SINK]
    for x in sinkcaps:
        if not x.intersect(ocaps).is_empty():
            return True
    return False

def available_muxers():
    """ return all available muxers """
    flist = gst.registry_get_default().get_feature_list(gst.ElementFactory)
    res = []
    for fact in flist:
        if list_compat(["Codec", "Muxer"], string.split(fact.get_klass(), '/')):
            res.append(fact)
    gst.log(str(res))
    return res

def available_video_encoders():
    """ returns all available video encoders """
    flist = gst.registry_get_default().get_feature_list(gst.ElementFactory)
    res = []
    for fact in flist:
        if list_compat(["Codec", "Encoder", "Video"], string.split(fact.get_klass(), '/')):
            res.append(fact)
        elif list_compat(["Codec", "Encoder", "Image"], string.split(fact.get_klass(), '/')):
            res.append(fact)
    gst.log(str(res))
    return res

def available_audio_encoders():
    """ returns all available audio encoders """
    flist = gst.registry_get_default().get_feature_list(gst.ElementFactory)
    res = []
    for fact in flist:
        if list_compat(["Codec", "Encoder", "Audio"], string.split(fact.get_klass(), '/')):
            res.append(fact)
    gst.log(str(res))
    return res

def encoders_muxer_compatible(encoders, muxer):
    """ returns the list of encoders compatible with the given muxer """
    gst.info("")
    res = []
    for encoder in encoders:
        for caps in [x.get_caps() for x in encoder.get_static_pad_templates() if x.direction == gst.PAD_SRC]:
            if my_can_sink_caps(muxer, caps):
                res.append(encoder)
                break
    return res

def muxer_can_sink_raw_audio(muxer):
    return my_can_sink_caps(muxer, gst.Caps("audio/x-raw-float;audio/x-raw-int"))

def muxer_can_sink_raw_video(muxer):
    return my_can_sink_caps(muxer, gst.Caps("video/x-raw-yuv;video/x-raw-rgb"))

