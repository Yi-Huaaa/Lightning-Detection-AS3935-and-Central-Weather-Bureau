import RPi.GPIO as GPIO, spidev, time, sys, os

class AS3935:

    def __init__(self):
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.mode = 1
        self.speed = 100000
        self.spi.max_speed_hz = self.speed
        self.pinINT = 15
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pinINT, GPIO.IN)

    def __del__(self):
        self.spi.close()
        print 'spi closed'

    def ReadReg(self, addr, bit=(7, 0), show=True):
        res = self.spi.xfer3([64 + addr, 0], self.speed)[(-1)]
        res &= (1 << bit[0] + 1) - 1
        res >>= bit[1]
        #time.sleep(0.1)
        if show:
            if bit[0] == bit[1]:
                tmp = bit[0]
            else:
                tmp = ('{}:{}').format(bit[0], bit[1])
            print ('Read reg{}[{}]: {}').format(addr, tmp, bin(res))
        return res

    def WriteReg(self, addr, data, bit=(7, 0), show=True):
        res = self.ReadReg(addr, show=False)
        mask = 255
        for i in range(bit[0], bit[1] - 1, -1):
            mask -= 1 << i

        data = res & mask | data << bit[1]
        self.spi.xfer3([addr, data], self.speed)
        if show:
            if bit[0] == bit[1]:
                tmp = bit[0]
            else:
                tmp = ('{}:{}').format(bit[0], bit[1])
            print ('Write reg{}[{}]: {}').format(addr, tmp, bin(data))
        #time.sleep(0.1)

    def Int(self):
        if GPIO.input(self.pinINT):
            return True
        else:
            return False

    def AntennaFreq(self):
        self.WriteReg(8, 1, (7, 7), False)
        start = time.time()
        num = 10000
        i = num
        state = 0
        while i > 0:
            GPIO.wait_for_edge(self.pinINT, GPIO.FALLING)
            i -= 1

        end = time.time()
        self.WriteReg(8, 0, (7, 7), False)
        #print "cost time =", end - start
        return num / (end - start)

    def AntennaTune(self, test=(0, 16)):
        raspi4 = False
        if raspi4:
            self.WriteReg(3, 0, (7,6))
        else:
            self.WriteReg(3, 0b1, (7,6))
        small = (100, 0)
        for i in range(test[0], test[1]):
            self.WriteReg(8, i, (3, 0), False)
            if raspi4:
                freq = self.AntennaFreq() * 16
            else:
                freq = self.AntennaFreq() * 32
            delta = (freq - 500000) / 5000
            print ('capacitor{:2}: {:.6f}Hz {:+.6f}%').format(i, freq, delta)
            if abs(delta) < small[0]:
                small = (abs(delta), i)

        print 'Setting capacitor value to', small[1]
        self.WriteReg(8, small[1], (3, 0))
        GPIO.remove_event_detect(self.pinINT)

    def Reset(self):
        self.WriteReg(60, 150)
    def CALIB_RCO(self):
        self.WriteReg(0x3d, 0x96)
        time.sleep(0.1)
        TRCO = 0
        SRCO = 0
        while TRCO * SRCO == 0:
            if self.ReadReg(0x3a, (7, 7)) == 1:
                TRCO = 1
                print "TRCO ok"
            elif self.ReadReg(0x3a, (6, 6)) == 1:
                TRCO = -1
                print "TRCO error"
            if self.ReadReg(0x3b, (7, 7)) == 1:
                SRCO = 1
                print "SRCO ok"
            elif self.ReadReg(0x3b, (6, 6)) == 1:
                SRCO = -1
                print "SRCO error"
        time.sleep(0.1)
        return TRCO > 0 and SRCO > 0

    def AFE(self):
        t = ReadReg(5) >> 1 & 31

    def IntHandler(self, _):
        time.sleep(0.002)
        t = self.ReadReg(3, bit=(3, 0))
        date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        print date
        if t == 4:
            print 'Disturber detect'
        elif t == 1:
            print 'Noise level too high'
            #self.SetNF(1)
        elif t == 8:
            tmp = date + ', ' + str(self.ReadReg(7)) + '\n'
            self.log.write(tmp)
            self.log.flush()
            print 'Lightning detect'
        elif t == 0:
            print 'Data Purge'
        else:
            print 'Reg[3] =', t, 'error value'
        sys.stdout.flush()

    def CheckHardware(self):
        n0 = 0
        n255 = 255
        for i in range(9):
            t = self.ReadReg(i)
            n0 |= t
            n255 &= t

        return n0 != 0 and n255 != 255
    def PrintSettings(self):
        if self.Indoor:
            output = 'Indoor, '
        else:
            output = 'Outdoor, '
        output += 'MASK_DIST '
        if self.MASK_DIST:
            output += 'enabled, '
        else:
            output += 'disabled, '
        output += 'SREJ: ' + str(self.SREJ)
        output += ', NF_LEV: ' + str(self.NF_LEV)
        print output

    def ReadSettings(self):
        self.MASK_DIST = (self.ReadReg(3, (5, 5)) == 1)
        self.SREJ = self.ReadReg(2, (3, 0))
        self.Indoor = (self.ReadReg(0, (5, 1)) == 0b10010)
        self.NF_LEV = self.ReadReg(1, (6,4))

    def SwitchMASK_DIST(self):
        if self.MASK_DIST:
            self.WriteReg(3, 0, (5, 5))
        else:
            self.WriteReg(3, 1, (5, 5))
        self.MASK_DIST = not self.MASK_DIST
    def SwitchAFE(self):
        self.Indoor = not self.Indoor
        if self.Indoor:
            self.WriteReg(0, 0b10010, (5, 1))
        else:
            self.WriteReg(0, 0b01110, (5, 1))
    def SetSREJ(self, offset):
        t = self.SREJ + offset
        t = max(0, t)
        t = min(t, 15)
        self.WriteReg(2, t, (3, 0))
        self.SREJ = t
    def SetNF(self, offset):
        t = self.NF_LEV + offset
        t = max(0, t)
        t = min(t, 7)
        self.WriteReg(1, t, (6,4))
        self.NF_LEV = t
    def Reboot(self):
        self.WriteReg(0, 1, (0, 0))
        time.sleep(1)
        self.WriteReg(0, 0, (0, 0))
    def Auto(self):
        if not self.CheckHardware():
            print 'Hardware failure detected'
            return
        a = raw_input("Type 'y' to Tune Antenna.\n")
        if a == 'y':
            self.AntennaTune((0, 8))
        self.ReadSettings()
        #pre-setting
        #self.SetSREJ(1 - self.SREJ)
        #self.SetNF(2 - self.NF_LEV)
        if not self.Indoor:
            self.SwitchAFE()
        if not self.MASK_DIST:
            self.SwitchMASK_DIST()
        a = raw_input("Type 'y' to CALIB_RCO.\n")
        if a == 'y':
            if not self.CALIB_RCO():
                return
        self.PrintSettings()
        if os.path.exists('Lightning_log.csv'):
            header = ''
        else:
            header = 'dataTime, D\n'
        self.log = open('Lightning_log.csv', 'a')
        self.log.write(header)
        self.log.flush()

        while self.Int():
            self.IntHandler(self.pinINT)
            time.sleep(0.1)

        GPIO.add_event_detect(self.pinINT, GPIO.RISING, callback=self.IntHandler)
        while True:
            cmd = raw_input()
            if cmd == 'int':
                a = self.Int()
                print a
                if a:
                    self.IntHandler(self.pinINT)
            elif cmd == 'print':
                self.PrintSettings()
            elif cmd == 'mask':
                self.SwitchMASK_DIST()
            elif cmd == 'afe':
                self.SwitchAFE()
            elif cmd == 'nf+':
                self.SetNF(1)
            elif cmd == 'nf-':
                self.SetNF(-1)
            elif cmd == 'srej+':
                self.SetSREJ(1)
            elif cmd == 'srej-':
                self.SetSREJ(-1)
            elif cmd == 'exit':
                break
            elif cmd == 'r':
                a = int(raw_input())
                self.ReadReg(a)
            else:
                print 'Cmd not found'

        GPIO.remove_event_detect(self.pinINT)
        GPIO.cleanup()


a = AS3935()
if __name__ == '__main__':
    a.Auto()
