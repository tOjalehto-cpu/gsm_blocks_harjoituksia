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

from gnuradio import blocks, gr
from gnuradio.filter import firdes
from gnuradio import soapy
import numpy as np
import threading
import time
from math import log, ceil

def xcorr(X, Y, maxlag):
    N = max(len(X), len(Y))
    N_nextpow2 = ceil(log(N + maxlag, 2))
    M = 2**N_nextpow2
    if len(X) < M:
        postpad_X = int(M - len(X) - maxlag)
    else:
        postpad_X = 0

    if len(Y) < M:
        postpad_Y = int(M - len(Y))
    else:
        postpad_Y = 0
        
    pre  = np.fft.fft(np.pad(X, (maxlag, postpad_X), 'constant', constant_values=(0, 0)))
    post = np.fft.fft(np.pad(Y, (0, postpad_Y), 'constant', constant_values=(0, 0)))
    cor  = np.fft.ifft(pre * np.conj(post))
    R = cor[0:2*maxlag]
    return R

class vector_sink_fullness_notifier:
    def __init__(self, b):
        self.b = b
        self.d_mutex = threading.Lock()

    def eval(self):
        self.d_mutex.acquire()
        try:
            self.b.fullness_report()
        except Exception as e:
            print("Vector sink fullness notification exception: ", e)
        finally:
            self.d_mutex.release()

class multi_hackrf_source(gr.hier_block2):
    def __init__(self, sample_rate=2e6, num_channels=2, hackrf_ids=[], sync_period=0.15, sync_center_freq=100e6, sync_gains={}, center_freqs={}, gains={}, bandwidth=20e6):
        gr.hier_block2.__init__(self,
            "multi_hackrf_source",
            gr.io_signature(0, 0, 0),  # Input signature
            gr.io_signature(num_channels, num_channels, gr.sizeof_gr_complex)  # Output signature
        )

        self.state = "sync"  # tilat: sync, work
        self.num_channels = num_channels
        self.hackrf_ids = hackrf_ids
        self.sample_rate = sample_rate
        self.delays = {}
        self.bandwidth = bandwidth

        self.gains = gains
        self.center_freqs = center_freqs

        self.sync_samples = int(round(sync_period * sample_rate / 2) * 2)
        self.sync_gains = sync_gains
        self.sync_center_freq = sync_center_freq

        self.phase_amplitude_corrections = {}
        self.phase_and_amplitude_correctors = {}
        self.hackrf_sources = {}
        self.delay_blocks = {}
        self.vsinks = {}

        self.vsink_notifier = vector_sink_fullness_notifier(self)

        for chan in range(self.num_channels):
            dev = f'driver=hackrf,serial={hackrf_ids[chan]}' if chan < len(hackrf_ids) else 'driver=hackrf'
            self.hackrf_sources[chan] = soapy.source(dev, "fc32", 1, '', '', [''], [''])
            self.hackrf_sources[chan].set_sample_rate(0, self.sample_rate)
            self.hackrf_sources[chan].set_bandwidth(0, self.bandwidth)
            self.hackrf_sources[chan].set_gain(0, 'AMP', 0)
            self.hackrf_sources[chan].set_gain(0, 'LNA', 24)
            self.hackrf_sources[chan].set_gain(0, 'VGA', 24)

            self.vsinks[chan] = blocks.vector_sink_c()

        self.apply_synchronization_settings()

        for chan in range(self.num_channels):
            self.delay_blocks[chan] = blocks.delay(gr.sizeof_gr_complex, 0)
            self.phase_amplitude_corrections[chan] = 1.0
            self.phase_and_amplitude_correctors[chan] = blocks.multiply_const_vcc((self.phase_amplitude_corrections[chan],))

            self.connect((self.hackrf_sources[chan], 0), (self.vsinks[chan], 0))
            self.connect((self.hackrf_sources[chan], 0), (self.delay_blocks[chan], 0))
            self.connect((self.delay_blocks[chan], 0), (self.phase_and_amplitude_correctors[chan], 0))

        # Ensure the output ports are connected
        for chan in range(self.num_channels):
            self.connect((self.phase_and_amplitude_correctors[chan], 0), (self, chan))

    def fullness_report(self):
        self.compute_and_set_delays()

    def compute_and_set_delays(self):
        N = self.sync_samples
        self.apply_operational_settings()

        self.delays[0] = 0
        sync_data = [self.vsinks[chan].data() for chan in range(self.num_channels)]

        self.phase_amplitude_corrections[0] = 1
        var0 = np.var(sync_data[0])
        for chan in range(1, self.num_channels):
            result_corr = xcorr(sync_data[0], sync_data[chan], int(len(sync_data[0]) / 2))
            max_position = np.argmax(np.abs(result_corr))
            self.delays[chan] = len(result_corr) / 2 - max_position

            self.phase_amplitude_corrections[chan] = result_corr[max_position] / np.sqrt(np.mean(np.real(sync_data[chan])**2 + np.imag(sync_data[chan])**2))
            self.phase_and_amplitude_correctors[chan].set_k((np.sqrt(var0 / np.var(sync_data[chan])) * (np.exp(1j * np.angle(self.phase_amplitude_corrections[chan]))),))

        for chan in range(self.num_channels):
            print(f"Delay of channel {chan}: {self.delays[chan]}, phase diff: {np.angle(self.phase_amplitude_corrections[chan]) / np.pi * 180} [deg]")
            self.delay_blocks[chan].set_dly(-int(self.delays[chan]))

        self.state = "work"

    def synchronize(self):
        if self.state == "work":
            self.apply_synchronization_settings()
            self.state = "sync"
            self.full_vsinks_counter = 0

            time.sleep(0.1)
            for chan in range(self.num_channels):
                self.vsinks[chan].reset()

    def apply_synchronization_settings(self):
        for chan in range(self.num_channels):
            self.hackrf_sources[chan].set_frequency(0, self.sync_center_freq)
            if len(self.sync_gains) == self.num_channels:
                self.hackrf_sources[chan].set_gain(0, 'VGA', self.sync_gains[chan])
            else:
                self.hackrf_sources[chan].set_gain(0, 'VGA', 30)

    def apply_operational_settings(self):
        for chan in range(self.num_channels):
            self.hackrf_sources[chan].set_gain(0, 'VGA', self.gains[chan])
            self.hackrf_sources[chan].set_frequency(0, self.center_freqs[chan])

    def get_num_channels(self):
        return self.num_channels

    def get_sample_rate(self):
        return self.sample_rate

    def get_center_freq(self, chan=0):
        return self.center_freqs[chan]

    def set_center_freq(self, freq, chan=0):
        self.center_freqs[chan] = freq
        print(f"Setting center freq {freq}")
        if self.state == "work":
            self.hackrf_sources[chan].set_frequency(0, freq)

    def get_freq_corr(self):
        return self.ppm

    def set_freq_corr(self, ppm):
        self.ppm = ppm
        print(f"Setting freq corr {ppm}")
        for chan in range(self.num_channels):
            self.hackrf_sources[chan].set_frequency_correction(0, self.ppm)

    def get_gain(self, chan=0):
        return self.gains[chan]

    def set_gain(self, gain, chan=0):
        self.gains[chan] = gain
        if self.state == "work":
            self.hackrf_sources[chan].set_gain(0, 'VGA', gain)

    def get_sync_center_freq(self):
        return self.sync_center_freq

    def set_sync_center_freq(self, freq, chan=0):
        self.sync_center_freq = freq
        if self.state == "sync":
            self.hackrf_sources[chan].set_frequency(0, freq)

    def get_sync_gain(self, chan=0):
        return self.sync_gains[chan]

    def set_sync_gain(self, gain, chan=0):
        self.sync_gains[chan] = gain
        if self.state == "sync":
            self.hackrf_sources[chan].set_gain(0, 'VGA', gain)

if __name__ == "__main__":
    from gnuradio import qtgui
    from PyQt5 import Qt
    import sys

    qapp = Qt.QApplication(sys.argv)
    tb = multi_hackrf_source(sample_rate=2e6, num_channels=2, hackrf_ids=["0000000000000000c66c63dc37540883", "0000000000000000147c63dc33993353"], sync_center_freq=100e6, sync_gains={0: 20, 1: 20}, center_freqs={0: 100e6, 1: 100e6}, gains={0: 20, 1: 20})
    tb.start()
    tb.synchronize()
    qapp.exec_()
    tb.stop()
    tb.wait()