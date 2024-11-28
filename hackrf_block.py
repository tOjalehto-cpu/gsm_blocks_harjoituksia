from gnuradio import gr, blocks, soapy, qtgui
from gnuradio.filter import window
from PyQt5 import Qt
import sys
import sip

class hackrf_block(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)

        self.sample_rate = 10e6
        self.center_freq = 105.2e6
        self.bandwidth = 0
        self.amp = False
        self.if_gain = 30
        self.vga_gain = 40

        # Create Soapy HackRF Source block
        dev = 'driver=hackrf'
        stream_args = ''
        tune_args = ['']
        settings = ['']

        self.soapy_hackrf_source = soapy.source(dev, "fc32", 1, '',
                                                stream_args, tune_args, settings)
        self.soapy_hackrf_source.set_sample_rate(0, self.sample_rate)
        self.soapy_hackrf_source.set_bandwidth(0, self.bandwidth)
        self.soapy_hackrf_source.set_frequency(0, self.center_freq)
        self.soapy_hackrf_source.set_gain(0, 'AMP', self.amp)
        self.soapy_hackrf_source.set_gain(0, 'LNA', min(max(self.if_gain, 0.0), 40.0))
        self.soapy_hackrf_source.set_gain(0, 'VGA', min(max(self.vga_gain, 0.0), 62.0))

        # Create a frequency sink
        self.freq_sink = qtgui.freq_sink_c(
            1024, # size of the FFT
            window.WIN_BLACKMAN_hARRIS, # window type
            self.center_freq, # center frequency
            self.sample_rate, # sample rate
            "Frequency Sink", # name
            1 # number of inputs
        )
        self.freq_sink.set_update_time(0.10)
        self.freq_sink.set_y_axis(-140, 10)
        self.freq_sink.set_y_label('Relative Gain', 'dB')
        self.freq_sink.enable_autoscale(False)
        self.freq_sink.enable_grid(False)
        self.freq_sink.set_fft_average(1.0)
        self.freq_sink.enable_axis_labels(True)
        self.freq_sink.enable_control_panel(False)

        # Connect the Soapy HackRF source to the frequency sink
        self.connect(self.soapy_hackrf_source, self.freq_sink)

        # Example of connecting the Soapy HackRF source to a null sink
        self.null_sink = blocks.null_sink(gr.sizeof_gr_complex)
        self.connect(self.soapy_hackrf_source, self.null_sink)

        # Create a top-level Qt widget and add the Qt GUI sink
        self.qtgui_window = Qt.QWidget()
        self.qtgui_layout = Qt.QVBoxLayout(self.qtgui_window)
        self.qtgui_layout.addWidget(sip.wrapinstance(self.freq_sink.qwidget(), Qt.QWidget))
        self.qtgui_window.show()

if __name__ == "__main__":
    from distutils.version import StrictVersion
    if StrictVersion(Qt.qVersion()) >= StrictVersion("5.0.0"):
        Qt.QApplication.setAttribute(Qt.Qt.AA_EnableHighDpiScaling, True)
    qapp = Qt.QApplication(sys.argv)
    tb = hackrf_block()
    tb.start()
    tb.qtgui_window.show()
    qapp.exec_()
    tb.stop()
    tb.wait()
