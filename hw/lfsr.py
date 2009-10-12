'''
Linear Feedback Shift Register

Includes simple lfsr module that cycles through bit patterns.
Can be configured to many widths, option to avoid locking patterns
that may occur due to glitches.  Can be configured to go in reverse.

Also includes reversible lfsr counter that has a direction
input so it can count forwards or backwards on every clock cycle.

'''

from myhdl import *
import sys
import os
from combinations import combinations

# Should we cosimulate in Verilog?
# False means use myhdl
# True means convert to verilog
cosimulate = True

# LFSR size limits
MIN_LFSR_WIDTH = 3
MAX_LFSR_WIDTH = 64

# Testing limits
MAX_TESTED_LFSR_WIDTH = 10
# MAX_TESTED_LFSR_WIDTH can be increased to verify larger sizes,
# but testing time increases exponentially.
TESTED_WIDTHS_PERIOD = range(MIN_LFSR_WIDTH, 
                             MAX_TESTED_LFSR_WIDTH + 1)
TESTED_WIDTHS = range(MIN_LFSR_WIDTH, MAX_LFSR_WIDTH + 1)
TESTED_WIDTHS_REVERSIBLE = range(MIN_LFSR_WIDTH, 
                                 MAX_TESTED_LFSR_WIDTH + 1)
TESTED_LEN_REVERSIBLE = range(3, 20)

# This file uses py.test for unit testing

def clockGen(clk):
    while 1:
        yield delay(10)
        clk.next = not clk


def test_period():
    '''Test for correct period'''
    def test(clk, enable, d, set, dset, width):
        set.next = True
        dset.next = intbv(0)[width:]
        enable.next = False
        yield posedge(clk)
        set.next = False
        enable.next = True
        yield posedge(clk)
        used = {}
        while True:
            if int(d.val) in used:
                actual = used.keys()
                actual.sort()
                expected = range(2 ** width - 1)
                assert actual == expected
                raise StopSimulation
            used[int(d.val)] = 1
            yield posedge(clk)

    for non_locking, reverse, width in combinations(
        [True, False], [True, False], TESTED_WIDTHS_PERIOD):
        clk = Signal(False)
        enable = Signal(False)
        d = Signal(intbv(0)[width:])
        set = Signal(False)
        dset = Signal(intbv(0)[width:])
        lfsr = LFSR(clk, enable, d, set, dset, width=width, 
                    non_locking=non_locking, reverse=reverse)
        chk = test(clk, enable, d, set, dset, width)
        clkgen_inst = clockGen(clk)
        print 'period', non_locking, reverse, width
        sim = Simulation(clkgen_inst, lfsr, chk)
        sim.run(quiet=1)

    for non_locking, direction, width in combinations(
        [True, False], [0, 1], TESTED_WIDTHS_PERIOD):
        clk = Signal(bool(0))
        enable = Signal(False)
        d = Signal(intbv(0)[width:])
        set = Signal(bool(0))
        dset = Signal(intbv(0)[width:])
        dir = Signal(bool(direction))
        lfsr = reversible_LFSR(clk, enable, d, dir, set, dset, width=width, 
                               non_locking=non_locking)
        chk = test(clk, enable, d, set, dset, width)
        print 'period2', non_locking, direction, width
        sim = Simulation(lfsr, chk)
        sim.run(quiet=1)

def test_nonlocking():
    '''Test for lockups'''
    def test(clk, enable, d, set, dset, width):
        # Check for 11...1 -> 11...1
        set.next = True
        dset.next = intbv(-1)[width:]
        enable.next = True
        clk.next = 1
        yield delay(10)
        clk.next = 0
        set.next = False
        yield delay(10)
        clk.next = 1
        yield delay(10)
        clk.next = 0
        yield delay(10)
        assert d.val != intbv(-1)[width:]
        # Check for 00...0 -> 00...0
        set.next = True
        dset.next = intbv(0)[width:]
        enable.next = True
        clk.next = 1
        yield delay(10)
        clk.next = 0
        set.next = False
        yield delay(10)
        clk.next = 1
        yield delay(10)
        clk.next = 0
        yield delay(10)
        assert d.val != intbv(0)[width:]
        raise StopSimulation

    for reverse, width in combinations([True, False], TESTED_WIDTHS):
        clk = Signal(bool(0))
        enable = Signal(True)
        d = Signal(intbv(0)[width:])
        set = Signal(False)
        dset = Signal(intbv(0)[width:])
        lfsr = LFSR(clk, enable, d, set, dset, width=width, 
                    non_locking=True, reverse=reverse)
        chk = test(clk, enable, d, set, dset, width)
        print 'nonlocking ', width, reverse
        sim = Simulation(lfsr, chk)
        sim.run(quiet=1)

    for direction, width in combinations([0, 1], TESTED_WIDTHS):
        clk = Signal(bool(0))
        enable = Signal(True)
        d = Signal(intbv(0)[width:])
        dir = Signal(bool(direction))
        set = Signal(False)
        dset = Signal(intbv(0)[width:])
        lfsr = reversible_LFSR(clk, enable, d, dir, set, dset, 
                               width=width, non_locking=True)
        chk = test(clk, enable, d, set, dset, width)
        print 'nonlocking2 ', width, direction
        sim = Simulation(lfsr, chk)
        sim.run(quiet=1)

def test_reverse():
    '''Test for correct reversing'''
    def test(clk, enable0, enable1, d0, d1, set0, set1, 
             dset0, dset1, width):
        enable0.next = True
        enable1.next = True
        set0.next = True
        set1.next = True
        dset0.next = intbv(0)[width:]
        dset1.next = intbv(0)[width:]
        clk.next = True
        yield delay(10)
        set0.next = False
        set1.next = False
        clk.next = False
        yield delay(10)
        seq0 = []
        seq1 = []
        for i in range(2 ** width):
            seq0.append(int(d0.val))
            seq1.append(int(d1.val))
            clk.next = True
            yield delay(10)
            clk.next = False
            yield delay(10)
        seq1.reverse()
        assert seq0 == seq1
        raise StopSimulation

    for non_locking, width in combinations(
        [True, False], TESTED_WIDTHS_PERIOD):
        clk = Signal(bool(0))
        enable0 = Signal(bool(0))
        enable1 = Signal(bool(0))
        d0 = Signal(intbv(0)[width:])
        d1 = Signal(intbv(0)[width:])
        set0 = Signal(bool(0))
        set1 = Signal(bool(0))
        dset0 = Signal(intbv(0)[width:])
        dset1 = Signal(intbv(0)[width:])
        lfsr0 = LFSR(clk, enable0, d0, set0, dset0, width=width, 
                     non_locking=non_locking, reverse=False)
        lfsr1 = LFSR(clk, enable1, d1, set1, dset1, width=width, 
                     non_locking=non_locking, reverse=True)
        chk = test(clk, enable0, enable1, d0, d1, 
                   set0, set1, dset0, dset1, width)
        print 'reverse ', non_locking, width
        sim = Simulation(lfsr0, lfsr1, chk)
        sim.run(quiet=1)

def test_reversible():
    '''Test for correct reversing behavior in reversible lfsrs'''
    def test(clk, enable, d, dir, set, dset, width, l):
        set.next = True
        dset.next = intbv(0)[width:]
        enable.next = True
        clk.next = 1
        yield delay(10)
        clk.next = 0
        set.next = False
        yield delay(10)
        clk.next = 1
        yield delay(10)
        for i in range(l):
            v0 = d.val
            clk.next = 0
            yield delay(10)
            clk.next = 1
            yield delay(10)
        clk.next = 0
        dir.next = not dir
        yield delay(10)
        clk.next = 1
        yield delay(10)
        assert v0 == d.val
        raise StopSimulation

    for non_locking, direction, width, l in combinations(
        [True, False], [0, 1], 
        TESTED_WIDTHS_REVERSIBLE, TESTED_LEN_REVERSIBLE):
        clk = Signal(bool(0))
        enable = Signal(bool(0))
        d = Signal(intbv(0)[width:])
        dir = Signal(bool(direction))
        set = Signal(bool(0))
        dset = Signal(intbv(0)[width:])
        lfsr = reversible_LFSR(clk, enable, d, dir, set, dset, 
                               width=width, non_locking=non_locking)
        chk = test(clk, enable, d, dir, set, dset, width, l)
        print 'reversible ', non_locking, direction, width, l
        sim = Simulation(lfsr, chk)
        sim.run(quiet=1)

'''Maximal length LFSR tap table

Example:
4 : [4, 3]
This means bit vector of length 4
New bit is lowest bit, will be a combination
of taps from existing bits.
Table is stored with bits numbered 1..n
So 4 : [4,3] means tap x[4] and x[3] to get new x[1].

Values from:
Peter Alfke, "Efficient Shift Registers, LFSR Counters, and Long Pseudo-
Random Sequence Generators", Xilinx Application Note 052, July 7, 1996.

'''
lfsr_tap_table = {
3 : [3, 2],
4 : [4, 3],
5 : [5, 3],
6 : [6, 5],
7 : [7, 6],
8 : [8, 6, 5, 4],
9 : [9, 5],
10 : [10, 7],
11 : [11, 9],
12 : [12, 6, 4, 1],
13 : [13, 4, 3, 1],
14 : [14, 5, 3, 1],
15 : [15, 14],
16 : [16, 15, 13, 4],
17 : [17, 14],
18 : [18, 11],
19 : [19, 6, 2, 1],
20 : [20, 17],
21 : [21, 19],
22 : [22, 21],
23 : [23, 18],
24 : [24, 23, 22, 17],
25 : [25, 22],
26 : [26, 6, 2, 1],
27 : [27, 5, 2, 1],
28 : [28, 25],
29 : [29, 27],
30 : [30, 6, 4, 1],
31 : [31, 28],
32 : [32, 22, 2, 1],
33 : [33, 20],
34 : [34, 27, 2, 1],
35 : [35, 33],
36 : [36, 25],
37 : [37, 5, 4, 3, 2, 1], # anomalous case, 6 taps required
38 : [38, 6, 5, 1],
39 : [39, 35],
40 : [40, 38, 21, 19],
41 : [41, 38],
42 : [42, 41, 20, 19],
43 : [43, 42, 38, 37],
44 : [44, 43, 18, 17],
45 : [45, 44, 42, 41],
46 : [46, 45, 26, 25],
47 : [47, 42],
48 : [48, 47, 21, 20],
49 : [49, 40],
50 : [50, 49, 24, 23],
51 : [51, 50, 36, 35],
52 : [52, 49],
53 : [53, 52, 38, 37],
54 : [54, 53, 18, 17],
55 : [55, 31],
56 : [56, 55, 35, 34],
57 : [57, 50],
58 : [58, 39],
59 : [59, 58, 38, 37],
60 : [60, 59],
61 : [61, 60, 46, 45],
62 : [62, 61, 6, 5],
63 : [63, 62],
64 : [64, 63, 61, 60],
}

def LFSR_bit(D, R, width=4, non_locking=True, reverse=False):
    assert (width >= MIN_LFSR_WIDTH and width <= MAX_LFSR_WIDTH)
    assert (len(D) >= width)

    taps = lfsr_tap_table[width]
    taps = [x - 1 for x in taps] # correct for table conventions
    if reverse:
        # To reverse sequence, do some math.
        # Normal seq:
        # x_(n-1) ... x_2 x_1 x_0 => y_n-1 ... y_2 y_1 y_0
        # Shift: y_1 = x_0  y_2 = x_1  ...  y_(n-1) = x_(n-2)
        # y_0 = x_t0 + x_t1 + 1
        # Now we want to go backwards (y=>x), solve for x_n-1
        # t0 is always n-1, so y_0 = x_(n-1) + x_t1 + 1
        # Solve for x_(n-1) to get:
        # x_(n-1) = y_0 + x_t1 + 1
        # We know x_t1 = y_(t1 + 1)
        # So x_(n-1) = y_0 + y_(t1 + 1) + 1
        taps = [0] + [t + 1 for t in taps[1:]]
    if len(taps) == 2:
        tp0 = taps[0]
        tp1 = taps[1]
        if non_locking:
            @always_comb
            def logic():
                if D[width:] == intbv(-1)[width:]:
                    R.next = 0
                else:
                    R.next = D[tp1] ^ D[tp0] ^ 1
        else:
            @always_comb
            def logic():
                R.next = D[tp1] ^ D[tp0] ^ 1
    elif len(taps) == 4:
        tp0 = taps[0]
        tp1 = taps[1]
        tp2 = taps[2]
        tp3 = taps[3]
        if non_locking:
            @always_comb
            def logic():
                if D[width:] == intbv(-1)[width:]:
                    R.next = 0
                else:
                    R.next = D[tp3] ^ D[tp2] ^ D[tp1] ^ D[tp0] ^ 1
        else:
            @always_comb
            def logic():
                R.next = D[tp3] ^ D[tp2] ^ D[tp1] ^ D[tp0] ^ 1
    elif len(taps) == 6:
        tp0 = taps[0]
        tp1 = taps[1]
        tp2 = taps[2]
        tp3 = taps[3]
        tp4 = taps[4]
        tp5 = taps[5]
        if non_locking:
            @always_comb
            def logic():
                if D[width:] == intbv(-1)[width:]:
                    R.next = 0
                else:
                    R.next = D[tp5] ^ D[tp4] ^ D[tp3] ^ D[tp2] ^ D[tp1] ^ D[tp0] ^ 1
        else:
            @always_comb
            def logic():
                R.next = D[tp5] ^ D[tp4] ^ D[tp3] ^ D[tp2] ^ D[tp1] ^ D[tp0] ^ 1

    return logic

def LFSR_my(clk, enable, D, set, Dset, width=4, non_locking=False, reverse=False):
    R = Signal(bool(0))
    lfsrbit_inst = LFSR_bit(D, R, width=width, 
        non_locking=non_locking, reverse=reverse)

    if not reverse:
        @always(clk.posedge)
        def logic():
            if set:
                D.next = Dset
            else:
                if enable:
                    for i in range(width - 1):
                        D.next[i + 1] = D[i]
                    D.next[0] = R
    else:
        @always(clk.posedge)
        def logic():
            if set:
                D.next = Dset
            else:
                if enable:
                    for i in range(width - 1):
                        D.next[i] = D[i + 1]
                    D.next[width - 1] = R

    return logic, lfsrbit_inst

def LFSR(*args, **kwargs):
    print args, kwargs
    if cosimulate:
        return LFSR_v(*args, **kwargs)
    else:
        return LFSR_my(*args, **kwargs)

def LFSR_v(clk, enable, D, set, Dset, width=4, non_locking=False, reverse=False):
    toVerilog(LFSR_my, clk, enable, D, set, Dset, width, non_locking, reverse)
    cmd = "iverilog -o lfsr_v.o LFSR_my.v tb_LFSR_my.v"
    os.system(cmd)
    cmd = "vvp -m myhdl lfsr_v.o"
    return Cosimulation(cmd, **locals())

def reversible_LFSR(clk, enable, D, dir, set, Dset, width=4, non_locking=False):
    Rforward, Rreverse = [Signal(bool(0)), Signal(bool(0))]
    lfsrbit_inst0 = LFSR_bit(D, Rforward, width=width, 
        non_locking=non_locking, reverse=False)
    lfsrbit_inst1 = LFSR_bit(D, Rreverse, width=width, 
        non_locking=non_locking, reverse=True)

    @always(clk.posedge)
    def logic():
        if set:
            D.next = Dset
        else:
            if enable:
                if not dir:
                    for i in range(width - 1):
                        D.next[i + 1] = D[i]
                    D.next[0] = Rforward
                else:
                    for i in range(width - 1):
                        D.next[i] = D[i + 1]
                    D.next[width - 1] = Rreverse

    return logic, lfsrbit_inst0, lfsrbit_inst1


def main(iCLK_50, iKEY, oLEDR):
    set = Signal(False)
    enable = Signal(True)
    Dset = Signal(intbv(0)[4:0])
    lfsr_inst = LFSR(iKEY, enable, oLEDR, set, Dset, width=5, non_locking=True)
    return lfsr_inst

def convert_main():
    clk = Signal(bool(0))
    key = Signal(intbv(0)[3:])
    led = Signal(intbv(0)[16:])
    mn = toVerilog(main, clk, key, led)

if __name__ == '__main__':
    test_period()
    test_nonlocking()
    test_reverse()
    test_reversible()
    convert_main()
