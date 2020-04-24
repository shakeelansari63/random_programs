# Ackermann's Function is a function which can only be wirtten in recursive and not converted to Loops

def ack(m, n):
    if m == 0: return n + 1
    elif n == 0: return ack(m - 1, 1)
    else: return ack(m - 1, ack(m, n - 1))

if __name__ == "__main__":
    # Get cli input
    import sys
    if len(sys.argv) < 3:
        print("Pass 2 cli numbers")
    else:
        m = int(sys.argv[1])
        n = int(sys.argv[2])
        print(ack(m, n))
