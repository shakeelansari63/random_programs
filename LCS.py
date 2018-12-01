# --*-- coding: utf-8 --*-- 

def lcs(s1, s2):
    """
    LCS Program for 2 strings
    """
    cache = [[None] * len(s2)] * len(s1)
    return calculateLCS(s1, s2, 0, 0, cache)

def calculateLCS(s1, s2, i1, i2, cache):
    """
    logic to calculate LCS
    """
    if len(s1) > i1 and len(s2) > i2:
        if cache[i1][i2]:
            return cache[i1][i2]
        elif s1[i1] == s2[i2]:
            cache[i1][i2] = s1[i1] + calculateLCS(s1, s2, i1 + 1, i2 + 1, cache)
            return cache[i1][i2]
        else:
            cache[i1][i2] = max_len(calculateLCS(s1, s2, i1 + 1, i2, cache), calculateLCS(s1, s2, i1, i2 + 1, cache))
            return cache[i1][i2]
    else:
        return ''

def max_len(s1, s2):
    """
    Find string with max length
    """
    if len(s1) >= len(s2):
        return s1
    else:
        return s2

s1 = input("Enter String 1: ")
s2 = input("Enter String 2: ")

print(lcs(s1,s2))