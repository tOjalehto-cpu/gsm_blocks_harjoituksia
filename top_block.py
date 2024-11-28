from gnuradio import gr
from gnuradio import qtgui
from PyQt5 import Qt
import sys
from multi_hackrf_one_block import multi_hackrf_source
import sip
from gnuradio.filter import window

class top_block(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self, "Top Block")
        
        # Luo multi_hackrf_source-olion määritetyillä parametreilla
        self.multi_hackrf = multi_hackrf_source(
            sample_rate=2e6,
            num_channels=2,
            hackrf_ids=["0000000000000000c66c63dc37540883", "0000000000000000147c63dc33993353"],
            sync_center_freq=100e6,
            sync_gains={0: 20, 1: 20},
            center_freqs={0: 100e6, 1: 100e6},
            gains={0: 20, 1: 20}
        )
        
        # Luo taajuusikkuna
        self.freq_sink = qtgui.freq_sink_c(
            1024,  # FFT-koko
            window.WIN_BLACKMAN_hARRIS,  # Ikkunatyyppi
            100e6,  # Keskitaajuus
            2e6,  # Näytteenottotaajuus
            "Frequency Sink",  # Nimi
            2  # Kanavien määrä
        )
        self.freq_sink.set_update_time(0.10)
        self.freq_sink.set_y_axis(-140, 10)
        self.freq_sink.set_y_label('Relative Gain', 'dB')
        self.freq_sink.enable_autoscale(False)
        self.freq_sink.enable_grid(False)
        self.freq_sink.set_fft_average(1.0)
        self.freq_sink.enable_axis_labels(True)
        self.freq_sink.enable_control_panel(False)

        # Yhdistä multi_hackrf_source taajuusikkunaan
        for chan in range(2):
            self.connect((self.multi_hackrf, chan), (self.freq_sink, chan))

        # Luo ylimmän tason Qt-widget ja lisää taajuusikkuna
        self.qtgui_window = Qt.QWidget()
        self.qtgui_layout = Qt.QVBoxLayout(self.qtgui_window)
        self.qtgui_layout.addWidget(sip.wrapinstance(self.freq_sink.qwidget(), Qt.QWidget))
        self.qtgui_window.show()

if __name__ == "__main__":
    qapp = Qt.QApplication(sys.argv)
    tb = top_block()
    tb.start()
    tb.multi_hackrf.synchronize()
    qapp.exec_()
    tb.stop()
    tb.wait()