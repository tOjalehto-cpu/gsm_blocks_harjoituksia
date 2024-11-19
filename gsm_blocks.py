from gnuradio import gr, gsm, blocks, qtgui
import osmosdr
from gnuradio.gsm import gsm_bcch_ccch_demapper
from PyQt5 import Qt
import sip
from gnuradio.filter import window



class SimpleGSMDecoder(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)

        #Samp rate ja frequency class attributeina
        self.samp_rate = 1e6
        self.center_freq = 945.2e6

        # source palikka
        self.source = osmosdr.source(args="hackrf=0")
        self.source.set_sample_rate(self.samp_rate)
        self.source.set_center_freq(self.center_freq)
        self.source.set_freq_corr(0)
        self.source.set_dc_offset_mode(0)
        self.source.set_iq_balance_mode(0)
        self.source.set_gain_mode(False)
        self.source.set_gain(30)
        self.source.set_if_gain(30)
        self.source.set_bb_gain(20)
        self.source.set_antenna("", 0)
        self.source.set_bandwidth(0, 0)

        # Rotator block
        self.rotator = blocks.rotator_cc(0.0)

        # Frequency sink
        self.qtgui_freq_sink = qtgui.freq_sink_c(
            1024, # size
            window.WIN_BLACKMAN_hARRIS, # wintype
            0, # fc
            1e6, # bw
            "Frequency Sink", # name
            1 # number of inputs
        )
        self.qtgui_freq_sink.set_update_time(0.10)
        self.qtgui_freq_sink.set_y_axis(-140, 10)
        self.qtgui_freq_sink.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink.enable_autoscale(False)
        self.qtgui_freq_sink.enable_grid(False)
        self.qtgui_freq_sink.set_fft_average(1.0)
        self.qtgui_freq_sink.enable_axis_labels(True)
        self.qtgui_freq_sink.enable_control_panel(False)

        # GSM input adaptori
        self.gsm_input = gsm.gsm_input(
            ppm =0,
            osr =4,
            fc = self.center_freq,
            samp_rate_in = self.samp_rate,
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
        self.connect((self.source, 0), (self.rotator, 0))
        self.connect((self.rotator, 0), (self.qtgui_freq_sink, 0))
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
        self.qtgui_layout = Qt.QVBoxLayout(self.qtgui_window)
        self.qtgui_layout.addWidget(sip.wrapinstance(self.qtgui_freq_sink.qwidget(), Qt.QWidget))
        self.qtgui_window.show()

if __name__ == '__main__':
    import sys
    from gnuradio import qtgui
    from PyQt5 import Qt

    qapp = Qt.QApplication(sys.argv)
    tb = SimpleGSMDecoder()
    tb.start()
    tb.qtgui_window.show()
    qapp.exec_()
    tb.stop()
    tb.wait()