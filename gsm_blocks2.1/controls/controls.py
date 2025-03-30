from PyQt5 import Qt


class ControlWidget(Qt.QWidget):
    def __init__(self, decoder):
        super(ControlWidget, self).__init__()
        self.decoder = decoder
        self.initUI()

    def initUI(self):
        # Luo pääasettelu
        self.layout = Qt.QVBoxLayout()

        # Lisää kontrollit (Device 1 ja Device 2)
        self.layout.addWidget(Qt.QLabel("Device 1 Controls"))
        self.layout.addWidget(Qt.QLabel("RF Gain (0 or 11):"))
        self.device1_rf_gain = Qt.QLineEdit(str(self.decoder.source1.get_gain("AMP")))
        self.device1_rf_gain.setPlaceholderText("RF Gain (0 or 11)")
        self.device1_rf_gain.returnPressed.connect(self.update_device1_rf_gain)
        self.layout.addWidget(self.device1_rf_gain)

        self.layout.addWidget(Qt.QLabel("IF Gain (0-40, step 8):"))
        self.device1_if_gain = Qt.QLineEdit(str(self.decoder.source1.get_gain("LNA")))
        self.device1_if_gain.setPlaceholderText("IF Gain (0-40, step 8)")
        self.device1_if_gain.returnPressed.connect(self.update_device1_if_gain)
        self.layout.addWidget(self.device1_if_gain)

        self.layout.addWidget(Qt.QLabel("Baseband Gain (0-62, step 2):"))
        self.device1_bb_gain = Qt.QLineEdit(str(self.decoder.source1.get_gain("VGA")))
        self.device1_bb_gain.setPlaceholderText("Baseband Gain (0-62, step 2)")
        self.device1_bb_gain.returnPressed.connect(self.update_device1_bb_gain)
        self.layout.addWidget(self.device1_bb_gain)

        # Lisää taajuussäädin Device 1:lle
        self.layout.addWidget(Qt.QLabel("Device 1 Frequency (Hz):"))
        self.device1_freq = Qt.QLineEdit(str(self.decoder.source1.get_center_freq()))
        self.device1_freq.setPlaceholderText("Enter frequency in Hz")
        self.device1_freq.returnPressed.connect(self.update_device1_freq)
        self.layout.addWidget(self.device1_freq)

        self.layout.addWidget(Qt.QLabel("Device 2 Controls"))
        self.layout.addWidget(Qt.QLabel("RF Gain (0 or 11):"))
        self.device2_rf_gain = Qt.QLineEdit(str(self.decoder.source2.get_gain("AMP")))
        self.device2_rf_gain.setPlaceholderText("RF Gain (0 or 11)")
        self.device2_rf_gain.returnPressed.connect(self.update_device2_rf_gain)
        self.layout.addWidget(self.device2_rf_gain)

        self.layout.addWidget(Qt.QLabel("IF Gain (0-40, step 8):"))
        self.device2_if_gain = Qt.QLineEdit(str(self.decoder.source2.get_gain("LNA")))
        self.device2_if_gain.setPlaceholderText("IF Gain (0-40, step 8)")
        self.device2_if_gain.returnPressed.connect(self.update_device2_if_gain)
        self.layout.addWidget(self.device2_if_gain)

        self.layout.addWidget(Qt.QLabel("Baseband Gain (0-62, step 2):"))
        self.device2_bb_gain = Qt.QLineEdit(str(self.decoder.source2.get_gain("VGA")))
        self.device2_bb_gain.setPlaceholderText("Baseband Gain (0-62, step 2)")
        self.device2_bb_gain.returnPressed.connect(self.update_device2_bb_gain)
        self.layout.addWidget(self.device2_bb_gain)

        # Lisää taajuussäädin Device 2:lle
        self.layout.addWidget(Qt.QLabel("Device 2 Frequency (Hz):"))
        self.device2_freq = Qt.QLineEdit(str(self.decoder.source2.get_center_freq()))
        self.device2_freq.setPlaceholderText("Enter frequency in Hz")
        self.device2_freq.returnPressed.connect(self.update_device2_freq)
        self.layout.addWidget(self.device2_freq)

        # Luo scroll area
        scroll_area = Qt.QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Luo widgetti, joka sisältää kaikki kontrollit
        container_widget = Qt.QWidget()
        container_widget.setLayout(self.layout)

        # Aseta container_widget scroll area -widgettiin
        scroll_area.setWidget(container_widget)

        # Lisää scroll area pääasetteluun
        main_layout = Qt.QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    # Päivitysmetodit (esimerkki yhdelle kontrollille)
    def update_device1_rf_gain(self):
        try:
            gain = int(self.device1_rf_gain.text())
            if gain in [0, 11]:
                self.decoder.source1.set_gain(gain, "AMP")
                print(f"Device 1 RF Gain set to: {gain}")
            else:
                print("Invalid RF Gain for Device 1 (must be 0 or 11)")
        except ValueError:
            print("Invalid RF Gain input for Device 1")

    def update_device1_if_gain(self):
        try:
            gain = int(self.device1_if_gain.text())
            if gain % 8 == 0 and 0 <= gain <= 40:
                self.decoder.source1.set_gain(gain, "LNA")
                print(f"Device 1 IF Gain set to: {gain}")
            else:
                print("Invalid IF Gain for Device 1 (must be 0-40 in steps of 8)")
        except ValueError:
            print("Invalid IF Gain input for Device 1")

    def update_device1_bb_gain(self):
        try:
            gain = int(self.device1_bb_gain.text())
            if gain % 2 == 0 and 0 <= gain <= 62:
                self.decoder.source1.set_gain(gain, "VGA")
                print(f"Device 1 Baseband Gain set to: {gain}")
            else:
                print("Invalid Baseband Gain for Device 1 (must be 0-62 in steps of 2)")
        except ValueError:
            print("Invalid Baseband Gain input for Device 1")

    def update_device2_rf_gain(self):
        try:
            gain = int(self.device2_rf_gain.text())
            if gain in [0, 11]:
                self.decoder.source2.set_gain(gain, "AMP")
                print(f"Device 2 RF Gain set to: {gain}")
            else:
                print("Invalid RF Gain for Device 2 (must be 0 or 11)")
        except ValueError:
            print("Invalid RF Gain input for Device 2")

    def update_device2_if_gain(self):
        try:
            gain = int(self.device2_if_gain.text())
            if gain % 8 == 0 and 0 <= gain <= 40:
                self.decoder.source2.set_gain(gain, "LNA")
                print(f"Device 2 IF Gain set to: {gain}")
            else:
                print("Invalid IF Gain for Device 2 (must be 0-40 in steps of 8)")
        except ValueError:
            print("Invalid IF Gain input for Device 2")

    def update_device2_bb_gain(self):
        try:
            gain = int(self.device2_bb_gain.text())
            if gain % 2 == 0 and 0 <= gain <= 62:
                self.decoder.source2.set_gain(gain, "VGA")
                print(f"Device 2 Baseband Gain set to: {gain}")
            else:
                print("Invalid Baseband Gain for Device 2 (must be 0-62 in steps of 2)")
        except ValueError:
            print("Invalid Baseband Gain input for Device 2")

    # Päivitysmetodit taajuudelle
    def update_device1_freq(self):
        try:
            freq = float(self.device1_freq.text())
            if freq > 0:
                self.decoder.source1.set_center_freq(freq)
                print(f"Device 1 Frequency set to: {freq} Hz")
            else:
                print("Invalid frequency for Device 1 (must be positive)")
        except ValueError:
            print("Invalid frequency input for Device 1")

    def update_device2_freq(self):
        try:
            freq = float(self.device2_freq.text())
            if freq > 0:
                self.decoder.source2.set_center_freq(freq)
                print(f"Device 2 Frequency set to: {freq} Hz")
            else:
                print("Invalid frequency for Device 2 (must be positive)")
        except ValueError:
            print("Invalid frequency input for Device 2")