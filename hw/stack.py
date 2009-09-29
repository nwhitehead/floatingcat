from myhdl import *
import sys
import random

# Stack size limits
MIN_WIDTH = 1
MIN_DEPTH = 2

# Testing limits
MIN_TESTED_WIDTH = 1
MAX_TESTED_WIDTH = 64
MIN_TESTED_DEPTH = 2
MAX_TESTED_DEPTH = 30
MAX_TESTED_OPS = 100

t_op = enum(
'NOP',   # ( S T | S T )
'POP',   # ( S T | X )
'STORE', # ( S T | S X )
'PUSH',  # ( S T | S T X )
)

def randintbv(width):
    return intbv(random.randint(0, 2 ** width - 1))[width-1:]

class model:
    def __init__(self, depth=8, width=8):
        self.stk = []
        self.depth = depth
        self.width = width
    def do_op(self, op, data):
        assert len(data) == self.width
        if op == t_op.NOP: pass
        elif op == t_op.POP:
            self.stk = self.stk[:len(self.stk) - 1]
            self.stk[0] = data
        elif op == t_op.PUSH:
            self.stk.append(data)
        elif op == t_op.STORE:
            self.stk[0] = data
        assert len(self.stk) <= depth
    def douts(self):
        return self.stk[0], self.stk[1]
    def do_ops(self, ops):
        for x in ops:
            op, data = x
            self.do_op(op, data)
    def generate_random_legal_ops(self, num=10):
        

def test_seq():
    '''Test legal sequences of operations against model'''
    for w in range(MIN_TESTED_WIDTH, MAX_TESTED_WIDTH + 1):

def test_period():
    '''Test for correct period'''
    def test(clk, d, width):
        used = {}
        while True:
            if int(d.val) in used:
                actual = used.keys()
                actual.sort()
                expected = range(2 ** width - 1)
                assert actual == expected
                raise StopSimulation
            used[int(d.val)] = 1
            clk.next = 1
            yield delay(10)
            clk.next = 0
            yield delay(10)

    for non_locking in [True, False]:
        for width in TESTED_WIDTHS_PERIOD:
            clk = Signal(bool(0))
            d = Signal(intbv(0)[width:])
            lfsr = LFSR(clk, d, width=width, non_locking=non_locking)
            chk = test(clk, d, width)
            sim = Simulation(lfsr, chk)
            sim.run(quiet=1)

def stack(clk, op, din, dout0, dout1, pos, depth=8, width=8, wrap=False):
    stk = [Signal(intbv(0)[width-1:0]) for x in range(depth)]
    @always(clk.posedge)
    def logic():
        if op == t_op.NOP:
            dout0.next = dout0
            dout1.next = dout1
            pos.next = pos
        elif op == t_op.PUSH:
            for i in range(depth - 2):
                stk[i].next = stk[i + 1]
            stk[depth - 1].next = din
            dout0.next = din
            dout1.next = stk[depth - 1]
            pos.next = pos + 1
        elif op == t_op.POP:
            for i in range(1, depth - 1):
                stk[i + 1].next = stk[i]
            if wrap:
                stk[0].next = stk[depth - 1]
            else:
                stk[0].next = 0
            dout0.next = stk[depth - 2]
            dout1.next = stk[depth - 1]
        elif op == t_op.RESET:
            pass
            
    return logic

def main(iCLK_50, iKEY, oLEDR):
    lfsr_inst = LFSR(iKEY, oLEDR, width=5, non_locking=True)
    return lfsr_inst

def convert_main():
    clk = Signal(bool(0))
    key = Signal(intbv(0)[3:])
    led = Signal(intbv(0)[16:])
    mn = toVerilog(main, clk, key, led)
    stk = toVerilog(stack, clk, key, key, led, led, led, led)

if __name__ == '__main__':
    convert_main()
