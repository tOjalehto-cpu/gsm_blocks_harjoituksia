#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2023 Your Name <your.email@example.com>.
# 
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation: either version 3, or (at your option)
# any later version.
# 
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this software: see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
# 

from gnuradio import gr, gsm, blocks, qtgui
import osmosdr
from gnuradio.gsm import gsm_bcch_ccch_demapper
from PyQt5 import Qt
import sip
from gnuradio.filter import window
import sys
from controls.controls import ControlWidget  # Import ControlWidget


class SimpleGSMDecoder(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)

        # Samp rate ja frequency class attributeina
        self.samp_rate = 4e6  # Jos samp rate yksi ei näy mitään
        self.center_freq = 900.756e6

        # Printataan käytettävä taajuus
        print(f"Käytettävä taajuus: {self.center_freq / 1e6} MHz")

        # source palikka 1
        self.source1 = osmosdr.source(args="hackrf=0")
        self.source1.set_sample_rate(self.samp_rate)
        self.source1.set_center_freq(self.center_freq)
        self.source1.set_freq_corr(0)
        self.source1.set_dc_offset_mode(0)
        self.source1.set_iq_balance_mode(0)
        self.source1.set_gain_mode(False)
        self.source1.set_gain(30)
        self.source1.set_if_gain(30)
        self.source1.set_bb_gain(40)
        self.source1.set_antenna("", 0)
        self.source1.set_bandwidth(0, 0)

        # source palikka 2
        self.source2 = osmosdr.source(args="hackrf=1")
        self.source2.set_sample_rate(self.samp_rate)
        self.source2.set_center_freq(self.center_freq)
        self.source2.set_freq_corr(0)
        self.source2.set_dc_offset_mode(0)
        self.source2.set_iq_balance_mode(0)
        self.source2.set_gain_mode(False)
        self.source2.set_gain(30)
        self.source2.set_if_gain(30)
        self.source2.set_bb_gain(40)
        self.source2.set_antenna("", 0)
        self.source2.set_bandwidth(0, 0)

        # Rotator block
        self.rotator = blocks.rotator_cc(0.0)

        # Frequency sink for source 1
        self.qtgui_freq_sink1 = qtgui.freq_sink_c(
            1024,  # size
            window.WIN_BLACKMAN_hARRIS,  # wintype
            self.center_freq,  # fc
            self.samp_rate,  # bw
            "Source 1 Spectrum",  # name
            1  # number of inputs
        )
        self.qtgui_freq_sink1.set_update_time(0.10)
        self.qtgui_freq_sink1.set_y_axis(-140, 10)
        self.qtgui_freq_sink1.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink1.enable_autoscale(False)
        self.qtgui_freq_sink1.enable_grid(False)
        self.qtgui_freq_sink1.set_fft_average(1.0)
        self.qtgui_freq_sink1.enable_axis_labels(True)
        self.qtgui_freq_sink1.enable_control_panel(False)

        # Frequency sink for source 2
        self.qtgui_freq_sink2 = qtgui.freq_sink_c(
            1024,  # size
            window.WIN_BLACKMAN_hARRIS,  # wintype
            self.center_freq,  # fc
            self.samp_rate,  # bw
            "Source 2 Spectrum",  # name
            1  # number of inputs
        )
        self.qtgui_freq_sink2.set_update_time(0.10)
        self.qtgui_freq_sink2.set_y_axis(-140, 10)
        self.qtgui_freq_sink2.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink2.enable_autoscale(False)
        self.qtgui_freq_sink2.enable_grid(False)
        self.qtgui_freq_sink2.set_fft_average(1.0)
        self.qtgui_freq_sink2.enable_axis_labels(True)
        self.qtgui_freq_sink2.enable_control_panel(False)

        # GSM input adaptori
        self.gsm_input = gsm.gsm_input(
            ppm=0,
            osr=4,
            fc=self.center_freq,
            samp_rate_in=self.samp_rate,
        )

        # GSM receiver palikka
        self.gsm_receiver = gsm.receiver(4, [0], [0], False)

        # GSM clock offset control
        self.clock_offset_control = gsm.clock_offset_control(
            fc=self.center_freq,
            samp_rate=self.samp_rate,
            osr=4
        )

        # Demapataan BCCH ja CCCH
        self.bcch_ccch_demapper = gsm_bcch_ccch_demapper()

        # Dekoodtaan kontrollikanava
        self.control_channels_decoder = gsm.control_channels_decoder()

        # Yhdistetään palikat
        self.connect((self.source1, 0), (self.rotator, 0))
        self.connect((self.source2, 0), (self.qtgui_freq_sink2, 0))
        self.connect((self.rotator, 0), (self.qtgui_freq_sink1, 0))
        self.connect((self.rotator, 0), (self.gsm_input, 0))
        self.connect((self.gsm_input, 0), (self.gsm_receiver, 0))
        self.msg_connect((self.clock_offset_control, 'ctrl'), (self.gsm_input, 'ctrl_in'))
        self.msg_connect((self.gsm_receiver, 'C0'), (self.bcch_ccch_demapper, 'bursts'))
        self.msg_connect((self.bcch_ccch_demapper, 'bursts'), (self.control_channels_decoder, 'bursts'))
        self.msg_connect((self.gsm_receiver, 'measurements'), (self.clock_offset_control, 'measurements'))

        # Printataan tulokset
        self.sink = blocks.message_debug()
        self.msg_connect((self.control_channels_decoder, 'msgs'), (self.sink, 'print'))

        # Create a top-level Qt widget and add the Qt GUI sink
        self.qtgui_window = Qt.QWidget()
        main_layout = Qt.QVBoxLayout(self.qtgui_window)

        # Add frequency sinks
        main_layout.addWidget(sip.wrapinstance(self.qtgui_freq_sink1.qwidget(), Qt.QWidget))
        main_layout.addWidget(sip.wrapinstance(self.qtgui_freq_sink2.qwidget(), Qt.QWidget))

        # Add control widget
        self.control_widget = ControlWidget(self)
        main_layout.addWidget(self.control_widget)

        self.qtgui_window.show()


if __name__ == '__main__':
    qapp = Qt.QApplication(sys.argv)
    tb = SimpleGSMDecoder()
    tb.start()
    qapp.exec_()
    tb.stop()
    tb.wait()