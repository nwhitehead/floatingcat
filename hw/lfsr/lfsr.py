from myhdl import *
import sys
from combinations import combinations

# LFSR size limits
MIN_LFSR_WIDTH = 3
MAX_LFSR_WIDTH = 16

# Testing limits
MAX_TESTED_LFSR_WIDTH = 10
# MAX_TESTED_LFSR_WIDTH can be increased to verify larger sizes,
# but testing time increases exponentially.
TESTED_WIDTHS_PERIOD = range(MIN_LFSR_WIDTH, 
                             min(MAX_LFSR_WIDTH, 
                                 MAX_TESTED_LFSR_WIDTH) + 1)
TESTED_WIDTHS_NONLOCKING = range(MIN_LFSR_WIDTH, MAX_LFSR_WIDTH + 1)


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

    for reversible, non_locking, reverse, width in 
            combinations([True, False], [True, False], 
                         [True, False], TESTED_WIDTHS_PERIOD)
        clk = Signal(bool(0))
        d = Signal(intbv(0)[width:])
        dir = Signal(bool(0))
        if reversible:
            lfsr = reversible_LFSR(clk, d, dir, width=width, 
                non_locking=non_locking)
        else:
            lfsr = LFSR(clk, d, width=width, 
                non_locking=non_locking, reverse=reverse)
        chk = test(clk, d, width)
        print 'period ', width, non_locking, reverse
        sim = Simulation(lfsr, chk)
        sim.run(quiet=1)

def test_nonlocking():
    '''Test for lockups'''
    def test(clk, d, width):
        # Check for 11...1 -> 11...1
        d.next = intbv(-1)[width:]
        yield delay(10)
        clk.next = 1
        yield delay(10)
        clk.next = 0
        yield delay(10)
        assert d.val != intbv(-1)[width:]
        # Check for 00...0 -> 00...0
        d.next = intbv(0)[width:]
        yield delay(10)
        clk.next = 1
        yield delay(10)
        clk.next = 0
        yield delay(10)
        assert d.val != intbv(0)[width:]
        raise StopSimulation

    for width in TESTED_WIDTHS_NONLOCKING:
        for reverse in [True, False]:
            clk = Signal(bool(0))
            d = Signal(intbv(0)[width:])
            lfsr = LFSR(clk, d, width=width, 
                non_locking=True, reverse=reverse)
            chk = test(clk, d, width)
            print 'nonlocking ', width, reverse
            sim = Simulation(lfsr, chk)
            sim.run(quiet=1)

def test_reverse():
    '''Test for correct reversing'''
    def test(clk, d0, d1, width):
        seq0 = []
        seq1 = []
        for i in range(2 ** width):
            seq0.append(int(d0.val))
            seq1.append(int(d1.val))
            clk.next = 1
            yield delay(10)
            clk.next = 0
            yield delay(10)
        seq1.reverse()
        assert seq0 == seq1
        raise StopSimulation

    for non_locking in [True, False]:
        for width in TESTED_WIDTHS_PERIOD:
            clk = Signal(bool(0))
            d0 = Signal(intbv(0)[width:])
            d1 = Signal(intbv(0)[width:])
            lfsr0 = LFSR(clk, d0, width=width, 
                non_locking=non_locking, reverse=False)
            lfsr1 = LFSR(clk, d1, width=width, 
                non_locking=non_locking, reverse=True)
            chk = test(clk, d0, d1, width)
            print 'reverse ', width, non_locking
            sim = Simulation(lfsr0, lfsr1, chk)
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

def LFSR(clk, D, width=4, non_locking=False, reverse=False):
    R = Signal(bool(0))
    lfsrbit_inst = LFSR_bit(D, R, width=width, 
        non_locking=non_locking, reverse=reverse)

    if not reverse:
        @always(clk.posedge)
        def logic():
            for i in range(width - 1):
                D.next[i + 1] = D[i]
            D.next[0] = R
    else:
        @always(clk.posedge)
        def logic():
            for i in range(width - 1):
                D.next[i] = D[i + 1]
            D.next[width - 1] = R

    return logic, lfsrbit_inst

def reversible_LFSR(clk, D, dir, width=4, non_locking=False):
    Rforward, Rreverse = [Signal(bool(0)), Signal(bool(0))]
    lfsrbit_inst0 = LFSR_bit(D, Rforward, width=width, 
        non_locking=non_locking, reverse=False)
    lfsrbit_inst1 = LFSR_bit(D, Rreverse, width=width, 
        non_locking=non_locking, reverse=True)

    @always(clk.posedge)
    def logic():
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
    lfsr_inst = LFSR(iKEY, oLEDR, width=5, non_locking=True)
    return lfsr_inst

def convert_main():
    clk = Signal(bool(0))
    key = Signal(intbv(0)[3:])
    led = Signal(intbv(0)[16:])
    mn = toVerilog(main, clk, key, led)

if __name__ == '__main__':
    convert_main()
